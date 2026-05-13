"""
Phase 3 sibling QA — page-load smoke harness.

Loads every env's start_site URL and records HTTP status + elapsed.
This is the "1 step each, no model — just verify pages load" pass
from phase4-checklist E3 Week-1.

Pre-req: `bash start_servers.sh start` (or `start_servers.sh start <env>`
for a subset) must have run first. This script does NOT manage the
server lifecycle — it only probes.

Output: agent/logs/phase3_page_load_smoke.json
"""
from __future__ import annotations

import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml


YAML_PATH = Path("agent/config/environments.yaml")
OUTPUT_PATH = Path("agent/logs/phase3_page_load_smoke.json")
PROBE_TIMEOUT_SEC = 5
MAX_RESPONSE_BYTES = 2048


def probe(url: str) -> dict:
    """Single GET probe. Returns status / elapsed / first-2KB body / error."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "phase3-smoke/1.0"})
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_SEC) as resp:
            body = resp.read(MAX_RESPONSE_BYTES)
            elapsed = time.time() - t0
            return {
                "status": resp.status,
                "elapsed_ms": round(elapsed * 1000, 1),
                "content_length": len(body),
                "content_type": resp.headers.get("Content-Type", ""),
                "first_bytes": body[:200].decode("utf-8", errors="replace"),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return {
            "status": e.code,
            "elapsed_ms": round(elapsed * 1000, 1),
            "content_length": 0,
            "content_type": "",
            "first_bytes": "",
            "error": f"HTTPError {e.code} {e.reason}",
        }
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
        elapsed = time.time() - t0
        return {
            "status": 0,
            "elapsed_ms": round(elapsed * 1000, 1),
            "content_length": 0,
            "content_type": "",
            "first_bytes": "",
            "error": f"{type(e).__name__}: {e}",
        }


def main() -> None:
    with open(YAML_PATH) as f:
        cfg = yaml.safe_load(f)
    envs = cfg["environments"]

    results: list[dict] = []
    for env_key, env in envs.items():
        sites = env.get("sites", {})
        start_site = env.get("start_site")
        if not sites or not start_site or start_site not in sites:
            results.append({
                "env": env_key,
                "site": None,
                "url": None,
                "result": {"error": "no start_site or sites in yaml"},
                "verdict": "skipped",
            })
            continue
        site = sites[start_site]
        port = site.get("port")
        if not port:
            results.append({
                "env": env_key,
                "site": start_site,
                "url": None,
                "result": {"error": "no port"},
                "verdict": "skipped",
            })
            continue
        url = f"http://localhost:{port}/"
        r = probe(url)
        verdict = "ok" if r["status"] == 200 else (
            "redirect" if 300 <= r["status"] < 400 else
            "down" if r["status"] == 0 else
            "http_error"
        )
        results.append({
            "env": env_key,
            "site": start_site,
            "url": url,
            "port": port,
            "result": r,
            "verdict": verdict,
        })
        print(f"{verdict:<10} {env_key:<40} {url} [{r.get('status')}]")

    by_verdict: dict[str, list[str]] = {}
    for r in results:
        by_verdict.setdefault(r["verdict"], []).append(r["env"])

    summary = {
        "total": len(results),
        "by_verdict": {k: len(v) for k, v in by_verdict.items()},
        "broken_envs": (
            by_verdict.get("down", []) +
            by_verdict.get("http_error", []) +
            by_verdict.get("skipped", [])
        ),
        "details": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  PHASE 3 PAGE-LOAD SMOKE — {summary['total']} envs probed")
    print("=" * 60)
    for verdict, envs in by_verdict.items():
        print(f"  {verdict:<12}: {len(envs)}")
    if summary["broken_envs"]:
        print("\n  Broken envs (need investigation):")
        for e in summary["broken_envs"]:
            print(f"    - {e}")
    print(f"\n[saved] {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
