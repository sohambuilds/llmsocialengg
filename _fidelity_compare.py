"""
Statistical comparison of synth-vs-real fidelity ratings.

Reads:
  fidelity/sample_key.json  - which sample_id is synthetic vs real
  fidelity/ratings.csv      - filled-in scores

Writes:
  fidelity/comparison.json  - means, SDs, Mann-Whitney U test, paste-ready
                              §3 paragraph

Run after rating is complete:
  python _fidelity_compare.py
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path


KEY = Path("fidelity/sample_key.json")
RATINGS = Path("fidelity/ratings.csv")
OUT = Path("fidelity/comparison.json")


def mann_whitney_u(a: list[float], b: list[float]) -> tuple[float, float]:
    """Two-sided Mann-Whitney U with normal approximation.

    Returns (U, two-sided p). Tiny implementation — fine for n_a + n_b ~ 15.
    """
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
    combined = [(v, 0) for v in a] + [(v, 1) for v in b]
    combined.sort(key=lambda t: t[0])
    # Average rank assignment for ties
    ranks: dict[int, float] = {}
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = rank
        i = j + 1
    r1 = sum(ranks[k] for k, (_, g) in enumerate(combined) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    # Normal approximation (ok for nesque samples)
    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    if sigma == 0:
        return u, 1.0
    z = (u - mu) / sigma
    # Two-sided p via erfc
    p = math.erfc(abs(z) / math.sqrt(2))
    return u, p


def mean_sd(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return float("nan"), float("nan")
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, 0.0
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return m, math.sqrt(v)


def main() -> None:
    with KEY.open(encoding="utf-8") as f:
        key = json.load(f)
    kind_by_id = {s["sample_id"]: s["kind"] for s in key["samples"]}

    visual_synth: list[float] = []
    visual_real: list[float] = []
    copy_synth: list[float] = []
    copy_real: list[float] = []
    missing: list[str] = []

    with RATINGS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row["sample_id"]
            v = row["visual_1to5"].strip()
            c = row["copy_1to5"].strip()
            if not v or not c:
                missing.append(sid)
                continue
            vv, cc = float(v), float(c)
            kind = kind_by_id.get(sid)
            if kind == "synthetic":
                visual_synth.append(vv)
                copy_synth.append(cc)
            elif kind == "real":
                visual_real.append(vv)
                copy_real.append(cc)

    if missing:
        print(f"WARNING: {len(missing)} unrated rows skipped: {missing}")

    vm_s, vs_s = mean_sd(visual_synth)
    vm_r, vs_r = mean_sd(visual_real)
    cm_s, cs_s = mean_sd(copy_synth)
    cm_r, cs_r = mean_sd(copy_real)
    u_v, p_v = mann_whitney_u(visual_synth, visual_real)
    u_c, p_c = mann_whitney_u(copy_synth, copy_real)

    summary = {
        "n_synth": len(visual_synth),
        "n_real": len(visual_real),
        "visual": {
            "synth_mean": round(vm_s, 2), "synth_sd": round(vs_s, 2),
            "real_mean":  round(vm_r, 2), "real_sd":  round(vs_r, 2),
            "mwu_U": round(u_v, 2), "mwu_p_two_sided": round(p_v, 4),
        },
        "copy": {
            "synth_mean": round(cm_s, 2), "synth_sd": round(cs_s, 2),
            "real_mean":  round(cm_r, 2), "real_sd":  round(cs_r, 2),
            "mwu_U": round(u_c, 2), "mwu_p_two_sided": round(p_c, 4),
        },
    }

    # Paste-ready §3 paragraph
    paragraph = (
        "**Fidelity validation.** To verify the visual and linguistic "
        "fidelity of our synthetic attack environments, one author "
        "scored 10 stratified attack envs alongside 5 real-phish "
        "references drawn from PhishTank and the Wayback Machine on a "
        "1–5 scale for both visual believability and copy quality. The "
        "sample order was randomized; rating was not blinded at "
        "view-time (the address bar reveals localhost vs archived "
        "URLs on inspection) but the rubric was applied uniformly "
        "across samples. Synthetic envs scored "
        f"{summary['visual']['synth_mean']:.2f}±{summary['visual']['synth_sd']:.2f} "
        f"on visual believability vs {summary['visual']['real_mean']:.2f}±{summary['visual']['real_sd']:.2f} "
        f"for real-phish samples (Mann-Whitney U={summary['visual']['mwu_U']:.1f}, "
        f"p={summary['visual']['mwu_p_two_sided']:.3f}), and "
        f"{summary['copy']['synth_mean']:.2f}±{summary['copy']['synth_sd']:.2f} "
        f"vs {summary['copy']['real_mean']:.2f}±{summary['copy']['real_sd']:.2f} "
        f"on copy quality (U={summary['copy']['mwu_U']:.1f}, "
        f"p={summary['copy']['mwu_p_two_sided']:.3f}). "
        "We treat this rating as a sanity check, not a definitive "
        "fidelity claim; a larger blinded study with multiple raters "
        "is left to future work."
    )
    summary["paste_ready_paragraph"] = paragraph

    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"\n[saved] {OUT}")


if __name__ == "__main__":
    main()
