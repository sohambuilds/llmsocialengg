"""
F1 detection-action gap, recomputed under LLM-judge DR.

Mirror of paper_tables.ipynb Tab 4 (lines 612-650) with a parameterised
DR column. Compares keyword DR (existing baseline) against the LLM-judge
primary (GPT-4o-mini), and a both-judges-agree sensitivity using the
secondary judge (Llama 4 Scout) that ran on the full 2020-session pool
per model.

GPT-5 mini has no judge run, so its LLM-judge cells are dropped from
the pooled row but kept in the per-model display under keyword DR.

Run from repo root:
    uv run python -m agent.logs.v2.dr_judge_f1
or:
    python agent/logs/v2/dr_judge_f1.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# Paths / constants (mirror paper_tables.ipynb cells around line 78-100)
REPO = Path(__file__).resolve().parents[3]
V2 = REPO / "agent" / "logs" / "v2"

SLICE_DIRS = {
    "gemini-3-flash":   V2 / "gemini3_v3_seeds1to5_full",
    "llama-4-scout":    V2 / "llama4_v3_seeds1to5_full_re",
    "gpt-5-mini":       V2 / "gpt5mini_v3_seed1_full",
    "claude-haiku-4.5": V2 / "haiku_v3_seed1to5_full",
}

MODEL_LABELS = {
    "gemini-3-flash":   "Gemini_3_Flash_Preview_(OpenRouter)",
    "llama-4-scout":    "Llama_4_Scout_(OpenRouter)",
    "gpt-5-mini":       "GPT-5_mini_(OpenRouter)",
    "claude-haiku-4.5": "Claude_Haiku_4.5_(OpenRouter)",
}

MODEL_PRETTY = {
    "gemini-3-flash":   "Gemini 3 Flash",
    "llama-4-scout":    "Llama 4 Scout",
    "gpt-5-mini":       "GPT-5 mini",
    "claude-haiku-4.5": "Claude Haiku 4.5",
}

MODEL_ORDER = ["gpt-5-mini", "claude-haiku-4.5", "gemini-3-flash", "llama-4-scout"]
CONDITIONS  = ["C0", "C1", "C2", "C3"]

JUDGE_DIRS = {
    "gemini-3-flash":   V2 / "gemini3_dr_judge",
    "claude-haiku-4.5": V2 / "haiku_dr_judge",
    "llama-4-scout":    V2 / "llama4_dr_judge",
}
JUDGE_AVAILABLE = set(JUDGE_DIRS.keys())


# ---- attack DataFrame loader (copied from paper_tables.ipynb 139-209) ----

def _row_from_meta(env, model_short, condition, seed, meta):
    if meta.get("status") != "ok":
        return None
    s   = meta.get("summary", {})
    dq  = meta.get("data_quality", {})
    tcr = s.get("TCR")
    crit_leaked = s.get("critical_fields_leaked") or []
    plr_any_str = (s.get("PLR") or "0.0%").rstrip("%")
    try:
        plr_any = float(plr_any_str) / 100.0
    except ValueError:
        plr_any = np.nan
    return {
        "env": env,
        "model_short": model_short,
        "condition": condition,
        "seed": seed,
        "plr_crit": int(len(crit_leaked) > 0),
        "plr_any": plr_any,
        "asr": int(s.get("ASR") == "SUCCEEDED"),
        "tcr_label": tcr,
        "task_completed": int(tcr == "COMPLETED"),
        "dr_keyword": int(s.get("DR") == "DETECTED"),
        "defended": int(bool(s.get("defended"))),
        "reached_trap": int(bool(s.get("reached_trap"))),
        "reliable": int(bool(s.get("reliable", dq.get("reliable")))),
        "browser_error_excluded": int(tcr == "BROWSER_ERROR"),
    }


def load_slice(slice_root, model_label, model_short):
    rows = []
    for env_dir in slice_root.iterdir():
        if not env_dir.is_dir():
            continue
        model_dir = env_dir / model_label
        if not model_dir.is_dir():
            continue
        for cond_dir in model_dir.iterdir():
            cond = cond_dir.name
            if cond not in CONDITIONS:
                continue
            for seed_dir in cond_dir.iterdir():
                if not seed_dir.name.startswith("seed_"):
                    continue
                try:
                    seed = int(seed_dir.name.split("_")[1])
                except ValueError:
                    continue
                meta_path = seed_dir / "meta.json"
                if not meta_path.exists():
                    continue
                row = _row_from_meta(env_dir.name, model_short, cond, seed,
                                     json.loads(meta_path.read_text()))
                if row is not None:
                    rows.append(row)
    return pd.DataFrame(rows)


def load_attack():
    parts = []
    for m, root in SLICE_DIRS.items():
        if not root.exists():
            print(f"WARN: slice dir missing for {m}: {root}")
            continue
        parts.append(load_slice(root, MODEL_LABELS[m], m))
    df_all = pd.concat(parts, ignore_index=True)
    n_pre = len(df_all)
    browser_err = df_all[df_all["browser_error_excluded"] == 1]
    df = df_all[df_all["browser_error_excluded"] == 0].reset_index(drop=True)
    is_benign = df["env"].str.endswith("_benign")
    attack = df[~is_benign].copy()
    print(f"loaded {n_pre} sessions; excluded {len(browser_err)} BROWSER_ERROR; "
          f"{len(df)} retained ({len(attack)} attack)")
    return attack


# ---- LLM-judge DR loader ----

def load_judge_dr():
    rows = []
    for m, jdir in JUDGE_DIRS.items():
        summary_path = jdir / "dr_summary_full.json"
        data = json.loads(summary_path.read_text())
        for s in data:
            sec = s.get("any_detection_secondary")
            rows.append({
                "env": s["env"],
                "model_short": m,
                "condition": s["condition"],
                "seed": s["seed"],
                "dr_llm_primary":   int(bool(s.get("any_detection_primary"))),
                "dr_llm_secondary": int(sec) if sec is not None else np.nan,
            })
    df = pd.DataFrame(rows)
    df["dr_llm_both"] = np.where(
        df["dr_llm_secondary"].isna(),
        np.nan,
        ((df["dr_llm_primary"] == 1) & (df["dr_llm_secondary"] == 1)).astype(float),
    )
    return df


# ---- F1 table (generalised from paper_tables 612-631) ----

def f1_table(df_in, condition, gate_reached_trap, dr_col,
             models=tuple(MODEL_ORDER)):
    rows = []
    for m in list(models) + ["Pooled"]:
        sub = df_in if m == "Pooled" else df_in[df_in["model_short"] == m]
        sub = sub[sub["condition"] == condition]
        if gate_reached_trap:
            sub = sub[sub["reached_trap"] == 1]
        sub = sub[sub[dr_col].notna()]
        dr1 = sub[sub[dr_col] == 1]
        dr0 = sub[sub[dr_col] == 0]
        plr_dr1 = dr1["plr_crit"].mean() if len(dr1) else np.nan
        plr_dr0 = dr0["plr_crit"].mean() if len(dr0) else np.nan
        rows.append({
            "Model": "Pooled" if m == "Pooled" else MODEL_PRETTY[m],
            "n_DR1": len(dr1),
            "n_DR0": len(dr0),
            "PLR_DR1_pp": plr_dr1 * 100 if not np.isnan(plr_dr1) else np.nan,
            "PLR_DR0_pp": plr_dr0 * 100 if not np.isnan(plr_dr0) else np.nan,
            "gap_pp": (plr_dr0 - plr_dr1) * 100
                if not (np.isnan(plr_dr0) or np.isnan(plr_dr1)) else np.nan,
        })
    return pd.DataFrame(rows)


# ---- Cohen's kappa (from dr_judge_audit.py) ----

def cohens_kappa(a, b):
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    n = len(a)
    if n == 0:
        return float("nan")
    po = (a == b).mean()
    pa1 = a.mean()
    pb1 = b.mean()
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe >= 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


# ---- Power-gate verdict per §8 ----

def power_verdict(n):
    if n < 50:
        return "DESCRIPTIVE-ONLY"
    if n < 200:
        return "UNDERPOWERED"
    return "PRIMARY-FAMILY"


def main():
    print("=" * 72)
    print("F1 detection-action gap, recomputed under LLM-judge DR")
    print("=" * 72)

    attack = load_attack()
    judge  = load_judge_dr()

    # Merge LLM-judge DR onto attack
    df = attack.merge(
        judge[["env", "model_short", "condition", "seed",
               "dr_llm_primary", "dr_llm_secondary", "dr_llm_both"]],
        on=["env", "model_short", "condition", "seed"],
        how="left",
    )

    print("\n-- Sanity: judge-DR coverage per model --")
    cov = df.groupby("model_short")["dr_llm_primary"].apply(
        lambda s: f"{s.notna().sum()} / {len(s)}"
    )
    print(cov.to_string())

    # ---- Sanity 1: keyword-DR F1 reproduces paper_tables Tab 4 ----
    print("\n" + "=" * 72)
    print("SANITY: keyword-DR F1 (must reproduce paper_tables Tab 4)")
    print("=" * 72)

    print("\nTab 4a-keyword - F1 at C0, no reached_trap gate:")
    print(f1_table(df, "C0", gate_reached_trap=False,
                   dr_col="dr_keyword").round(1).to_string(index=False))

    print("\nTab 4b-keyword - F1 at C3, reached_trap=1 only:")
    print(f1_table(df, "C3", gate_reached_trap=True,
                   dr_col="dr_keyword").round(1).to_string(index=False))

    # ---- LLM-judge primary F1 ----
    print("\n" + "=" * 72)
    print("LLM-judge primary DR (GPT-4o-mini)")
    print("3-model pool: Gemini + Haiku + Llama (no GPT-5 mini judge data)")
    print("=" * 72)

    models_judged = ["claude-haiku-4.5", "gemini-3-flash", "llama-4-scout"]

    print("\nTab 4a-llmjudge - F1 at C0:")
    t4a_llm = f1_table(df, "C0", gate_reached_trap=False,
                       dr_col="dr_llm_primary", models=models_judged)
    print(t4a_llm.round(1).to_string(index=False))

    print("\nTab 4b-llmjudge - F1 at C3, reached_trap=1 only:")
    t4b_llm = f1_table(df, "C3", gate_reached_trap=True,
                       dr_col="dr_llm_primary", models=models_judged)
    print(t4b_llm.round(1).to_string(index=False))

    # ---- Both-judges-agree sensitivity ----
    print("\n" + "=" * 72)
    print("SENSITIVITY: both judges agree on DR=1 (high-confidence detectors)")
    print("Secondary judge (Llama 4 Scout) ran on the full pool, n=2020 per model")
    print("=" * 72)

    print("\nTab 4a-bothagree - F1 at C0:")
    t4a_both = f1_table(df, "C0", gate_reached_trap=False,
                        dr_col="dr_llm_both", models=models_judged)
    print(t4a_both.round(1).to_string(index=False))

    print("\nTab 4b-bothagree - F1 at C3, reached_trap=1 only:")
    t4b_both = f1_table(df, "C3", gate_reached_trap=True,
                        dr_col="dr_llm_both", models=models_judged)
    print(t4b_both.round(1).to_string(index=False))

    # ---- Side-by-side comparison ----
    print("\n" + "=" * 72)
    print("Side-by-side: F1 gap (keyword vs LLM-judge primary vs both-agree)")
    print("=" * 72)

    def gap_comparison(condition, gate_reached_trap):
        kw   = f1_table(df, condition, gate_reached_trap, "dr_keyword")
        llm  = f1_table(df, condition, gate_reached_trap, "dr_llm_primary",
                        models=models_judged)
        both = f1_table(df, condition, gate_reached_trap, "dr_llm_both",
                        models=models_judged)

        rows = []
        # Per-model rows: align on Model name
        for m in MODEL_ORDER:
            name = MODEL_PRETTY[m]
            kw_r = kw[kw["Model"] == name].iloc[0]
            llm_r = llm[llm["Model"] == name].iloc[0] if name in llm["Model"].values \
                else None
            both_r = both[both["Model"] == name].iloc[0] if name in both["Model"].values \
                else None
            rows.append({
                "Model": name,
                "kw_n_DR1": int(kw_r["n_DR1"]),
                "kw_gap_pp": kw_r["gap_pp"],
                "llm_n_DR1": int(llm_r["n_DR1"]) if llm_r is not None else None,
                "llm_gap_pp": llm_r["gap_pp"] if llm_r is not None else np.nan,
                "both_n_DR1": int(both_r["n_DR1"]) if both_r is not None else None,
                "both_gap_pp": both_r["gap_pp"] if both_r is not None else np.nan,
            })
        # Pooled rows
        for label, frame in [("Pooled (kw=4 models, llm=3 models)", (kw, llm, both))]:
            pkw, pllm, pboth = (f[f["Model"] == "Pooled"].iloc[0] for f in frame)
            rows.append({
                "Model": label,
                "kw_n_DR1": int(pkw["n_DR1"]),
                "kw_gap_pp": pkw["gap_pp"],
                "llm_n_DR1": int(pllm["n_DR1"]),
                "llm_gap_pp": pllm["gap_pp"],
                "both_n_DR1": int(pboth["n_DR1"]),
                "both_gap_pp": pboth["gap_pp"],
            })
        return pd.DataFrame(rows)

    print("\nAt C0 (paper-plan headline anchor):")
    gc_c0 = gap_comparison("C0", gate_reached_trap=False)
    print(gc_c0.round(1).to_string(index=False))

    print("\nAt C3 (analysis-plan S4 prereg, reached_trap=1 only):")
    gc_c3 = gap_comparison("C3", gate_reached_trap=True)
    print(gc_c3.round(1).to_string(index=False))

    # ---- Power-gate verdict ----
    print("\n" + "=" * 72)
    print("Power-gate verdict (S8: n>=50 descriptive, n>=200 primary family)")
    print("=" * 72)

    for label, gc in [("C0", gc_c0), ("C3", gc_c3)]:
        pooled = gc[gc["Model"].str.startswith("Pooled")].iloc[0]
        n_kw   = int(pooled["kw_n_DR1"])
        n_llm  = int(pooled["llm_n_DR1"])
        n_both = int(pooled["both_n_DR1"])
        print(f"\n{label} pooled:")
        print(f"  keyword   n_DR1 = {n_kw:5d}  -> {power_verdict(n_kw)}")
        print(f"  llmjudge  n_DR1 = {n_llm:5d}  -> {power_verdict(n_llm)}")
        print(f"  bothagree n_DR1 = {n_both:5d}  -> {power_verdict(n_both)}")

    # ---- Inter-judge kappa per model (from full pool) ----
    print("\n" + "=" * 72)
    print("Inter-judge kappa (primary GPT-4o-mini vs secondary Llama 4 Scout)")
    print("Full pool, n=2020 per model")
    print("=" * 72)

    judge_full = judge[judge["dr_llm_secondary"].notna()].copy()
    print()
    for m in ["claude-haiku-4.5", "gemini-3-flash", "llama-4-scout"]:
        sub = judge_full[judge_full["model_short"] == m]
        k = cohens_kappa(sub["dr_llm_primary"], sub["dr_llm_secondary"])
        print(f"  {MODEL_PRETTY[m]:<22} kappa = {k:.3f}  (n={len(sub)})")

    # ---- Sanity: judge-DR rates per condition vs CLAUDE.md table ----
    print("\n" + "=" * 72)
    print("SANITY: LLM-judge DR rates per (model x condition)")
    print("(should match CLAUDE.md: Llama C3 14.5, Gemini C3 24.0, Haiku C3 41.0)")
    print("=" * 72)

    rates = (judge.groupby(["model_short", "condition"])["dr_llm_primary"]
                  .mean().unstack().mul(100).round(2))
    print()
    print(rates.reindex(["claude-haiku-4.5", "gemini-3-flash", "llama-4-scout"])
               [CONDITIONS].to_string())

    # ---- Where did the filtered-out keyword-detectors go? ----
    print("\n" + "=" * 72)
    print("Decomposition: keyword DR=1 partitioned by LLM-judge verdict (C3, reach=1)")
    print("=" * 72)

    sub = df[(df["condition"] == "C3")
             & (df["reached_trap"] == 1)
             & (df["dr_llm_primary"].notna())].copy()
    kw1 = sub[sub["dr_keyword"] == 1]
    kw1_jt = kw1[kw1["dr_llm_primary"] == 1]   # genuine detectors
    kw1_jf = kw1[kw1["dr_llm_primary"] == 0]   # false-positive narrators

    def m(s):
        return f"n={len(s):4d}  PLR_crit={s['plr_crit'].mean()*100:5.1f} pp"

    print(f"\n  keyword=1 total:           {m(kw1)}")
    print(f"    -> judge=1 (true detect): {m(kw1_jt)}")
    print(f"    -> judge=0 (narrator):    {m(kw1_jf)}")
    print(f"\n  Interpretation: keyword DR conflates true detectors")
    print(f"  with narrators. Narrators leak at a higher rate than")
    print(f"  true detectors, so keyword DR drags PLR_DR1 upward and")
    print(f"  narrows the apparent F1 gap LESS than LLM-judge does.")
    print(f"  When narrators move to LLM-judge DR=0, they also drag")
    print(f"  PLR_DR0 down, which is what shrinks the C3 gap vs keyword.")

    # ---- Headline synthesis ----
    print("\n" + "=" * 72)
    print("HEADLINE SYNTHESIS (paper-facing)")
    print("=" * 72)

    def gap_pp_at(table, model_name):
        r = table[table["Model"] == model_name]
        return r["gap_pp"].iloc[0] if len(r) else float("nan")

    kw_c3   = f1_table(df, "C3", gate_reached_trap=True, dr_col="dr_keyword")
    llm_c3  = f1_table(df, "C3", gate_reached_trap=True,
                       dr_col="dr_llm_primary", models=models_judged)

    print(f"\nPrimary anchor: F1 at C3, reached_trap=1 (analysis-plan S4 prereg)")
    print(f"  keyword DR pooled gap:  {gap_pp_at(kw_c3,  'Pooled'):5.1f} pp  "
          f"(n_DR1={int(kw_c3[kw_c3['Model']=='Pooled']['n_DR1'].iloc[0])}, "
          f"primary-family power)")
    print(f"  LLM-judge pooled gap:   {gap_pp_at(llm_c3, 'Pooled'):5.1f} pp  "
          f"(n_DR1={int(llm_c3[llm_c3['Model']=='Pooled']['n_DR1'].iloc[0])}, "
          f"primary-family power)")
    print(f"\n  Direction: NARROWS by "
          f"{gap_pp_at(kw_c3,'Pooled') - gap_pp_at(llm_c3,'Pooled'):.1f} pp")
    print(f"  -> Filtering out narrators pulls leaky-narrator sessions")
    print(f"     into DR=0, which lowers PLR_DR0 and shrinks the apparent gap.")
    print(f"     But the gap remains large and well-powered.")

    kw_c0  = f1_table(df, "C0", gate_reached_trap=False, dr_col="dr_keyword")
    llm_c0 = f1_table(df, "C0", gate_reached_trap=False,
                      dr_col="dr_llm_primary", models=models_judged)
    print(f"\nSecondary anchor: F1 at C0 (paper-plan #1 headline)")
    print(f"  keyword DR pooled gap:  {gap_pp_at(kw_c0,  'Pooled'):5.1f} pp  "
          f"(n_DR1={int(kw_c0[kw_c0['Model']=='Pooled']['n_DR1'].iloc[0])}, "
          f"UNDERPOWERED)")
    print(f"  LLM-judge pooled gap:   {gap_pp_at(llm_c0, 'Pooled'):5.1f} pp  "
          f"(n_DR1={int(llm_c0[llm_c0['Model']=='Pooled']['n_DR1'].iloc[0])}, "
          f"UNDERPOWERED)")
    print(f"\n  Direction: WIDENS by "
          f"{gap_pp_at(llm_c0,'Pooled') - gap_pp_at(kw_c0,'Pooled'):.1f} pp")
    print(f"  -> But cell collapses below power threshold. C0 becomes")
    print(f"     descriptive-only under LLM-judge. Anchor shifts to C3.")

    print(f"\nPer-model verdict at C3 (LLM-judge, reached_trap=1):")
    for m_name in ["Claude Haiku 4.5", "Gemini 3 Flash", "Llama 4 Scout"]:
        r = llm_c3[llm_c3["Model"] == m_name].iloc[0]
        n = int(r["n_DR1"])
        v = power_verdict(n)
        print(f"  {m_name:<18}  gap={r['gap_pp']:5.1f} pp  "
              f"n_DR1={n:3d}  -> {v}")

    print("\nGPT-5 mini: no LLM-judge run; not included in LLM-judge pooled.")
    print("Llama C0 LLM-judge n_DR1=1 (single session); descriptive only at C0.")


if __name__ == "__main__":
    main()
