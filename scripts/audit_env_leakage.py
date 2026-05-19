"""One-shot audit before re-running v2:

1. Scrub for "localhost" / "test environment" / "sandbox" / "dev mode"
   strings in env templates and Python files that the agent might see
   through observation or screenshot.
2. Enumerate file-input dragdrop patterns (<input type=file> hidden behind
   visible drop-zones / role=button divs) so we know which envs were
   silently broken pre-fix-5.
3. Cross-check every env's authored domains against environments.yaml +
   the new _PORT_TO_DOMAIN map in browser.py.

Read-only. Prints a report. Re-runnable.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# Windows console defaults to cp1252; templates contain emoji + arrows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
ALL_WEBSITES = REPO / "all_websites"
AGENT_CONFIG = REPO / "agent" / "config"

# Strings whose presence in agent-visible page content would leak the
# benchmark's "this is a test" framing. NOT case-sensitive.
LEAKAGE_NEEDLES = [
    "localhost",
    "127.0.0.1",
    "test environment",
    "dev environment",
    "development environment",
    "sandbox",
    "dev instance",
    "dev mode",
    "this is a test",
    "for testing",
    "benchmark",
]

# Files we audit for leakage. Templates render server-side, Python files
# can embed prose returned in API responses, JS files can inject content.
AUDIT_EXTS = {".html", ".htm", ".py", ".js", ".jinja", ".jinja2", ".tmpl"}

# False-positive filter: code that references localhost for legitimate
# server bootstrap (host="0.0.0.0", port=N etc.) is fine — the agent never
# sees this. We flag only matches inside string literals that look like
# user-facing prose.
PROSE_HINT_RE = re.compile(
    r"""(['"])([^'"]{0,200}?(?:""" + "|".join(re.escape(n) for n in LEAKAGE_NEEDLES) + r"""))[^'"]{0,200}?\1""",
    re.IGNORECASE,
)


_NOISE_PATTERNS = [
    # CSS selectors and class names mentioning benchmark/localhost
    re.compile(r"^\s*(?:html|body|\.|#|@|\[)\s*(?:\[data-)?benchmark", re.IGNORECASE),
    re.compile(r"benchmark-(?:quality|browser-chrome|secret|wrapper|root|env-tag)", re.IGNORECASE),
    re.compile(r"^[^<]*<style"),
    # Server-side prints / startup banners — agent never sees these
    re.compile(r"^\s*print\s*\(\s*f?[\"'].*localhost", re.IGNORECASE),
    re.compile(r"^\s*print\s*\(.*Benchmark", re.IGNORECASE),
    # Flask secret_key / app config lines
    re.compile(r"app\.secret_key\s*=", re.IGNORECASE),
    re.compile(r"^\s*secret_key\s*=", re.IGNORECASE),
    # Constants / config dicts setting localhost URLs
    re.compile(r"^\s*_(?:MAIN|GEN|LOG|URL|HOST)\s*=\s*f?[\"']http://localhost"),
    re.compile(r"SITE_PORTS\s*[\[\.]", re.IGNORECASE),
    # CSS rule bodies containing 'sandbox' / 'dev' as part of selectors
    re.compile(r"^\s*[a-z-]+\s*:\s*[^;]*sandbox", re.IGNORECASE),
    # Server runner banner prints
    re.compile(r"Server Runner", re.IGNORECASE),
    re.compile(r"Running on\s+http://localhost", re.IGNORECASE),
    # File-doctring / module-docstring first lines
    re.compile(r"^[\"']{1,3}.*Benchmark.*[\"']{0,3}\s*$", re.IGNORECASE),
    # Module docstrings on line 2: '<env> Benchmark - Flask Backend'
    re.compile(r"^\s*[\w\s-]+Benchmark\s*-\s*(Flask Backend|Server Runner)", re.IGNORECASE),
]


def _is_noise(line: str) -> bool:
    return any(p.search(line) for p in _NOISE_PATTERNS)


def audit_leakage() -> dict:
    findings: dict[str, list[tuple[int, str]]] = {}
    for f in ALL_WEBSITES.rglob("*"):
        if f.suffix.lower() not in AUDIT_EXTS:
            continue
        # Skip vendor/static minified bundles
        if any(part in {"node_modules", "vendor", "dist"} for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if not any(n in low for n in LEAKAGE_NEEDLES):
                continue
            # Filter out obvious server-config lines
            if re.search(r"(host\s*=|port\s*=|0\.0\.0\.0|127\.0\.0\.1\s*[,)])", line):
                continue
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if _is_noise(line):
                continue
            hits.append((i, line.strip()[:160]))
        if hits:
            findings[str(f.relative_to(REPO))] = hits
    return findings


def audit_dragdrop() -> dict:
    """Find <input type=file> elements paired with hidden/styled wrappers."""
    findings: dict[str, list[str]] = {}
    file_input_re = re.compile(
        r"""<input[^>]*type\s*=\s*['"]file['"][^>]*>""",
        re.IGNORECASE,
    )
    hidden_input_re = re.compile(
        r"""<input[^>]*type\s*=\s*['"]file['"][^>]*(?:style\s*=\s*['"][^'"]*display\s*:\s*none|hidden\b)""",
        re.IGNORECASE,
    )
    for f in ALL_WEBSITES.rglob("*.html"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        inputs = file_input_re.findall(text)
        if not inputs:
            continue
        hidden = hidden_input_re.findall(text)
        # Look for an adjacent drop-zone div (heuristic: <div with class containing
        # "drop"/"upload" or with onclick triggering a file input)
        dropzone_hits = re.findall(
            r"<div[^>]*(?:class\s*=\s*['\"][^'\"]*(?:drop|upload)[^'\"]*['\"]|onclick\s*=\s*['\"][^'\"]*getElementById[^'\"]*\.click)",
            text,
            re.IGNORECASE,
        )
        if hidden or dropzone_hits:
            note = f"file_inputs={len(inputs)} hidden={len(hidden)} dropzones={len(dropzone_hits)}"
            findings[str(f.relative_to(REPO))] = [note]
    return findings


def audit_yaml_domains() -> dict:
    """Verify every env's `domain:` field maps cleanly into _PORT_TO_DOMAIN."""
    import yaml
    cfg = yaml.safe_load((AGENT_CONFIG / "environments.yaml").read_text())
    seen_ports: dict[int, str] = {}
    collisions: list[str] = []
    missing_domain: list[str] = []
    for env_name, env in (cfg.get("environments") or {}).items():
        for site_key, site in (env.get("sites") or {}).items():
            domain = site.get("domain", "")
            port = site.get("port")
            if not domain:
                missing_domain.append(f"{env_name}.{site_key} (port={port})")
            if port is not None and port in seen_ports and seen_ports[port] != domain:
                collisions.append(
                    f"port {port}: {seen_ports[port]!r} (earlier) vs {domain!r} ({env_name}.{site_key})"
                )
            if port is not None:
                seen_ports.setdefault(port, domain)
    return {"missing_domain": missing_domain, "port_collisions": collisions, "n_ports": len(seen_ports)}


def main() -> int:
    print("=" * 72)
    print(" 1. Agent-visible leakage scan (localhost / test / sandbox / dev)")
    print("=" * 72)
    leak = audit_leakage()
    if not leak:
        print("  No suspicious agent-visible strings found in templates/code.")
    else:
        print(f"  Found in {len(leak)} files. Review each manually:")
        for path, hits in sorted(leak.items()):
            print(f"\n  {path}  ({len(hits)} hits)")
            for ln, line in hits[:5]:
                print(f"    L{ln}: {line}")
            if len(hits) > 5:
                print(f"    ... +{len(hits) - 5} more")

    print()
    print("=" * 72)
    print(" 2. File-input dragdrop pattern enumeration")
    print("=" * 72)
    dd = audit_dragdrop()
    if not dd:
        print("  No file-input + dragdrop wrappers found.")
    else:
        print(f"  {len(dd)} templates use the dragdrop pattern:")
        for path, notes in sorted(dd.items()):
            print(f"  {path}: {notes[0]}")

    print()
    print("=" * 72)
    print(" 3. environments.yaml domain coverage")
    print("=" * 72)
    yd = audit_yaml_domains()
    print(f"  Distinct ports with a domain: {yd['n_ports']}")
    if yd["missing_domain"]:
        print(f"  WARNING: {len(yd['missing_domain'])} sites have no `domain:` field:")
        for s in yd["missing_domain"]:
            print(f"    {s}")
    if yd["port_collisions"]:
        print(f"  WARNING: {len(yd['port_collisions'])} port collisions:")
        for c in yd["port_collisions"]:
            print(f"    {c}")
    if not yd["missing_domain"] and not yd["port_collisions"]:
        print("  All sites have a domain. No port collisions.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
