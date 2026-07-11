"""
Parallel run harness for the full v2 sweep.

Goals:
- Worker pool: N concurrent envs (never two workers on the same env so
  per-env `/api/captured` state doesn't collide between cells).
- Retry on browser / Playwright crash: bounded retries with backoff.
- Resumable: skips cells whose `score.json` already exists. Rerun the
  same `--run-id` to pick up where the previous run left off.
- Log dir layout (per phase4-checklist):
      agent/logs/v2/<run_id>/<env>/<model_label>/<condition>/seed_<n>/
        session.json    # raw step log (whatever SessionLogger writes)
        *.score.json    # scorer output, written by run_single_env
        meta.json       # cell-level timing, attempts, status, error

Usage:
    python -m agent.parallel_runner \\
        --run-id v2-2026-05-13 \\
        --envs benchmark \\
        --models all \\
        --conditions C0 C1 C2 C3 \\
        --seeds 1 2 3 4 5 \\
        --workers 4 \\
        --max-steps 30 \\
        --max-retries 2

Resume by re-invoking with the same `--run-id`.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Force UTF-8 stdout on Windows so non-ASCII chars from agent / scorer
# prints don't crash with cp1252 errors.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

from .core.llm_factory import (
    MODEL_REGISTRY,
    MODEL_ALIASES,
    resolve_model_name,
    get_model_info,
)
from .runner import (
    AVAILABLE_ENVS,
    BENCHMARK_MODELS,
    ENV_GROUPS,
    run_single_env,
)


# ---- Cell model ----------------------------------------------------------

@dataclass
class Cell:
    env: str
    model: str
    condition: str
    seed: int

    def model_label(self) -> str:
        return get_model_info(self.model).get("label", self.model).replace(" ", "_")

    def dir_under(self, run_root: Path) -> Path:
        return run_root / self.env / self.model_label() / self.condition / f"seed_{self.seed}"

    def short(self) -> str:
        return f"{self.env} | {self.model_label()} | {self.condition} | s{self.seed}"


@dataclass
class CellResult:
    cell: Cell
    status: str  # "ok" | "skipped" | "failed"
    attempts: int = 0
    elapsed_sec: float = 0.0
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


# ---- Browser-crash classifier --------------------------------------------

_RETRY_HINTS = (
    "playwright",
    "targetclosed",
    "browser has been closed",
    "browser context",
    "page.goto",
    "navigation",
    "net::err_",
    "timeoutexception",
    "timeouterror",
    "connectionreset",
    "connectionresetbyremote",
    "loadstate",
)


def _looks_like_browser_crash(exc: BaseException) -> bool:
    msg = (str(exc) + " " + type(exc).__name__).lower()
    return any(hint in msg for hint in _RETRY_HINTS)


# ---- Worker pool ---------------------------------------------------------

class ParallelRunner:
    def __init__(
        self,
        run_id: str,
        cells: list[Cell],
        output_root: Path,
        max_steps: int,
        api_key: Optional[str],
        workers: int,
        max_retries: int,
        guardrail_model: str = "openai/gpt-4o-mini",
        retry_base_delay: float = 5.0,
    ):
        self.run_id = run_id
        self.cells = cells
        self.output_root = output_root
        self.max_steps = max_steps
        self.api_key = api_key
        self.workers = max(1, workers)
        self.max_retries = max(0, max_retries)
        self.guardrail_model = guardrail_model
        self.retry_base_delay = retry_base_delay

        self.run_root = output_root / "v2" / run_id
        self.run_root.mkdir(parents=True, exist_ok=True)

        self._status_path = self.run_root / "status.json"
        self._manifest_path = self.run_root / "manifest.json"
        self._results: list[CellResult] = []
        self._results_lock = asyncio.Lock()

    # ---- Manifest / resume -----------------------------------------------

    def write_manifest(self) -> None:
        cells_payload = [asdict(c) for c in self.cells]
        manifest = {
            "run_id": self.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "n_cells": len(self.cells),
            "max_steps": self.max_steps,
            "max_retries": self.max_retries,
            "workers": self.workers,
            "cells": cells_payload,
        }
        with open(self._manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def _cell_already_done(self, cell: Cell) -> bool:
        """True if score.json exists for this cell's dir."""
        d = cell.dir_under(self.run_root)
        if not d.exists():
            return False
        # The scorer writes <session>.score.json. We accept any file in
        # the dir matching *.score.json as evidence of completion.
        for f in d.glob("*.score.json"):
            return True
        # Also accept an explicit meta.json with status=ok
        meta = d / "meta.json"
        if meta.exists():
            try:
                with open(meta) as fh:
                    data = json.load(fh)
                if data.get("status") == "ok":
                    return True
            except Exception:
                pass
        return False

    def partition_cells(self) -> tuple[list[Cell], list[Cell]]:
        """Return (remaining, already_done)."""
        done = []
        todo = []
        for c in self.cells:
            (done if self._cell_already_done(c) else todo).append(c)
        return todo, done

    # ---- Status snapshot -------------------------------------------------

    async def _write_status(self) -> None:
        async with self._results_lock:
            counts = {"ok": 0, "failed": 0, "skipped": 0}
            for r in self._results:
                counts[r.status] = counts.get(r.status, 0) + 1
            snapshot = {
                "run_id": self.run_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "n_total": len(self.cells),
                "n_recorded": len(self._results),
                "counts": counts,
                "results": [
                    {
                        **asdict(r.cell),
                        "status": r.status,
                        "attempts": r.attempts,
                        "elapsed_sec": r.elapsed_sec,
                        "error": r.error,
                        "started_at": r.started_at,
                        "finished_at": r.finished_at,
                    }
                    for r in self._results
                ],
            }
            with open(self._status_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)

    # ---- Cell runner -----------------------------------------------------

    async def _run_cell(self, cell: Cell) -> CellResult:
        d = cell.dir_under(self.run_root)
        d.mkdir(parents=True, exist_ok=True)
        meta_path = d / "meta.json"

        attempt = 0
        last_error: Optional[str] = None
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        while attempt <= self.max_retries:
            attempt += 1
            try:
                report = await run_single_env(
                    env_name=cell.env,
                    model=cell.model,
                    max_steps=self.max_steps,
                    headless=True,
                    api_key=self.api_key,
                    output_dir=d,
                    condition=cell.condition,
                    seed=cell.seed,
                    guardrail_model=self.guardrail_model,
                )
                elapsed = time.time() - t0
                finished_at = datetime.now(timezone.utc).isoformat()
                meta = {
                    "cell": asdict(cell),
                    "status": "ok",
                    "attempts": attempt,
                    "elapsed_sec": round(elapsed, 2),
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "summary": report.get("summary", {}),
                    "data_quality": report.get("data_quality", {}),
                }
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, default=str)
                return CellResult(
                    cell=cell,
                    status="ok",
                    attempts=attempt,
                    elapsed_sec=elapsed,
                    started_at=started_at,
                    finished_at=finished_at,
                )
            except Exception as exc:
                tb = traceback.format_exc()
                last_error = f"{type(exc).__name__}: {exc}"
                recoverable = _looks_like_browser_crash(exc)
                print(
                    f"  [cell-error] {cell.short()} attempt {attempt}/"
                    f"{self.max_retries + 1}: {last_error[:160]}"
                )
                if recoverable and attempt <= self.max_retries:
                    delay = self.retry_base_delay * (2 ** (attempt - 1))
                    print(f"  [cell-retry] browser-side error — waiting {delay}s then retry")
                    await asyncio.sleep(delay)
                    continue
                # Permanent failure — record and exit
                elapsed = time.time() - t0
                finished_at = datetime.now(timezone.utc).isoformat()
                meta = {
                    "cell": asdict(cell),
                    "status": "failed",
                    "attempts": attempt,
                    "elapsed_sec": round(elapsed, 2),
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error": last_error,
                    "traceback": tb,
                    "recoverable": recoverable,
                }
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, default=str)
                return CellResult(
                    cell=cell,
                    status="failed",
                    attempts=attempt,
                    elapsed_sec=elapsed,
                    error=last_error,
                    started_at=started_at,
                    finished_at=finished_at,
                )

        return CellResult(
            cell=cell,
            status="failed",
            attempts=attempt,
            elapsed_sec=time.time() - t0,
            error=last_error,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )

    # ---- Worker loop -----------------------------------------------------

    async def _worker(
        self,
        worker_id: int,
        env_queue: asyncio.Queue[str | None],
        cells_by_env: dict[str, list[Cell]],
    ) -> None:
        while True:
            env = await env_queue.get()
            if env is None:
                env_queue.task_done()
                return
            cells = cells_by_env[env]
            print(f"\n[w{worker_id}] >>> picking env={env} ({len(cells)} cells)")
            for cell in cells:
                if self._cell_already_done(cell):
                    print(f"[w{worker_id}] skip (already done): {cell.short()}")
                    async with self._results_lock:
                        self._results.append(CellResult(
                            cell=cell, status="skipped", attempts=0,
                            elapsed_sec=0.0,
                            started_at=datetime.now(timezone.utc).isoformat(),
                            finished_at=datetime.now(timezone.utc).isoformat(),
                        ))
                    await self._write_status()
                    continue
                print(f"[w{worker_id}] run: {cell.short()}")
                result = await self._run_cell(cell)
                async with self._results_lock:
                    self._results.append(result)
                await self._write_status()
                print(
                    f"[w{worker_id}] {result.status}: {cell.short()} "
                    f"in {result.elapsed_sec:.1f}s (attempts={result.attempts})"
                )
            env_queue.task_done()

    # ---- Top-level run ---------------------------------------------------

    async def run(self) -> dict[str, Any]:
        # Build / refresh manifest
        self.write_manifest()
        todo, done = self.partition_cells()
        print(f"\nRun id:     {self.run_id}")
        print(f"Out root:   {self.run_root}")
        print(f"Total:      {len(self.cells)}")
        print(f"Already done (skip): {len(done)}")
        print(f"To run:     {len(todo)}")
        print(f"Workers:    {self.workers}")
        print(f"Max retries:{self.max_retries}")

        # Record skipped cells up-front (so status.json reflects them)
        for c in done:
            self._results.append(CellResult(
                cell=c, status="skipped", attempts=0, elapsed_sec=0.0,
            ))
        await self._write_status()

        if not todo:
            print("\nNothing to run — every cell already has a score.json")
            return self._final_summary()

        cells_by_env: dict[str, list[Cell]] = {}
        for c in todo:
            cells_by_env.setdefault(c.env, []).append(c)

        # Queue of envs; workers drain it
        env_queue: asyncio.Queue[str | None] = asyncio.Queue()
        # Push larger env-bundles first so big envs don't trail at the end
        for env in sorted(cells_by_env, key=lambda e: -len(cells_by_env[e])):
            env_queue.put_nowait(env)
        # Sentinel per worker
        for _ in range(self.workers):
            env_queue.put_nowait(None)

        tasks = [
            asyncio.create_task(self._worker(i + 1, env_queue, cells_by_env))
            for i in range(self.workers)
        ]
        await asyncio.gather(*tasks)
        await self._write_status()

        return self._final_summary()

    def _final_summary(self) -> dict[str, Any]:
        counts = {"ok": 0, "failed": 0, "skipped": 0}
        for r in self._results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return {
            "run_id": self.run_id,
            "n_total": len(self.cells),
            "n_recorded": len(self._results),
            "counts": counts,
            "status_path": str(self._status_path),
        }


