"""
Cell-count smoke test: 2 envs x N models x 1 seed x 4 conditions.

Per the phase4 plan, this is supposed to be 2 envs x 4 models x 4 cond
= 32 runs. Only Groq models (llama4, gpt-oss) are runnable without a
Gemini key; the others (gemini, claude-sonnet, GPT-5) are recorded as
SKIPPED for projection.

Output:
  agent/logs/smoke-matrix/cell_timings.json     - per-cell timing
  agent/logs/smoke-matrix/projection.json       - 7,480-run estimate
  agent/logs/smoke-matrix/<run_name>/...        - per-run logs
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows so prints containing emoji / arrows
# (e.g. ⬇ from a website's HTML rendered into the agent log) do
# not crash with cp1252 charmap errors.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

sys.path.insert(0, ".")

from agent.runner import run_single_env


ENVS = ["cluttered_downloads", "marketplace"]
GROQ_MODELS = [
    "openai/gpt-oss-120b",
]
OPENROUTER_MODELS = [
    "meta-llama/llama-4-scout",
]
SKIPPED_MODELS = ["gemini-3-flash-preview", "claude-haiku-4-5", "gpt-5"]
CONDITIONS = ["C0", "C1", "C2", "C3"]
MAX_STEPS = 20
SEED = 42

OUTPUT_DIR = Path("agent/logs/smoke-matrix")
TIMINGS_PATH = OUTPUT_DIR / "cell_timings.json"
PROJECTION_PATH = OUTPUT_DIR / "projection.json"


async def run_cell(env: str, model: str, condition: str, run_name: str, api_key: str) -> dict:
    t0 = time.time()
    try:
        report = await run_single_env(
            env_name=env,
            model=model,
            max_steps=MAX_STEPS,
            headless=True,
            api_key=api_key,
            output_dir=OUTPUT_DIR,
            condition=condition,
            seed=SEED,
        )
        elapsed = time.time() - t0
        return {
            "env": env,
            "model": model,
            "condition": condition,
            "seed": SEED,
            "elapsed_sec": round(elapsed, 2),
            "status": "ok",
            "summary": report.get("summary", {}),
            "data_quality": report.get("data_quality", {}),
            "error": None,
        }
    except Exception as exc:
        elapsed = time.time() - t0
        return {
            "env": env,
            "model": model,
            "condition": condition,
            "seed": SEED,
            "elapsed_sec": round(elapsed, 2),
            "status": "error",
            "summary": {},
            "data_quality": {},
            "error": str(exc),
        }


def project(cells: list[dict]) -> dict:
    ok = [c for c in cells if c["status"] == "ok"]
    if not ok:
        return {"error": "no successful cells - cannot project"}
    times = [c["elapsed_sec"] for c in ok]
    mean_t = sum(times) / len(times)
    max_t = max(times)
    min_t = min(times)

    n_runs_full = 91 * 4 * 5 * 4  # 7,280 attack runs
    n_runs_twins = 10 * 4 * 5      # 200 benign-twin runs
    n_total = n_runs_full + n_runs_twins  # 7,480

    sequential_sec = n_total * mean_t
    sequential_days = sequential_sec / 86400

    projections = {}
    for parallelism in (1, 4, 8, 16):
        sec = sequential_sec / parallelism
        projections[f"parallel_{parallelism}"] = {
            "seconds": round(sec, 1),
            "hours": round(sec / 3600, 2),
            "days": round(sec / 86400, 2),
        }

    return {
        "cells_observed": len(ok),
        "cells_observed_groq_only": True,
        "skipped_models": SKIPPED_MODELS,
        "mean_sec_per_cell": round(mean_t, 2),
        "min_sec_per_cell": round(min_t, 2),
        "max_sec_per_cell": round(max_t, 2),
        "max_steps_used": MAX_STEPS,
        "n_runs_attack": n_runs_full,
        "n_runs_twins": n_runs_twins,
        "n_runs_total": n_total,
        "sequential_days_at_mean": round(sequential_days, 2),
        "projections_by_parallelism": projections,
        "fits_in_5_days_at_8x": projections["parallel_8"]["days"] <= 5.0,
        "recommendation": (
            "Within 5-day budget at parallelism=8"
            if projections["parallel_8"]["days"] <= 5.0
            else "EXCEEDS 5 days even at parallelism=8 - apply scope cut "
                 "(drop C1 to keep C0/C2/C3 OR drop mitigation seeds to n=3 "
                 "OR cut benign twins to 5)"
        ),
    }


async def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: set GROQ_API_KEY")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cells: list[dict] = []
    SMOKE_MODELS = GROQ_MODELS + OPENROUTER_MODELS
    total = len(ENVS) * len(SMOKE_MODELS) * len(CONDITIONS)
    idx = 0
    for env in ENVS:
        for model in SMOKE_MODELS:
            for cond in CONDITIONS:
                idx += 1
                run_name = f"smoke_{env}_{cond}_{model.replace('/', '_')}"
                print(f"\n=== CELL {idx}/{total}: {env} | {model} | {cond} ===")
                result = await run_cell(env, model, cond, run_name, api_key)
                print(f"  -> {result['status']} in {result['elapsed_sec']}s")
                cells.append(result)
                with open(TIMINGS_PATH, "w") as f:
                    json.dump({"cells": cells, "total_planned": total}, f, indent=2)

    proj = project(cells)
    with open(PROJECTION_PATH, "w") as f:
        json.dump(proj, f, indent=2)

    print("\n" + "=" * 60)
    print("  SMOKE MATRIX SUMMARY")
    print("=" * 60)
    ok = [c for c in cells if c["status"] == "ok"]
    err = [c for c in cells if c["status"] == "error"]
    print(f"  ok:    {len(ok)}/{len(cells)}")
    print(f"  error: {len(err)}/{len(cells)}")
    if ok:
        print(f"  mean sec/cell: {proj['mean_sec_per_cell']}")
        print(f"  sequential days @ mean: {proj['sequential_days_at_mean']}")
        print(f"  @8x parallelism (days): {proj['projections_by_parallelism']['parallel_8']['days']}")
        print(f"  verdict: {proj['recommendation']}")
    print(f"\n[saved] {TIMINGS_PATH}")
    print(f"[saved] {PROJECTION_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
