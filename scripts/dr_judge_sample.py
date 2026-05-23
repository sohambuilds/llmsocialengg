"""
DR Judge sampling infrastructure.

Draws stratified sample manifests from a parallel-runner run directory
for the LLM-as-judge DR validation pipeline.

Three sample pools:
  --pool c0      200-session C0 validation pool (2 seeds × up to 100 envs)
  --pool c123    50 sessions per condition across C1/C2/C3 (stratified by env)
  --pool recall  Judge-negative recall slice: sessions where judge=NOT_DETECTED;
                 requires --judge-results pointing at a prior judge output JSON.

Output:
  <outdir>/sample_c0_200.json       — C0 manifest
  <outdir>/sample_c123_150.json     — C1/C2/C3 combined manifest
  <outdir>/sample_recall_neg.json   — judge-negative recall manifest

Manifest schema:
  {
    "pool": "c0",
    "n": 200,
    "sessions": [
      {
        "path": "agent/logs/.../session.json",
        "env": "gov_portal",
        "condition": "C0",
        "seed": 1,
        "keyword_dr": "UNDETECTED"   # from meta.json
      }, ...
    ]
  }

Usage:
  python scripts/dr_judge_sample.py --run-dir agent/logs/v2/llama4_v3_seeds1to5_full_re \\
      --out-dir agent/logs/v2/llama4_dr_judge --pool c0

  python scripts/dr_judge_sample.py --run-dir agent/logs/v2/llama4_v3_seeds1to5_full_re \\
      --out-dir agent/logs/v2/llama4_dr_judge --pool c123

  python scripts/dr_judge_sample.py --run-dir agent/logs/v2/llama4_v3_seeds1to5_full_re \\
      --out-dir agent/logs/v2/llama4_dr_judge --pool recall \\
      --judge-results agent/logs/v2/llama4_dr_judge/dr_results_c0.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


# Files to exclude from session enumeration
_SKIP_NAMES = {
    "meta.json", "manifest.json", "status.json",
    "aggregate_results.json", "dr_judge_results.json",
}
_SKIP_SUFFIXES = (".score.json",)


def _is_session_file(p: Path) -> bool:
    if p.name in _SKIP_NAMES:
        return False
    if any(p.name.endswith(s) for s in _SKIP_SUFFIXES):
        return False
    if "_score" in p.name:
        return False
    return p.suffix == ".json"


def _load_meta(session_path: Path) -> dict[str, Any]:
    """Load the meta.json sibling of a session file."""
    meta_path = session_path.parent / "meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {}


def _session_record(session_path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    cell = meta.get("cell", {})
    summary = meta.get("summary", {})
    return {
        "path": str(session_path),
        "env": cell.get("env", session_path.parts[-4] if len(session_path.parts) >= 4 else "unknown"),
        "condition": cell.get("condition", "unknown"),
        "seed": cell.get("seed", 0),
        "keyword_dr": summary.get("DR", "UNDETECTED"),
        "reached_trap": summary.get("reached_trap", False),
        "tcr": summary.get("TCR", ""),
    }


def enumerate_sessions(run_dir: Path, condition: str | None = None) -> list[dict[str, Any]]:
    """Enumerate all session files under run_dir, optionally filtered by condition."""
    records = []
    for p in sorted(run_dir.glob("**/*.json")):
        if not _is_session_file(p):
            continue
        meta = _load_meta(p)
        rec = _session_record(p, meta)
        if condition and rec["condition"] != condition:
            continue
        if rec["condition"] == "unknown":
            continue
        records.append(rec)
    return records


def draw_c0_pool(
    run_dir: Path,
    n: int = 200,
    seeds_per_env: int = 2,
    rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Draw a C0 validation pool of n sessions.
    Strategy: enumerate all C0 sessions, group by env, pick seeds_per_env per env,
    then cap at n (shuffled).
    """
    rng = random.Random(rng_seed)
    all_c0 = enumerate_sessions(run_dir, condition="C0")

    # Group by env
    by_env: dict[str, list[dict]] = {}
    for rec in all_c0:
        by_env.setdefault(rec["env"], []).append(rec)

    sample: list[dict[str, Any]] = []
    for env, recs in sorted(by_env.items()):
        chosen = rng.sample(recs, min(seeds_per_env, len(recs)))
        sample.extend(chosen)

    rng.shuffle(sample)
    return sample[:n]