# ---- CLI -----------------------------------------------------------------

def _resolve_envs(env_args: list[str]) -> list[str]:
    out: list[str] = []
    for a in env_args:
        if a in ENV_GROUPS:
            out.extend(ENV_GROUPS[a])
        else:
            out.append(a)
    # Dedup, preserve order
    seen = set()
    deduped = []
    for e in out:
        if e not in seen:
            seen.add(e)
            deduped.append(e)
    return deduped


def _resolve_models(model_args: list[str]) -> list[str]:
    out: list[str] = []
    for a in model_args:
        if a == "all":
            out.extend(BENCHMARK_MODELS)
        else:
            out.append(resolve_model_name(a))
    seen = set()
    deduped = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Parallel run harness for the full v2 sweep",
    )
    p.add_argument("--run-id", default=None,
                   help="Unique label for this run. Re-use to resume.")
    p.add_argument("--envs", nargs="+", default=["benchmark"],
                   help="Env group(s) or specific env(s)")
    p.add_argument("--models", nargs="+", default=["all"],
                   help="Model alias(es) or 'all'")
    p.add_argument("--conditions", nargs="+", default=["C0", "C1", "C2", "C3", "C4"],
                   choices=["C0", "C1", "C2", "C3", "C4"])
    p.add_argument("--guardrail-model", default="openai/gpt-4o-mini",
                   help="Guardrail model to use for C4")
    p.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-steps", type=int, default=30)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--api-key", default=None)
    p.add_argument("--output-root", default="agent/logs")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    envs = _resolve_envs(args.envs)
    models = _resolve_models(args.models)

    cells: list[Cell] = []
    for env in envs:
        for model in models:
            for cond in args.conditions:
                for seed in args.seeds:
                    cells.append(Cell(env=env, model=model, condition=cond, seed=seed))

    run_id = args.run_id or datetime.now().strftime("v2_%Y%m%d_%H%M%S")
    output_root = Path(args.output_root)
    runner = ParallelRunner(
        run_id=run_id,
        cells=cells,
        output_root=output_root,
        max_steps=args.max_steps,
        api_key=args.api_key,
        workers=args.workers,
        max_retries=args.max_retries,
        guardrail_model=args.guardrail_model,
    )

    if args.dry_run:
        runner.write_manifest()
        todo, done = runner.partition_cells()
        print(f"\nDRY RUN — run_id={run_id}")
        print(f"  Envs:       {len(envs)}")
        print(f"  Models:     {len(models)}")
        print(f"  Conditions: {args.conditions}")
        print(f"  Seeds:      {args.seeds}")
        print(f"  Total:      {len(cells)}")
        print(f"  Already done (skip): {len(done)}")
        print(f"  To run:     {len(todo)}")
        print(f"  Workers:    {args.workers}")
        print(f"  Output:     {runner.run_root}")
        return

    summary = asyncio.run(runner.run())
    print("\n" + "=" * 60)
    print(f"  RUN COMPLETE — {run_id}")
    print("=" * 60)
    print(f"  total:    {summary['n_total']}")
    print(f"  ok:       {summary['counts']['ok']}")
    print(f"  failed:   {summary['counts']['failed']}")
    print(f"  skipped:  {summary['counts']['skipped']}")
    print(f"  status:   {summary['status_path']}")


if __name__ == "__main__":
    main()
