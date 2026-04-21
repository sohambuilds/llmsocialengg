"""
Comprehensive analysis of Scammer4U benchmark aggregate results.
Reads all aggregate_results.json files from agent/logs/{gemini,gpt-oss,llama}-{1,2,3}/
and produces detailed statistics for the report.

Run: python analyze_results.py
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import statistics

LOGS_DIR = Path(__file__).parent / "agent" / "logs"

# Map of model short names
MODEL_SHORT = {
    "gemini-3-flash-preview": "Gemini 3 Flash",
    "openai/gpt-oss-120b": "GPT-OSS 120B",
    "meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout",
}

ENV_TIERS = {
    "cluttered_downloads": 1,
    "coc_gems": 1,
    "github_phish": 1,
    "virus_scanner": 1,
    "file_converter": 1,
    "quiz_scam": 1,
    "job_portal": 2,
    "gov_portal": 2,
    "ecommerce": 2,
    "news": 2,
    "marketplace": 2,
    "summarizer": 2,
    "freelance": 3,
    "support_chat": 3,
    "saas_onboard": 3,
    "crypto_platform": 3,
}

ENV_NAMES_PRETTY = {
    "cluttered_downloads": "Cluttered Downloads",
    "coc_gems": "CoC Gems Scam",
    "github_phish": "GitHub Phishing",
    "virus_scanner": "Virus Scanner",
    "file_converter": "File Converter",
    "quiz_scam": "Quiz Scam",
    "job_portal": "Job Portal",
    "gov_portal": "Gov Portal",
    "ecommerce": "E-commerce",
    "news": "News Site",
    "marketplace": "Marketplace",
    "summarizer": "Summarizer",
    "freelance": "Freelance Platform",
    "support_chat": "Support Chat",
    "saas_onboard": "SaaS Onboard",
    "crypto_platform": "Crypto Platform",
}


def load_all_results():
    """Load all aggregate_results.json files and return a flat list of entries."""
    all_entries = []
    run_dirs = [
        "gemini-1", "gemini-2", "gemini-3",
        "gpt-oss-1", "gpt-oss-2", "gpt-oss-3",
        "llama-1", "llama-2", "llama-3",
    ]
    
    loaded_files = []
    for run_dir in run_dirs:
        fpath = LOGS_DIR / run_dir / "aggregate_results.json"
        if fpath.exists():
            with open(fpath, "r") as f:
                data = json.load(f)
            loaded_files.append((run_dir, len(data)))
            for entry in data:
                if "env" not in entry:
                    continue  # skip malformed entries
                entry["_source_dir"] = run_dir
                all_entries.append(entry)
    
    return all_entries, loaded_files


def get_model_key(entry):
    """Normalize model name to a short key."""
    model = entry.get("model", "unknown")
    for full, short in MODEL_SHORT.items():
        if full in model:
            return short
    return model


def analyze_per_model_per_env(entries):
    """Group entries by (model, env) and compute aggregates across runs."""
    grouped = defaultdict(list)
    for e in entries:
        model = get_model_key(e)
        env = e["env"]
        grouped[(model, env)].append(e)
    return grouped


def compute_aggregates(entries_list):
    """Compute aggregate stats from multiple runs of the same (model, env)."""
    plrs = []
    asrs = []  # 1 if succeeded, 0 if failed
    tcrs = []  # 1 if completed, 0 if not
    drs = []   # 1 if detected, 0 if not
    steps_list = []
    total_fields_leaked = []
    critical_fields_leaked = []
    reliable_count = 0
    
    for e in entries_list:
        metrics = e.get("metrics", {})
        summary = e.get("summary", {})
        dq = e.get("data_quality", {})
        
        if dq.get("reliable", True):
            reliable_count += 1
        
        plr_data = metrics.get("pii_leakage_rate", {})
        plrs.append(plr_data.get("plr", 0.0))
        
        asr_data = metrics.get("attack_success_rate", {})
        asrs.append(1 if asr_data.get("attack_succeeded", False) else 0)
        total_fields_leaked.append(asr_data.get("total_fields_to_attacker", 0))
        critical_fields_leaked.append(asr_data.get("critical_fields_to_attacker", 0))
        
        tcr_data = metrics.get("task_completion_rate", {})
        tcrs.append(1 if tcr_data.get("task_completed", False) else 0)
        steps_list.append(tcr_data.get("steps_taken", 0))
        
        dr_data = metrics.get("detection_rate", {})
        drs.append(1 if dr_data.get("any_detection", False) else 0)
    
    n = len(entries_list)
    return {
        "n_runs": n,
        "n_reliable": reliable_count,
        "plr_mean": statistics.mean(plrs) if plrs else 0,
        "plr_values": plrs,
        "asr_rate": sum(asrs) / n if n > 0 else 0,
        "asr_values": asrs,
        "tcr_rate": sum(tcrs) / n if n > 0 else 0,
        "tcr_values": tcrs,
        "dr_rate": sum(drs) / n if n > 0 else 0,
        "dr_values": drs,
        "steps_mean": statistics.mean(steps_list) if steps_list else 0,
        "total_fields_mean": statistics.mean(total_fields_leaked) if total_fields_leaked else 0,
        "critical_fields_mean": statistics.mean(critical_fields_leaked) if critical_fields_leaked else 0,
    }


def collect_all_leaked_fields(entries_list):
    """Collect all unique leaked field names across entries."""
    fields = set()
    for e in entries_list:
        plr = e.get("metrics", {}).get("pii_leakage_rate", {})
        for f in plr.get("fields_leaked", []):
            fields.add(f)
    return fields


def analyze_sensitivity_breakdown(entries_list):
    """Break down leaked fields by sensitivity level."""
    sensitivity_counts = defaultdict(set)
    for e in entries_list:
        plr = e.get("metrics", {}).get("pii_leakage_rate", {})
        for detail in plr.get("details", []):
            field = detail.get("field", "")
            sens = detail.get("sensitivity", "unknown")
            sensitivity_counts[sens].add(field)
    return {k: list(v) for k, v in sensitivity_counts.items()}


def main():
    entries, loaded_files = load_all_results()
    
    print("=" * 80)
    print("SCAMMER4U BENCHMARK - COMPREHENSIVE RESULTS ANALYSIS")
    print("=" * 80)
    
    # ── Data Loading Summary ──
    print("\n## DATA LOADING SUMMARY")
    print(f"Total entries loaded: {len(entries)}")
    for dirname, count in loaded_files:
        print(f"  {dirname}: {count} entries")
    
    # ── Unique models and envs ──
    models = sorted(set(get_model_key(e) for e in entries))
    envs = sorted(set(e["env"] for e in entries))
    print(f"\nModels: {models}")
    print(f"Environments: {envs}")
    print(f"Total unique (model, env) combinations: {len(set((get_model_key(e), e['env']) for e in entries))}")
    
    grouped = analyze_per_model_per_env(entries)
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 1: Per-Environment Results (averaged across runs)
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 1: PER-ENVIRONMENT RESULTS (averaged across runs)")
    print("=" * 80)
    
    # Sort envs by tier, then name
    sorted_envs = sorted(envs, key=lambda e: (ENV_TIERS.get(e, 99), e))
    
    header = f"{'Environment':<22} {'Tier':>4}"
    for m in models:
        header += f" | {'PLR':>5} {'ASR':>5} {'TCR':>5} {'DR':>5} {'N':>3}"
    print(header)
    print("-" * len(header))
    
    for env in sorted_envs:
        tier = ENV_TIERS.get(env, "?")
        row = f"{env:<22} {tier:>4}"
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                plr_str = f"{agg['plr_mean']:.0%}"
                asr_str = f"{agg['asr_rate']:.0%}"
                tcr_str = f"{agg['tcr_rate']:.0%}"
                dr_str = f"{agg['dr_rate']:.0%}"
                n_str = f"{agg['n_runs']}"
                row += f" | {plr_str:>5} {asr_str:>5} {tcr_str:>5} {dr_str:>5} {n_str:>3}"
            else:
                row += f" | {'--':>5} {'--':>5} {'--':>5} {'--':>5} {'--':>3}"
        print(row)
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 2: Model-Level Aggregate Metrics
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 2: MODEL-LEVEL AGGREGATE METRICS (across all envs)")
    print("=" * 80)
    
    for m in models:
        model_entries = [e for e in entries if get_model_key(e) == m]
        model_envs = set(e["env"] for e in model_entries)
        
        # Per-env averages first, then average across envs
        env_plrs = []
        env_asrs = []
        env_tcrs = []
        env_drs = []
        env_steps = []
        
        for env in model_envs:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                env_plrs.append(agg["plr_mean"])
                env_asrs.append(agg["asr_rate"])
                env_tcrs.append(agg["tcr_rate"])
                env_drs.append(agg["dr_rate"])
                env_steps.append(agg["steps_mean"])
        
        print(f"\n  {m}")
        print(f"    Environments evaluated: {len(model_envs)}")
        print(f"    Total runs: {len(model_entries)}")
        print(f"    Avg PLR (across envs): {statistics.mean(env_plrs):.1%}" if env_plrs else "    Avg PLR: N/A")
        print(f"    Avg ASR (across envs): {statistics.mean(env_asrs):.1%}" if env_asrs else "    Avg ASR: N/A")
        print(f"    Avg TCR (across envs): {statistics.mean(env_tcrs):.1%}" if env_tcrs else "    Avg TCR: N/A")
        print(f"    Avg DR  (across envs): {statistics.mean(env_drs):.1%}" if env_drs else "    Avg DR:  N/A")
        print(f"    Avg Steps: {statistics.mean(env_steps):.1f}" if env_steps else "    Avg Steps: N/A")
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 3: Per-Tier Breakdown
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 3: PER-TIER BREAKDOWN (averaged per model)")
    print("=" * 80)
    
    header = f"{'Model':<20} {'Tier':>5} {'PLR':>6} {'ASR':>6} {'TCR':>6} {'DR':>6} {'#Envs':>6} {'#Runs':>6}"
    print(header)
    print("-" * len(header))
    
    for m in models:
        for tier in [1, 2, 3]:
            tier_envs = [env for env in envs if ENV_TIERS.get(env, 99) == tier]
            tier_plrs = []
            tier_asrs = []
            tier_tcrs = []
            tier_drs = []
            n_runs = 0
            n_envs = 0
            
            for env in tier_envs:
                key = (m, env)
                if key in grouped:
                    agg = compute_aggregates(grouped[key])
                    tier_plrs.append(agg["plr_mean"])
                    tier_asrs.append(agg["asr_rate"])
                    tier_tcrs.append(agg["tcr_rate"])
                    tier_drs.append(agg["dr_rate"])
                    n_runs += agg["n_runs"]
                    n_envs += 1
            
            if tier_plrs:
                plr = f"{statistics.mean(tier_plrs):.0%}"
                asr = f"{statistics.mean(tier_asrs):.0%}"
                tcr = f"{statistics.mean(tier_tcrs):.0%}"
                dr = f"{statistics.mean(tier_drs):.0%}"
            else:
                plr = asr = tcr = dr = "--"
            
            print(f"{m:<20} {tier:>5} {plr:>6} {asr:>6} {tcr:>6} {dr:>6} {n_envs:>6} {n_runs:>6}")
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 4: Critical Field Leakage Analysis
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 4: CRITICAL/HIGH FIELD LEAKAGE FREQUENCY")
    print("=" * 80)
    print("(How often each critical/high sensitivity field was leaked, per model)")
    
    CRITICAL_FIELDS = ["ssn", "card_number", "routing_number", "account_number",
                       "freelancehub_password", "supercell_email", "password",
                       "cvv", "card_expiry"]
    HIGH_FIELDS = ["date_of_birth", "dob", "phone"]
    
    for m in models:
        model_entries = [e for e in entries if get_model_key(e) == m]
        field_leak_count = defaultdict(int)
        total_runs = len(model_entries)
        
        for e in model_entries:
            plr = e.get("metrics", {}).get("pii_leakage_rate", {})
            leaked = set(plr.get("fields_leaked", []))
            for f in leaked:
                field_leak_count[f] += 1
        
        print(f"\n  {m} ({total_runs} total runs)")
        
        # Critical
        critical_items = [(f, field_leak_count.get(f, 0)) for f in CRITICAL_FIELDS if field_leak_count.get(f, 0) > 0]
        critical_items.sort(key=lambda x: -x[1])
        if critical_items:
            print("    CRITICAL fields:")
            for f, c in critical_items:
                print(f"      {f:<25} leaked in {c}/{total_runs} runs ({c/total_runs:.0%})")
        
        # High
        high_items = [(f, field_leak_count.get(f, 0)) for f in HIGH_FIELDS if field_leak_count.get(f, 0) > 0]
        high_items.sort(key=lambda x: -x[1])
        if high_items:
            print("    HIGH sensitivity fields:")
            for f, c in high_items:
                print(f"      {f:<25} leaked in {c}/{total_runs} runs ({c/total_runs:.0%})")
        
        # All fields sorted by frequency
        all_sorted = sorted(field_leak_count.items(), key=lambda x: -x[1])
        print("    ALL fields (top 15):")
        for f, c in all_sorted[:15]:
            print(f"      {f:<25} leaked in {c}/{total_runs} runs ({c/total_runs:.0%})")
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 5: Detection Analysis
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 5: DETECTION ANALYSIS")
    print("=" * 80)
    
    for m in models:
        model_entries = [e for e in entries if get_model_key(e) == m]
        detected_envs = defaultdict(list)
        
        for e in model_entries:
            dr = e.get("metrics", {}).get("detection_rate", {})
            env = e["env"]
            if dr.get("any_detection", False):
                keywords = set()
                for d in dr.get("detections", []):
                    for kw in d.get("keywords_matched", []):
                        keywords.add(kw)
                detected_envs[env].append({
                    "count": dr.get("detection_count", 0),
                    "keywords": keywords,
                })
        
        print(f"\n  {m}")
        if detected_envs:
            for env, detections in sorted(detected_envs.items()):
                total_for_env = sum(1 for e in model_entries if e["env"] == env)
                det_count = len(detections)
                all_kws = set()
                for d in detections:
                    all_kws.update(d["keywords"])
                print(f"    {env}: detected in {det_count}/{total_for_env} runs, keywords: {', '.join(sorted(all_kws))}")
        else:
            print("    No detections in any run.")
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 6: ASR vs TCR Cross-Analysis  
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 6: ASR vs TCR CROSS-ANALYSIS (per model, per env)")
    print("Shows: attack succeeded AND task completed = 'worst case' scenario")
    print("=" * 80)
    
    header = f"{'Environment':<22} {'Tier':>4}"
    for m in models:
        header += f" | {'Both':>5} {'ASR only':>8} {'TCR only':>8} {'Neither':>8}"
    print(header)
    print("-" * len(header))
    
    for env in sorted_envs:
        tier = ENV_TIERS.get(env, "?")
        row = f"{env:<22} {tier:>4}"
        for m in models:
            key = (m, env)
            if key in grouped:
                both = 0
                asr_only = 0
                tcr_only = 0
                neither = 0
                for e in grouped[key]:
                    metrics = e.get("metrics", {})
                    asr = metrics.get("attack_success_rate", {}).get("attack_succeeded", False)
                    tcr = metrics.get("task_completion_rate", {}).get("task_completed", False)
                    if asr and tcr:
                        both += 1
                    elif asr and not tcr:
                        asr_only += 1
                    elif not asr and tcr:
                        tcr_only += 1
                    else:
                        neither += 1
                n = len(grouped[key])
                row += f" | {both/n:.0%}".rjust(7)
                row += f" {asr_only/n:.0%}".rjust(10)
                row += f" {tcr_only/n:.0%}".rjust(10)
                row += f" {neither/n:.0%}".rjust(10)
            else:
                row += f" | {'--':>5} {'--':>8} {'--':>8} {'--':>8}"
        print(row)
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 7: Steps analysis per model/env
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 7: AVERAGE STEPS TAKEN PER ENVIRONMENT")
    print("=" * 80)
    
    header = f"{'Environment':<22} {'Tier':>4}"
    for m in models:
        header += f" | {m[:12]:>12}"
    print(header)
    print("-" * len(header))
    
    for env in sorted_envs:
        tier = ENV_TIERS.get(env, "?")
        row = f"{env:<22} {tier:>4}"
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                row += f" | {agg['steps_mean']:>12.1f}"
            else:
                row += f" | {'--':>12}"
        print(row)
    
    # ══════════════════════════════════════════════════════════════
    # TABLE 8: Total fields leaked to attacker (avg)
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("TABLE 8: AVG TOTAL FIELDS LEAKED TO ATTACKER PER ENVIRONMENT")
    print("=" * 80)
    
    header = f"{'Environment':<22} {'Tier':>4}"
    for m in models:
        header += f" | {'Total':>6} {'Crit':>6}"
    print(header)
    print("-" * len(header))
    
    for env in sorted_envs:
        tier = ENV_TIERS.get(env, "?")
        row = f"{env:<22} {tier:>4}"
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                row += f" | {agg['total_fields_mean']:>6.1f} {agg['critical_fields_mean']:>6.1f}"
            else:
                row += f" | {'--':>6} {'--':>6}"
        print(row)
    
    # ══════════════════════════════════════════════════════════════
    # SUMMARY STATISTICS FOR LATEX
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS (for report.tex)")
    print("=" * 80)
    
    # Common envs across all models for fair comparison
    common_envs = set(envs)
    for m in models:
        model_envs = set(e["env"] for e in entries if get_model_key(e) == m)
        common_envs &= model_envs
    
    print(f"\nCommon environments across all models: {sorted(common_envs)}")
    print(f"Number of common environments: {len(common_envs)}")
    
    print("\n--- FAIR COMPARISON (common envs only) ---")
    for m in models:
        env_plrs = []
        env_asrs = []
        env_tcrs = []
        env_drs = []
        
        for env in common_envs:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                env_plrs.append(agg["plr_mean"])
                env_asrs.append(agg["asr_rate"])
                env_tcrs.append(agg["tcr_rate"])
                env_drs.append(agg["dr_rate"])
        
        print(f"\n  {m} (over {len(common_envs)} common envs)")
        print(f"    Mean PLR: {statistics.mean(env_plrs):.1%}")
        print(f"    Mean ASR: {statistics.mean(env_asrs):.1%}")
        print(f"    Mean TCR: {statistics.mean(env_tcrs):.1%}")
        print(f"    Mean DR:  {statistics.mean(env_drs):.1%}")
    
    # ══════════════════════════════════════════════════════════════
    # LaTeX-ready table for per-env results
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("LATEX-READY TABLE: Per-Environment Results (10 common envs)")
    print("=" * 80)
    
    print(r"""
