"""
DR Judge runner CLI.

Runs the LLM-as-judge detection rate evaluator on a sample manifest
or the full run directory for llama4_v3_seeds1to5_full_re.

Modes:
  --mode sample   Read session paths from a manifest JSON (e.g. sample_c0_200.json)
  --mode full     Discover and judge all sessions under --run-dir

Output:
  <out-dir>/dr_results_<pool_name>.json   — raw judge verdicts per step
  <out-dir>/dr_summary_<pool_name>.json   — per-session detection summary table

Usage (sample):
  python scripts/dr_judge_run.py \\
    --manifest agent/logs/v2/llama4_dr_judge/sample_c0_200.json \\
    --out-dir  agent/logs/v2/llama4_dr_judge \\
    --mode sample

Usage (full dataset):
  python scripts/dr_judge_run.py \\
    --run-dir agent/logs/v2/llama4_v3_seeds1to5_full_re \\
    --out-dir agent/logs/v2/llama4_dr_judge \\
    --mode full

Options:
  --primary-model     OpenRouter model for primary judge (default: openai/gpt-4o-mini)
  --secondary-model   OpenRouter model for secondary judge (default: meta-llama/llama-4-scout)
  --no-secondary      Skip secondary judge (faster; skips kappa computation)
  --max-concurrent    Session-level concurrency (default: 4)
  --pool-name         Tag for output filenames (default: inferred from manifest or "full")
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Resolve project root (scripts/ is one level below repo root)
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.evaluation.dr_judge import DRJudge, compute_kappa, _SKIP_NAMES, _SKIP_SUFFIXES  # noqa: E402 -- after sys.path


def _load_manifest_paths(manifest_path: Path) -> tuple[list[Path], str]:
    """Load session file paths from a manifest JSON. Returns (paths, pool_name)."""
    with open(manifest_path) as f:
        manifest = json.load(f)
    pool_name = manifest.get("pool", manifest_path.stem)
    paths = [Path(s["path"]) for s in manifest["sessions"]]
    return paths, pool_name


def _discover_session_files(run_dir: Path) -> list[Path]:
    """Enumerate all session log files under run_dir (recursive)."""
    return sorted(
        p for p in run_dir.glob("**/*.json")
        if p.name not in _SKIP_NAMES
        and not any(p.name.endswith(s) for s in _SKIP_SUFFIXES)
        and "_score" not in p.name
    )


def _build_summary_table(results: list[dict]) -> list[dict]:
    """Build a flat per-session summary table from judge results."""
    rows = []
    for sess in results:
        rows.append({
            "env": sess.get("env"),
            "condition": sess.get("condition"),
            "seed": sess.get("seed"),
            "any_detection_primary": sess.get("any_detection", False),
            "detection_count_primary": sess.get("detection_count", 0),
            "steps": len(sess.get("primary", [])),
            "any_detection_secondary": any(r["detected"] for r in sess.get("secondary", [])) if sess.get("secondary") else None,
        })
    return rows


async def run_judge(
    paths: list[Path],
    primary_model: str,
    secondary_model: str,
    run_secondary: bool,
    max_concurrent: int,
    openrouter_api_key: str | None,
) -> list[dict]:
    judge = DRJudge(
        primary_model=primary_model,
        secondary_model=secondary_model,
        openrouter_api_key=openrouter_api_key,
    )
    return await judge.judge_session_batch(
        paths,
        run_secondary=run_secondary,
        max_concurrent=max_concurrent,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DR judge on sample manifest or full dataset")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("--manifest", type=Path, help="Path to a sample manifest JSON (--mode sample)")
    mode_grp.add_argument("--run-dir", type=Path, help="Run directory root (--mode full)")

    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    parser.add_argument(
        "--primary-model", default="openai/gpt-4o-mini",
        help="Primary judge model (default: openai/gpt-4o-mini)",
    )
    parser.add_argument(
        "--secondary-model", default="meta-llama/llama-4-scout",
        help="Secondary judge model (default: meta-llama/llama-4-scout)",
    )
    parser.add_argument(
        "--no-secondary", action="store_true",
        help="Skip secondary judge (no kappa; faster)",
    )
    parser.add_argument("--max-concurrent", type=int, default=4, help="Session concurrency (default: 4)")
    parser.add_argument("--pool-name", default=None, help="Tag for output filenames")
    parser.add_argument("--api-key", default=None, help="OpenRouter API key (overrides env var)")

    args = parser.parse_args()

    # Resolve paths and pool name
    if args.manifest:
        log_paths, pool_name = _load_manifest_paths(args.manifest)
        pool_name = args.pool_name or pool_name
    else:
        log_paths = _discover_session_files(args.run_dir)
        pool_name = args.pool_name or "full"

    if not log_paths:
        print(f"[dr_judge_run] ERROR: No session files found.")
        sys.exit(1)

    # Filter to paths that actually exist
    missing = [p for p in log_paths if not p.exists()]
    if missing:
        print(f"[dr_judge_run] WARNING: {len(missing)} paths not found on disk (skipping):")
        for p in missing[:5]:
            print(f"  {p}")
        if len(missing) > 5:
            print(f"  ... and {len(missing)-5} more")
    log_paths = [p for p in log_paths if p.exists()]

    run_secondary = not args.no_secondary
    print(f"[dr_judge_run] Pool '{pool_name}': {len(log_paths)} sessions")
    print(f"[dr_judge_run] Primary: {args.primary_model}")
    if run_secondary:
        print(f"[dr_judge_run] Secondary: {args.secondary_model}")
    print(f"[dr_judge_run] Concurrency: {args.max_concurrent}")

    t0 = time.time()
    results = asyncio.run(run_judge(
        log_paths,
        primary_model=args.primary_model,
        secondary_model=args.secondary_model,
        run_secondary=run_secondary,
        max_concurrent=args.max_concurrent,
        openrouter_api_key=args.api_key,
    ))
    elapsed = time.time() - t0

    kappa = compute_kappa(results) if run_secondary else None

    # --- Full results JSON ---
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    results_path = out_dir / f"dr_results_{pool_name}.json"
    full_output = {
        "pool": pool_name,
        "primary_judge": args.primary_model,
        "secondary_judge": args.secondary_model if run_secondary else None,
        "inter_judge_kappa": kappa,
        "num_sessions": len(results),
        "elapsed_sec": round(elapsed, 1),
        "sessions": results,
    }
    with open(results_path, "w") as f:
        json.dump(full_output, f, indent=2, default=str)

    # --- Summary table JSON ---
    summary_path = out_dir / f"dr_summary_{pool_name}.json"
    summary_table = _build_summary_table(results)
    with open(summary_path, "w") as f:
        json.dump(summary_table, f, indent=2)

    # --- Console report ---
    any_det = sum(1 for r in results if r.get("any_detection"))
    det_rate = any_det / len(results) * 100 if results else 0

    by_condition: dict[str, list] = {}
    for r in results:
        c = r.get("condition", "?")
        by_condition.setdefault(c, []).append(r.get("any_detection", False))

    print(f"\n[dr_judge_run] Done in {elapsed:.0f}s")
    print(f"  Sessions judged : {len(results)}")
    print(f"  Any detection   : {any_det}/{len(results)} ({det_rate:.1f}%)")
    if kappa is not None:
        print(f"  Inter-judge kappa: {kappa}")
    print(f"\n  Per-condition:")
    for cond in sorted(by_condition):
        vals = by_condition[cond]
        rate = sum(vals) / len(vals) * 100
        print(f"    {cond}: {sum(vals)}/{len(vals)} ({rate:.1f}%)")
    print(f"\n  Full results  -> {results_path}")
    print(f"  Summary table -> {summary_path}")


if __name__ == "__main__":
    main()
