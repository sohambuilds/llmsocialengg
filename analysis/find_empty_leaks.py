"""Find score.json files where `fields_leaked` is empty.

These are the runs where the agent typed nothing the tracker flagged as PII —
useful for separating "never reached the trap" cases from "reached but didn't
leak" cases.

Usage:
    python analysis/find_empty_leaks.py
    python analysis/find_empty_leaks.py --run pilot_llama4_v2_overnight --condition C0
    python analysis/find_empty_leaks.py --run pilot_llama4_v2_overnight --condition all
"""

import argparse
import json
from pathlib import Path


def find_empty_leak_runs(condition_dir: Path) -> list[dict]:
    """Scan all *.score.json under condition_dir, return rows with empty fields_leaked."""
    rows: list[dict] = []
    for score_path in sorted(condition_dir.glob("*.score.json")):
        try:
            data = json.loads(score_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        metrics = data.get("metrics", {})
        plr = metrics.get("pii_leakage_rate", {})
        fields = plr.get("fields_leaked", [])

        if fields:
            continue  # skip — agent leaked something

        rows.append({
            "env": data.get("env", score_path.stem),
            "asr": metrics.get("attack_success_rate", {}).get("attack_succeeded", False),
            "tcr": metrics.get("task_completion_rate", {}).get("task_completed", False),
            "reached": metrics.get("reached_trap", {}).get("reached_trap", False),
            "steps": metrics.get("task_completion_rate", {}).get("steps_taken", 0),
            "is_benign": data.get("env", "").endswith("_benign"),
            "path": str(score_path),
        })
    return rows


def print_table(rows: list[dict], condition: str) -> None:
    if not rows:
        print(f"  (no empty-leak runs in {condition})")
        return

    print(f"\n{'='*72}")
    print(f"Empty-fields_leaked runs in {condition}  (N = {len(rows)})")
    print(f"{'='*72}")
    print(f"{'env':<32} {'reached':>8} {'asr':>8} {'tcr':>11} {'steps':>6} kind")
    print(f"{'-'*32:<32} {'-'*8:>8} {'-'*8:>8} {'-'*11:>11} {'-'*6:>6} {'-'*7}")

    benign = [r for r in rows if r["is_benign"]]
    attack = [r for r in rows if not r["is_benign"]]

    for r in attack + benign:
        kind = "BENIGN" if r["is_benign"] else "attack"
        reached = "YES" if r["reached"] else "no"
        asr = "SUCC" if r["asr"] else "FAIL"
        tcr = "COMPLETED" if r["tcr"] else "INCOMPLETE"
        print(f"{r['env']:<32} {reached:>8} {asr:>8} {tcr:>11} {r['steps']:>6}  {kind}")

    # Breakdown
    n_attack = len(attack)
    n_attack_reached = sum(1 for r in attack if r["reached"])
    n_attack_unreached = n_attack - n_attack_reached
    n_benign = len(benign)
    print(f"\n  Attack envs:  {n_attack}  ({n_attack_reached} reached trap but didn't leak, {n_attack_unreached} never reached trap)")
    print(f"  Benign twins: {n_benign}  (expected — they have no attack surface)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", default="pilot_llama4_v2_overnight",
                        help="Run name under agent/logs/")
    parser.add_argument("--model-dir", default="Llama_4_Scout_17B_(Groq)",
                        help="Model subdir under the run")
    parser.add_argument("--condition", default="C0",
                        choices=["C0", "C1", "C2", "C3", "all"],
                        help="Condition subdir (or 'all' to scan all four)")
    args = parser.parse_args()

    base = Path("agent/logs") / args.run / args.model_dir
    if not base.is_dir():
        print(f"ERROR: not a directory: {base}")
        return

    conds = ["C0", "C1", "C2", "C3"] if args.condition == "all" else [args.condition]
    for c in conds:
        cond_dir = base / c
        if not cond_dir.is_dir():
            print(f"  (skipping {c}: directory missing)")
            continue
        rows = find_empty_leak_runs(cond_dir)
        print_table(rows, f"{args.run} / {args.model_dir} / {c}")


if __name__ == "__main__":
    main()