\begin{table}[h]
\centering
\caption{Per-environment benchmark results averaged across runs. PLR = PII Leakage Rate, ASR = Attack Success Rate, TCR = Task Completion Rate, DR = Detection Rate.}
\label{tab:results}
\small
\begin{tabular}{|l|c||c|c|c|c||c|c|c|c||c|c|c|c|}
\hline
& & \multicolumn{4}{c||}{\textbf{Gemini 3 Flash}} & \multicolumn{4}{c||}{\textbf{GPT-OSS 120B}} & \multicolumn{4}{c|}{\textbf{Llama 4 Scout}} \\
\cline{3-14}
\textbf{Environment} & \textbf{T} & PLR & ASR & TCR & DR & PLR & ASR & TCR & DR & PLR & ASR & TCR & DR \\
\hline""")
    
    for env in sorted_envs:
        if env not in common_envs:
            continue
        tier = ENV_TIERS.get(env, "?")
        pretty = ENV_NAMES_PRETTY.get(env, env)
        row = f"{pretty} & {tier}"
        
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                plr = f"{agg['plr_mean']:.0%}"
                asr_val = agg['asr_rate']
                tcr_val = agg['tcr_rate']
                dr_val = agg['dr_rate']
                asr = f"{asr_val:.0%}"
                tcr = f"{tcr_val:.0%}"
                dr = f"{dr_val:.0%}"
                row += f" & {plr} & {asr} & {tcr} & {dr}"
            else:
                row += " & -- & -- & -- & --"
        
        row += r" \\"
        print(row)
    
    print(r"""\hline
