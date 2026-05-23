"""
DR Judge audit: precision/recall vs human labels + per-condition kappa matrix.

Takes:
  1. A judge results JSON (from dr_judge_run.py)
  2. A human labels JSON (one label per session)

Computes:
  - Precision  = TP / (TP + FP)  [judge said DETECTED; human says YES/NO]
  - Recall     = TP / (TP + FN)  [human said DETECTED; judge says YES/NO]
  - F1
  - Per-condition kappa table (primary vs secondary)
  - Keyword-DR vs LLM-judge DR comparison table (per condition)

Human labels JSON format (write this after human review):
  [
    {
      "env": "gov_portal",
      "condition": "C0",
      "seed": 1,
      "human_detected": true,        // true = human confirms detection
      "notes": "agent said 'typosquat' at step 3"
    },
    ...
  ]

Output:
  Printed report + optional --out-csv for paper tables.

Usage:
  python scripts/dr_judge_audit.py \\
    --judge-results agent/logs/v2/llama4_dr_judge/dr_results_c0.json \\
    --human-labels  agent/logs/v2/llama4_dr_judge/human_labels_c0.json \\
    --score-dir     agent/logs/v2/llama4_v3_seeds1to5_full_re

  # Kappa matrix only (no human labels needed):
  python scripts/dr_judge_audit.py \\
    --judge-results agent/logs/v2/llama4_dr_judge/dr_results_c0.json \\
    --kappa-only

  # Keyword vs LLM-judge comparison:
  python scripts/dr_judge_audit.py \\
    --judge-results agent/logs/v2/llama4_dr_judge/dr_results_full.json \\
    --score-dir agent/logs/v2/llama4_v3_seeds1to5_full_re \\
    --compare-keyword
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


# ── Precision / recall ─────────────────────────────────────────────────────────

def compute_precision_recall(
    judge_results: dict,
    human_labels: list[dict],
) -> dict:
    """
    Match human labels to judge results by (env, condition, seed).
    Returns TP, FP, FN, TN, precision, recall, F1.
    """
    # Index human labels
    human_idx: dict[tuple, bool] = {
        (h["env"], h["condition"], h["seed"]): h["human_detected"]
        for h in human_labels
    }

    tp = fp = fn = tn = 0

    for sess in judge_results.get("sessions", []):
        key = (sess["env"], sess["condition"], sess["seed"])
        if key not in human_idx:
            continue  # not labeled

        judge_pos = sess.get("any_detection", False)
        human_pos = human_idx[key]

        if judge_pos and human_pos:
            tp += 1
        elif judge_pos and not human_pos:
            fp += 1
        elif not judge_pos and human_pos:
            fn += 1
        else:
            tn += 1

    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall    = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    f1        = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else float("nan")

    return {
        "n_labeled": n,
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    }


# ── Per-condition kappa ────────────────────────────────────────────────────────

def compute_kappa_from_results(primary_labels: list[bool], secondary_labels: list[bool]) -> float:
    """Cohen's kappa between two binary label lists."""
    n = len(primary_labels)
    if n == 0:
        return float("nan")

    po = sum(p == s for p, s in zip(primary_labels, secondary_labels)) / n

    p_pos = sum(primary_labels) / n
    s_pos = sum(secondary_labels) / n
    pe = p_pos * s_pos + (1 - p_pos) * (1 - s_pos)

    kappa = (po - pe) / (1 - pe) if abs(1 - pe) > 1e-9 else 1.0
    return round(kappa, 4)


def per_condition_kappa(judge_results: dict) -> dict[str, float]:
    """Compute primary-vs-secondary kappa broken down by condition."""
    by_condition: dict[str, tuple[list, list]] = {}

    for sess in judge_results.get("sessions", []):
        cond = sess.get("condition", "?")
        primary = sess.get("primary", [])
        secondary = sess.get("secondary", [])

        if not secondary:
            continue

        # Align on step index
        sec_by_step = {r["step"]: r["detected"] for r in secondary}
        for r in primary:
            step = r["step"]
            if step not in sec_by_step:
                continue
            pp, ss = by_condition.setdefault(cond, ([], []))
            pp.append(r["detected"])
            ss.append(sec_by_step[step])

    result = {}
    for cond, (pp, ss) in sorted(by_condition.items()):
        result[cond] = compute_kappa_from_results(pp, ss)
    return result


# ── Keyword-DR vs LLM-judge comparison ────────────────────────────────────────

def keyword_vs_llm_comparison(
    judge_results: dict,
    score_dir: Path,
) -> list[dict]:
    """
    For each judged session, look up the keyword DR from the sibling meta.json
    and compare with LLM-judge any_detection.

    Returns a list of rows: env, condition, seed, keyword_dr, llm_dr, agreement.
    """
    rows = []
    for sess in judge_results.get("sessions", []):
        env  = sess.get("env")
        cond = sess.get("condition")
        seed = sess.get("seed")

        # Discover meta.json for this cell
        pattern = f"{env}/*/C{cond[-1] if cond else '?'}/seed_{seed}/meta.json"
        meta_files = list(score_dir.glob(f"{env}/**/{cond}/seed_{seed}/meta.json"))

        keyword_dr = None
        if meta_files:
            with open(meta_files[0]) as f:
                meta = json.load(f)
            keyword_dr = meta.get("summary", {}).get("DR")

        llm_dr = "DETECTED" if sess.get("any_detection") else "UNDETECTED"
        keyword_dr_bool = keyword_dr == "DETECTED" if keyword_dr else None
        llm_dr_bool = sess.get("any_detection", False)

        agreement = None
        if keyword_dr_bool is not None:
            agreement = keyword_dr_bool == llm_dr_bool

        rows.append({
            "env": env,
            "condition": cond,
            "seed": seed,
            "keyword_dr": keyword_dr,
            "llm_dr": llm_dr,
            "agreement": agreement,
        })

    return rows


