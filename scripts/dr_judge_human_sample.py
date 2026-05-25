"""
Draw a stratified 50-session sample for the judge-vs-human DR validation.

Output: three CSVs in --out-dir
  labels_A.csv             — annotator A: session_id, env, condition, model,
                             agent_reasoning_text, your_label_0_or_1, notes
  labels_B.csv             — annotator B: same shape
  judge_ground_truth.csv   — hidden until labelling is done; contains the
                             primary-judge label per session_id

The two annotator files are identical so the two raters can label independently.
The reasoning trace is a single newline-separated string per session — opens
fine in Excel / Google Sheets with cell-wrap turned on.

Stratification:
  - 4 models  x 4 conditions = 16 cells
  - ~3 sessions per cell, balanced ~50/50 between judge DR=1 and DR=0
  - reached_trap=True only (matches the F1 primary-form gating in §4)
  - excludes BROWSER_ERROR-terminated sessions (matches the retained pool)

Usage:
  python scripts/dr_judge_human_sample.py \\
    --judge-dirs agent/logs/v2/llama4_dr_judge \\
                 agent/logs/v2/gemini3_dr_judge \\
                 agent/logs/v2/haiku_dr_judge \\
                 agent/logs/v2/gpt5mini_dr_judge \\
    --out-dir agent/logs/v2/dr_human_label \\
    --n 50 --seed 20260525
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from collections import defaultdict


def load_judge_sessions(judge_dir: Path) -> list[dict]:
    """Load per-session judge results from <judge_dir>/dr_results_full.json."""
    results_path = judge_dir / "dr_results_full.json"
    with open(results_path) as f:
        d = json.load(f)
    return d["sessions"]


def find_session_file(model_run_root: Path, env: str, model_dir_name: str,
                      condition: str, seed: int) -> Path | None:
    """Locate the per-session JSON for a (env, model, condition, seed) cell."""
    cell_dir = model_run_root / env / model_dir_name / condition / f"seed_{seed}"
    if not cell_dir.is_dir():
        return None
    for f in cell_dir.glob("*.json"):
        name = f.name
        if name.endswith(".score.json") or name in ("meta.json", "manifest.json", "status.json"):
            continue
        return f
    return None


# Map from dr_results model identifier to (run-dir name, on-disk model dir name)
MODEL_RUN_MAP = {
    "meta-llama/llama-4-scout":      ("llama4_v3_seeds1to5_full_re",  "Llama_4_Scout_(OpenRouter)"),
    "google/gemini-3-flash-preview": ("gemini3_v3_seeds1to5_full",    "Gemini_3_Flash_Preview_(OpenRouter)"),
    "anthropic/claude-haiku-4.5":    ("haiku_v3_seed1to5_full",       "Claude_Haiku_4.5_(OpenRouter)"),
    "openai/gpt-5-mini":             ("gpt5mini_v3_seed1to5_full",    "GPT-5_mini_(OpenRouter)"),
}


def short_model(model: str) -> str:
    m = model.lower()
    if "llama" in m:        return "Llama"
    if "gemini" in m:       return "Gemini"
    if "haiku" in m:        return "Haiku"
    if "gpt-5" in m:        return "GPT5mini"
    return model


def format_reasoning(session_path: Path) -> tuple[str, int, bool]:
    """Extract a flat newline-separated reasoning trace + step count + reached_trap.
       Returns ('', 0, False) if the session file is unreadable.
    """
    try:
        with open(session_path) as f:
            d = json.load(f)
    except Exception:
        return "", 0, False
    reached = bool(d.get("reached_trap", False))
    lines = []
    steps = d.get("steps", [])
    for s in steps:
        step_no = s.get("step", "?")
        url     = s.get("url", "")
        actions = s.get("actions", []) or []
        for a in actions:
            r = (a.get("reasoning") or "").strip()
            if r:
                lines.append(f"[step {step_no} @ {url}] {r}")
    return "\n".join(lines), len(steps), reached


def stratified_pick(candidates: list[dict], n_total: int, rng: random.Random) -> list[dict]:
    """Balance the picks across (model x condition) cells and within each cell
       across judge DR=1 / DR=0. Returns up to n_total picks."""
    cells = defaultdict(lambda: {"DR1": [], "DR0": []})
    for c in candidates:
        key = (c["model"], c["condition"])
        sub = "DR1" if c["judge_dr"] == 1 else "DR0"
        cells[key][sub].append(c)
    cell_keys = sorted(cells.keys())
    per_cell = max(1, n_total // len(cell_keys))
    picked = []
    for k in cell_keys:
        for sub in ("DR1", "DR0"):
            pool = cells[k][sub]
            rng.shuffle(pool)
            picked.extend(pool[: max(1, per_cell // 2)])
    # If under-quota, top up by random draws from any remaining candidate
    leftover = [c for c in candidates if c not in picked]
    rng.shuffle(leftover)
    while len(picked) < n_total and leftover:
        picked.append(leftover.pop())
    rng.shuffle(picked)
    return picked[:n_total]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dirs", nargs="+", required=True,
                    help="One or more <model>_dr_judge/ directories containing dr_results_full.json.")
    ap.add_argument("--run-root", default="agent/logs/v2",
                    help="Parent of the *_v3_seed*_full[_re] run directories (default: agent/logs/v2).")
    ap.add_argument("--out-dir", required=True,
                    help="Directory to write labels_A.csv, labels_B.csv, judge_ground_truth.csv.")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260525)
    ap.add_argument("--require-reach", action="store_true", default=True,
                    help="Restrict to reached_trap=True sessions (default: True).")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    run_root = Path(args.run_root)
    out_dir  = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load every judge result, attach session-file path + reasoning trace
    candidates: list[dict] = []
    for jd in args.judge_dirs:
        sessions = load_judge_sessions(Path(jd))
        for s in sessions:
            model = s["model"]
            run_map = MODEL_RUN_MAP.get(model)
            if run_map is None:
                continue
            run_dir_name, model_dir_name = run_map
            sf = find_session_file(run_root / run_dir_name,
                                   s["env"], model_dir_name,
                                   s["condition"], s["seed"])
            if sf is None:
                continue
            text, n_steps, reached = format_reasoning(sf)
            if not text:
                continue
            if args.require_reach and not reached:
                continue
            judge_dr = 1 if s["any_detection"] else 0
            candidates.append({
                "session_id": f"{short_model(model)}_{s['env']}_{s['condition']}_s{s['seed']}",
                "env":        s["env"],
                "condition":  s["condition"],
                "model":      model,
                "seed":       s["seed"],
                "n_steps":    n_steps,
                "agent_reasoning_text": text,
                "judge_dr":   judge_dr,
                "session_path": str(sf),
            })

    print(f"[sample] candidates after filtering: {len(candidates)}")
    if len(candidates) < args.n:
        print(f"[sample] WARNING: requested n={args.n} but only {len(candidates)} candidates available")

    picks = stratified_pick(candidates, args.n, rng)
    print(f"[sample] selected: {len(picks)}")

    # Cell-by-cell balance for the user's sanity
    balance = defaultdict(lambda: [0, 0])
    for p in picks:
        balance[(short_model(p["model"]), p["condition"])][p["judge_dr"]] += 1
    print("[sample] (model, condition) -> [DR=0 count, DR=1 count]:")
    for k in sorted(balance):
        print(f"   {k}: {balance[k]}")

    # 2. Write annotator CSVs (identical, blind: no judge_dr column)
    annotator_cols = [
        "session_id", "env", "condition", "model_family", "n_steps",
        "agent_reasoning_text",
        "your_label_0_or_1",
        "notes_optional",
    ]
    for who in ("A", "B"):
        path = out_dir / f"labels_{who}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(annotator_cols)
            for p in picks:
                w.writerow([
                    p["session_id"], p["env"], p["condition"],
                    short_model(p["model"]), p["n_steps"],
                    p["agent_reasoning_text"],
                    "",   # your_label_0_or_1
                    "",   # notes
                ])
        print(f"[sample] wrote {path}")

    # 3. Write the ground-truth CSV (do NOT show this to annotators until after)
    gt_path = out_dir / "judge_ground_truth.csv"
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["session_id", "judge_dr", "env", "condition",
                    "model_family", "session_path"])
        for p in picks:
            w.writerow([p["session_id"], p["judge_dr"], p["env"],
                        p["condition"], short_model(p["model"]),
                        p["session_path"]])
    print(f"[sample] wrote {gt_path} (KEEP HIDDEN UNTIL LABELLING IS DONE)")

    # 4. Quick reproducibility breadcrumb
    meta = {
        "seed": args.seed,
        "n_requested": args.n,
        "n_drawn": len(picks),
        "judge_dirs": args.judge_dirs,
        "run_root": args.run_root,
        "require_reach": args.require_reach,
        "balance": {f"{k[0]}_{k[1]}": v for k, v in balance.items()},
    }
    with open(out_dir / "sample_meta.json", "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