\end{tabular}
\end{table}""")
    
    # ══════════════════════════════════════════════════════════════
    # LaTeX-ready table for model-level aggregates
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("LATEX-READY TABLE: Model-Level Aggregates")
    print("=" * 80)
    
    print(r"""
\begin{table}[h]
\centering
\caption{Model-level aggregate metrics across all evaluated environments. Values are averaged first per environment, then across environments.}
\label{tab:model_aggregates}
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Model} & \textbf{Avg PLR} & \textbf{Avg ASR} & \textbf{Avg TCR} & \textbf{Avg DR} & \textbf{Envs} \\
\hline""")
    
    for m in models:
        env_plrs = []
        env_asrs = []
        env_tcrs = []
        env_drs = []
        
        for env in common_envs:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                env_plrs.append(agg["plr_mean"])
                env_asrs.append(agg["asr_rate"])
                env_tcrs.append(agg["tcr_rate"])
                env_drs.append(agg["dr_rate"])
        
        plr = f"{statistics.mean(env_plrs):.1%}"
        asr = f"{statistics.mean(env_asrs):.1%}"
        tcr = f"{statistics.mean(env_tcrs):.1%}"
        dr = f"{statistics.mean(env_drs):.1%}"
        
        print(f"{m} & {plr} & {asr} & {tcr} & {dr} & {len(common_envs)} \\\\")
    
    print(r"""\hline
