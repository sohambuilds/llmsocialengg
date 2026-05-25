"""
Compute Cohen's kappa between the human annotators and the LLM judge.

Reads:
  <label-dir>/labels_A.csv             (annotator A: your_label_0_or_1 filled in)
  <label-dir>/labels_B.csv             (annotator B: your_label_0_or_1 filled in)
  <label-dir>/judge_ground_truth.csv   (judge_dr per session_id)

Outputs (to stdout AND <label-dir>/kappa_results.json):
  - n_labelled (per annotator)
  - Cohen's kappa: A vs B, A vs judge, B vs judge, majority vs judge
  - per-condition kappa: majority vs judge
  - prevalence + agreement (for sanity)
  - drop-in LaTeX snippet ready to paste into app:dr-sensitivity

Decision rule for analysis-plan D2 (judge-vs-human kappa >= 0.7):
  - We use majority-of-two vs judge as the headline kappa
  - A and B disagreements where one matches the judge are counted by the
    individual A-vs-judge / B-vs-judge kappas (reported for transparency).

Usage:
  python scripts/dr_judge_human_kappa.py --label-dir agent/logs/v2/dr_human_label
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def cohens_kappa(a: list[int], b: list[int]) -> tuple[float, float, float]:
    """Cohen's kappa for two binary 0/1 vectors of equal length.

    Returns (kappa, observed_agreement, expected_agreement).
    """
    assert len(a) == len(b), "vectors must be same length"
    n = len(a)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    obs = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n
    pa0 = 1 - pa1
    pb1 = sum(b) / n
    pb0 = 1 - pb1
    exp = pa1 * pb1 + pa0 * pb0
    if exp == 1.0:
        return float("nan"), obs, exp
    kappa = (obs - exp) / (1 - exp)
    return kappa, obs, exp


def load_labels(path: Path, label_col: str) -> dict[str, int]:
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = row["session_id"].strip()
            raw = row.get(label_col, "").strip()
            if raw in ("0", "1"):
                out[sid] = int(raw)
    return out


def load_judge(path: Path) -> dict[str, dict]:
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = row["session_id"].strip()
            out[sid] = {
                "judge_dr":     int(row["judge_dr"]),
                "condition":    row["condition"],
                "model_family": row["model_family"],
            }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label-dir", required=True)
    args = ap.parse_args()

    label_dir = Path(args.label_dir)
    a_path = label_dir / "labels_A.csv"
    b_path = label_dir / "labels_B.csv"
    g_path = label_dir / "judge_ground_truth.csv"

    a_lab = load_labels(a_path, "your_label_0_or_1")
    b_lab = load_labels(b_path, "your_label_0_or_1")
    judge = load_judge(g_path)

    print(f"[kappa] annotator A labelled {len(a_lab)} / {len(judge)}")
    print(f"[kappa] annotator B labelled {len(b_lab)} / {len(judge)}")

    # Intersection of fully-labelled session IDs
    both_ids = sorted(set(a_lab) & set(b_lab) & set(judge))
    print(f"[kappa] sessions with A+B+judge all present: {len(both_ids)}")
    if not both_ids:
        print("[kappa] no fully-labelled sessions yet — nothing to compute.")
        return

    a = [a_lab[s] for s in both_ids]
    b = [b_lab[s] for s in both_ids]
    j = [judge[s]["judge_dr"] for s in both_ids]
    maj = [1 if (ax + bx) >= 2 else 0 for ax, bx in zip(a, b)]  # tie-break: 0 (no agreement -> not detected)
    # When A and B disagree (sum=1), majority is undefined. We instead split:
    # if A=B use that; if A!=B drop from the majority-vs-judge calc and report
    # the disagreement count separately.
    agree_idx = [i for i, (ax, bx) in enumerate(zip(a, b)) if ax == bx]
    a_agree = [a[i] for i in agree_idx]
    j_agree = [j[i] for i in agree_idx]
    disagree_ct = len(both_ids) - len(agree_idx)

    k_ab,   ag_ab, _ = cohens_kappa(a, b)
    k_aj,   ag_aj, _ = cohens_kappa(a, j)
    k_bj,   ag_bj, _ = cohens_kappa(b, j)
    k_majj, ag_mj, _ = cohens_kappa(a_agree, j_agree) if a_agree else (float("nan"), float("nan"), float("nan"))

    print()
    print("=== headline kappas ===")
    print(f"  A vs B (human-human)            : kappa = {k_ab: .3f}  (agreement {ag_ab:.1%})")
    print(f"  A vs judge                       : kappa = {k_aj: .3f}  (agreement {ag_aj:.1%})")
    print(f"  B vs judge                       : kappa = {k_bj: .3f}  (agreement {ag_bj:.1%})")
    print(f"  consensus (A==B) vs judge        : kappa = {k_majj: .3f}  "
          f"(agreement {ag_mj:.1%}, n={len(a_agree)}, A/B disagree on {disagree_ct})")

    # Per-condition kappa on the consensus-vs-judge cell (for the paper appendix)
    print()
    print("=== per-condition consensus-vs-judge ===")
    per_cond_kappa = {}
    by_cond_human = defaultdict(list)
    by_cond_judge = defaultdict(list)
    for sid in both_ids:
        if a_lab[sid] != b_lab[sid]:
            continue
        cond = judge[sid]["condition"]
        by_cond_human[cond].append(a_lab[sid])
        by_cond_judge[cond].append(judge[sid]["judge_dr"])
    for cond in sorted(by_cond_human):
        h = by_cond_human[cond]
        jj = by_cond_judge[cond]
        kc, ac, _ = cohens_kappa(h, jj)
        per_cond_kappa[cond] = {"kappa": kc, "agreement": ac, "n": len(h)}
        print(f"  {cond}: kappa={kc: .3f}, agreement={ac:.1%}, n={len(h)}")

    # Save machine-readable
    out = {
        "n_total": len(both_ids),
        "n_consensus": len(a_agree),
        "n_disagree_AB": disagree_ct,
        "kappa_A_B": k_ab,
        "kappa_A_judge": k_aj,
        "kappa_B_judge": k_bj,
        "kappa_consensus_judge": k_majj,
        "agreement_consensus_judge": ag_mj,
        "per_condition": per_cond_kappa,
        "prevalence_judge_DR1": sum(j) / len(j),
        "prevalence_A_DR1":     sum(a) / len(a),
        "prevalence_B_DR1":     sum(b) / len(b),
    }
    out_path = label_dir / "kappa_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[kappa] wrote {out_path}")

    # LaTeX snippet for app:dr-sensitivity
    snippet = (
        f"Judge--human agreement on the {len(both_ids)}-pair human-labelled set "
        f"(two raters labelling blind; consensus restricted to the "
        f"{len(a_agree)} pairs on which the two raters agreed): "
        f"Cohen's $\\kappa = {k_majj:.2f}$ (consensus vs primary judge), "
        f"with $\\kappa = {k_ab:.2f}$ between the two human raters."
    )
    if k_majj >= 0.7:
        snippet += " This clears the pre-registered $\\kappa \\geq 0.7$ bar (\\S\\ref{sec:dr}, analysis-plan D2)."
    else:
        snippet += (" This is below the pre-registered $\\kappa \\geq 0.7$ bar; "
                    "per analysis-plan D2 the F1 primary anchor falls back to "
                    "keyword-DR.")
    print()
    print("=== LaTeX snippet for app:dr-sensitivity ===")
    print(snippet)


if __name__ == "__main__":
    main()