def _format_comparison_summary(rows: list[dict]) -> str:
    by_condition: dict[str, dict] = {}
    for r in rows:
        cond = r["condition"] or "?"
        cell = by_condition.setdefault(cond, {"agree": 0, "disagree": 0, "keyword_only": 0, "llm_only": 0, "both": 0, "neither": 0, "n": 0})
        cell["n"] += 1
        kw = r["keyword_dr"] == "DETECTED" if r["keyword_dr"] else None
        ll = r["llm_dr"] == "DETECTED"
        if kw is None:
            continue
        if kw and ll:
            cell["both"] += 1
        elif not kw and not ll:
            cell["neither"] += 1
        elif kw and not ll:
            cell["keyword_only"] += 1
        elif not kw and ll:
            cell["llm_only"] += 1
        cell["agree"] += int(kw == ll)
        cell["disagree"] += int(kw != ll)

    lines = ["Keyword-DR vs LLM-judge comparison:", f"{'Cond':>5}  {'n':>5}  {'agree%':>7}  {'both%':>6}  {'neither%':>8}  {'kw_only%':>9}  {'llm_only%':>10}"]
    for cond in sorted(by_condition):
        c = by_condition[cond]
        n = c["n"] or 1
        lines.append(
            f"{cond:>5}  {c['n']:>5}  {c['agree']/n*100:>6.1f}%"
            f"  {c['both']/n*100:>5.1f}%  {c['neither']/n*100:>7.1f}%"
            f"  {c['keyword_only']/n*100:>8.1f}%  {c['llm_only']/n*100:>9.1f}%"
        )
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Audit DR judge precision/recall and kappa")
    parser.add_argument("--judge-results", required=True, type=Path,
                        help="Path to dr_results_<pool>.json from dr_judge_run.py")
    parser.add_argument("--human-labels", type=Path,
                        help="Path to human labels JSON (optional; enables precision/recall)")
    parser.add_argument("--score-dir", type=Path,
                        help="Run directory root for keyword-DR lookup (optional)")
    parser.add_argument("--kappa-only", action="store_true",
                        help="Only compute per-condition kappa (skip precision/recall)")
    parser.add_argument("--compare-keyword", action="store_true",
                        help="Print keyword-DR vs LLM-judge comparison table")
    parser.add_argument("--out-json", type=Path, help="Save audit results to JSON")
    args = parser.parse_args()

    judge_results = _load_json(args.judge_results)
    if not isinstance(judge_results, dict):
        print("ERROR: judge-results must be a JSON object (dict)")
        return

    print(f"\nDR Judge Audit: {args.judge_results.name}")
    print(f"  Sessions: {judge_results.get('num_sessions', '?')}")
    print(f"  Primary judge: {judge_results.get('primary_judge', '?')}")
    print(f"  Secondary judge: {judge_results.get('secondary_judge', '?')}")
    print(f"  Global kappa: {judge_results.get('inter_judge_kappa', 'N/A')}")

    output: dict = {}

    # -- Per-condition kappa ---
    kappa_table = per_condition_kappa(judge_results)
    if kappa_table:
        print("\nPer-condition kappa (primary vs secondary):")
        for cond, k in sorted(kappa_table.items()):
            print(f"  {cond}: {k}")
        output["per_condition_kappa"] = kappa_table

    if args.kappa_only:
        return

    # -- Precision / recall (requires human labels) ---
    if args.human_labels:
        human_labels = _load_json(args.human_labels)
        if not isinstance(human_labels, list):
            print("ERROR: human-labels must be a JSON array")
            return
        pr = compute_precision_recall(judge_results, human_labels)
        print(f"\nPrecision / Recall (vs {len(human_labels)} human labels):")
        print(f"  n labeled : {pr['n_labeled']}")
        print(f"  TP={pr['TP']}  FP={pr['FP']}  FN={pr['FN']}  TN={pr['TN']}")
        print(f"  Precision : {pr['precision']:.4f}")
        print(f"  Recall    : {pr['recall']:.4f}")
        print(f"  F1        : {pr['f1']:.4f}")
        output["precision_recall"] = pr

    # -- Keyword vs LLM-judge ---
    if args.compare_keyword and args.score_dir:
        rows = keyword_vs_llm_comparison(judge_results, args.score_dir)
        print(f"\n{_format_comparison_summary(rows)}")
        output["keyword_vs_llm_rows"] = rows

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n[audit] Saved -> {args.out_json}")


if __name__ == "__main__":
    main()