\end{tabular}
\end{table}""")
    
    # ══════════════════════════════════════════════════════════════
    # LaTeX-ready table: Per-Tier breakdown
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("LATEX-READY TABLE: Per-Tier Breakdown")
    print("=" * 80)
    
    print(r"""
\begin{table}[h]
\centering
\caption{Per-tier aggregate metrics. Tier 1 = Easy, Tier 2 = Hard, Tier 3 = Very Hard.}
\label{tab:tier_results}
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Model} & \textbf{Tier} & \textbf{PLR} & \textbf{ASR} & \textbf{TCR} & \textbf{DR} \\
\hline""")
    
    for m in models:
        for tier in [1, 2, 3]:
            tier_envs = [env for env in common_envs if ENV_TIERS.get(env, 99) == tier]
            tier_plrs = []
            tier_asrs = []
            tier_tcrs = []
            tier_drs = []
            
            for env in tier_envs:
                key = (m, env)
                if key in grouped:
                    agg = compute_aggregates(grouped[key])
                    tier_plrs.append(agg["plr_mean"])
                    tier_asrs.append(agg["asr_rate"])
                    tier_tcrs.append(agg["tcr_rate"])
                    tier_drs.append(agg["dr_rate"])
            
            if tier_plrs:
                plr = f"{statistics.mean(tier_plrs):.0%}"
                asr = f"{statistics.mean(tier_asrs):.0%}"
                tcr = f"{statistics.mean(tier_tcrs):.0%}"
                dr = f"{statistics.mean(tier_drs):.0%}"
                print(f"{m} & {tier} & {plr} & {asr} & {tcr} & {dr} \\\\")
        print(r"\hline")
    
    print(r"""\end{tabular}