def draw_c123_pool(
    run_dir: Path,
    n_per_condition: int = 50,
    rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Draw ~n_per_condition sessions from each of C1, C2, C3.
    Strategy: enumerate each condition, group by env, pick 1 seed per env,
    then cap at n_per_condition (shuffled).
    """
    rng = random.Random(rng_seed)
    sample: list[dict[str, Any]] = []

    for cond in ("C1", "C2", "C3"):
        recs = enumerate_sessions(run_dir, condition=cond)
        by_env: dict[str, list[dict]] = {}
        for rec in recs:
            by_env.setdefault(rec["env"], []).append(rec)

        cond_sample: list[dict[str, Any]] = []
        for env, env_recs in sorted(by_env.items()):
            cond_sample.append(rng.choice(env_recs))

        rng.shuffle(cond_sample)
        sample.extend(cond_sample[:n_per_condition])

    return sample


def draw_recall_pool(
    judge_results_path: Path,
    run_dir: Path,
    n: int = 50,
    rng_seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Draw judge-negative sessions for recall audit.

    Loads a prior judge output JSON, finds sessions where primary judge
    returned any_detection=False, then intersects with session files in run_dir.
    These are sampled for human review to estimate judge recall.
    """
    rng = random.Random(rng_seed)

    with open(judge_results_path) as f:
        judge_output = json.load(f)

    sessions_in_results = judge_output.get("sessions", [])

    # Build a path-keyed dict from the manifest embedded in the results (if present)
    # or fall back to matching on env+condition+seed.
    negatives: list[dict[str, Any]] = []
    for session in sessions_in_results:
        if not session.get("any_detection", True):
            negatives.append(session)

    print(f"[recall] Found {len(negatives)} judge-negative sessions in {judge_results_path.name}")

    # Re-enrich with file paths from run_dir so the manifest has usable paths
    # Build an (env, condition, seed) -> path index
    path_index: dict[tuple, str] = {}
    for p in sorted(run_dir.glob("**/*.json")):
        if not _is_session_file(p):
            continue
        meta = _load_meta(p)
        cell = meta.get("cell", {})
        key = (cell.get("env"), cell.get("condition"), cell.get("seed"))
        if all(k is not None for k in key):
            path_index[key] = str(p)

    enriched: list[dict[str, Any]] = []
    for sess in negatives:
        key = (sess.get("env"), sess.get("condition"), sess.get("seed"))
        path = path_index.get(key, "")
        if not path:
            continue
        meta = _load_meta(Path(path))
        rec = _session_record(Path(path), meta)
        enriched.append(rec)

    rng.shuffle(enriched)
    return enriched[:n]


def save_manifest(pool: list[dict[str, Any]], pool_name: str, out_path: Path) -> None:
    manifest = {
        "pool": pool_name,
        "n": len(pool),
        "sessions": pool,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[sample] Wrote {len(pool)} sessions -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw DR judge sample manifests")
    parser.add_argument(
        "--run-dir",
        required=True,
        type=Path,
        help="Root of the parallel-runner run (e.g. agent/logs/v2/llama4_v3_seeds1to5_full_re)",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Directory to write manifest JSON files",
    )
    parser.add_argument(
        "--pool",
        choices=["c0", "c123", "recall", "all"],
        default="c0",
        help="Which pool to draw (default: c0). 'all' draws c0 + c123.",
    )
    parser.add_argument("--n-c0", type=int, default=200, help="Size of C0 pool (default: 200)")
    parser.add_argument("--n-c123", type=int, default=50, help="Sessions per condition for C1/C2/C3 (default: 50)")
    parser.add_argument("--n-recall", type=int, default=50, help="Size of recall audit pool (default: 50)")
    parser.add_argument("--rng-seed", type=int, default=42, help="RNG seed for reproducibility (default: 42)")
    parser.add_argument(
        "--judge-results",
        type=Path,
        help="Path to prior judge output JSON (required for --pool recall)",
    )
    args = parser.parse_args()

    if args.pool in ("c0", "all"):
        pool = draw_c0_pool(args.run_dir, n=args.n_c0, rng_seed=args.rng_seed)
        save_manifest(pool, "c0", args.out_dir / "sample_c0_200.json")

    if args.pool in ("c123", "all"):
        pool = draw_c123_pool(args.run_dir, n_per_condition=args.n_c123, rng_seed=args.rng_seed)
        save_manifest(pool, "c123", args.out_dir / "sample_c123_150.json")

    if args.pool == "recall":
        if not args.judge_results:
            parser.error("--judge-results is required for --pool recall")
        pool = draw_recall_pool(args.judge_results, args.run_dir, n=args.n_recall, rng_seed=args.rng_seed)
        save_manifest(pool, "recall", args.out_dir / "sample_recall_neg.json")


if __name__ == "__main__":
    main()