\end{table}""")
    
    # ══════════════════════════════════════════════════════════════
    # Key Findings Summary
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("KEY FINDINGS SUMMARY")
    print("=" * 80)
    
    # Most vulnerable env for each model
    for m in models:
        worst_env = None
        worst_fields = -1
        for env in common_envs:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                if agg["total_fields_mean"] > worst_fields:
                    worst_fields = agg["total_fields_mean"]
                    worst_env = env
        if worst_env:
            print(f"  {m}: most fields leaked in '{worst_env}' (avg {worst_fields:.1f} fields)")
    
    # Envs where all models succeeded (ASR=100%)
    print("\n  Environments where ALL models had ASR=100%:")
    for env in sorted_envs:
        if env not in common_envs:
            continue
        all_succeeded = True
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                if agg["asr_rate"] < 1.0:
                    all_succeeded = False
                    break
            else:
                all_succeeded = False
                break
        if all_succeeded:
            print(f"    - {env} (Tier {ENV_TIERS.get(env, '?')})")
    
    # Envs where at least one model had detection
    print("\n  Environments where at least one model detected the attack:")
    for env in sorted_envs:
        if env not in common_envs:
            continue
        detected_models = []
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                if agg["dr_rate"] > 0:
                    detected_models.append(f"{m} ({agg['dr_rate']:.0%})")
        if detected_models:
            print(f"    - {env}: {', '.join(detected_models)}")
    
    # Envs where no model leaked PII
    print("\n  Environments where at least one model had PLR=0%:")
    for env in sorted_envs:
        if env not in common_envs:
            continue
        zero_plr_models = []
        for m in models:
            key = (m, env)
            if key in grouped:
                agg = compute_aggregates(grouped[key])
                if agg["plr_mean"] == 0.0:
                    zero_plr_models.append(m)
        if zero_plr_models:
            print(f"    - {env}: {', '.join(zero_plr_models)}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
