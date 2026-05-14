"""
CLI entry point for the web navigation agent benchmark.

Usage:
    # Single env, single model (quick test)
    python -m agent.runner --env cluttered_downloads --model gemini --headed

    # Run the benchmark subset (10 curated envs) with one model
    python -m agent.runner --env benchmark --model llama-scout

    # Run all 16 environments
    python -m agent.runner --env all --model gpt-oss

    # Full benchmark: all 3 models × 10 envs
    python -m agent.runner --env benchmark --model all

    # Run specific tier only
    python -m agent.runner --env tier1 --model gemini --max-steps 30

    # Custom run name for organizing results
    python -m agent.runner --env job_portal --model gemini --run-name test-run-1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout on Windows. Without this, agent / scorer prints
# that include glyphs from rendered page content (e.g. ⬇ from a
# website's HTML) crash the whole run with a cp1252 charmap error.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

from .core.agent import WebNavigationAgent, load_user_profile, load_env_config
from .core.llm_factory import (
    MODEL_REGISTRY,
    MODEL_ALIASES,
    resolve_model_name,
    get_model_info,
)
from .evaluation.logger import SessionLogger
from .evaluation.pii_tracker import PIITracker
from .evaluation.scorer import Scorer, SERVER_CAPTURE_PORTS


# -- Environment definitions -------------------------------------------

AVAILABLE_ENVS = [
    "job_portal", "ecommerce", "news", "freelance", "gov_portal",
    "coc_gems", "cluttered_downloads",
    "marketplace", "github_phish", "summarizer",
    "virus_scanner", "file_converter", "quiz_scam",
    "support_chat", "saas_onboard", "crypto_platform",
    # Phase 3 worked-brief calibration envs
    "virus_scanner_calm", "virus_scanner_subtle",
    "marketplace_pi_hidden",
    "forum_register_medium", "forum_register_critical",
    # Phase 3 Wave C — salience siblings (Vaibhav)
    "virus_scanner_plausible",
    "quiz_scam_subtle",
    "summarizer_plausible",
    "summarizer_subtle",
    "crypto_platform_blatant",
    "crypto_platform_subtle",
    "saas_onboard_subtle",
    "e10_mychart_plausible",
    "e10_mychart_blatant",
    "freelance_blatant",
    "support_chat_plausible",
    # Phase 3 Wave A — pressure siblings
    "job_portal_no_timer",
    "gov_portal_no_timer",
    "marketplace_calm",
    # Phase 3 Wave B — prompt injection siblings (Sarthak)
    "ecommerce_pi",
    "news_pi",
    "quiz_scam_pi_sysmsg",
    "e8_chase_pi_hidden",
    "e17_amazon_pi_visible",
    "saas_onboard_pi_hidden",
    "saas_onboard_pi_sysmsg",
    "support_chat_pi_visible",
    "support_chat_pi_sysmsg",
    # Phase 3 Wave D — interaction style siblings (Sarthak)
    "summarizer_chat",
    "marketplace_chat",
    "gov_portal_chat",
    "e18_linkedin_chat",
    "support_chat_static",
    "freelance_static",
    # Standalone scam envs
    "dating_verify",
    "adp_no_banner",
    "aws_no_countdown",
    "booking_no_timer",
    "e7_ninite_calm",
    "e8_chase_no_countdown",
    # Wave G — authority pressure sibling
    "saas_onboard_authority",
    "adp_authority",
    "marketplace_social_proof",
    "e23_netflix_social_proof",
    "ecommerce_scarcity",
    "github_phish_scarcity",
    # newly added envs
    "news_medium",
    "bumble_medium",
    "saas_onboard_medium",
    "e10_mychart_calm",
    "e13_irs_no_timer",
    "e14_oracle_no_timer",
    "job_portal_medium",
    "saas_onboard_direct",
    "marketplace_email_entry",
    "ancestry_dna_email_entry",
    "betterhelp_email_entry",
    "bumble_email_entry",
    "dating_photo_id",
    "insurance_quote",
    "insurance_quote_medium",
    # Stranded parents (Phase 1/2 builds promoted into the registry so
    # F-pair siblings have a runnable parent for ablation comparisons).
    "adp",
    "aws",
    "ancestry_dna",
    "betterhelp",
    "booking",
    "bumble",
    "e7_ninite",
    "e8_chase",
    "e10_mychart",
    "e13_irs",
    "e14_oracle",
    "e17_amazon",
    "e18_linkedin",
    "e23_netflix",
    # Phase 4 — Benign twin baselines (no attack elements)
    "job_portal_benign",
    "e18_linkedin_benign",
    "freelance_benign",
    "ecommerce_benign",
    "marketplace_benign",
    "e17_amazon_benign",
    "gov_portal_benign",
    "e13_irs_benign",
    "support_chat_benign",
    "e12_dhl_benign",
]

# Curated benchmark subset (4 easy + 4 hard + 2 very hard = 10 envs)
BENCHMARK_ENVS = [
    # Tier 1: Easy
    "cluttered_downloads",
    "coc_gems",
    "github_phish",
    "summarizer",
    # Tier 2: Hard
    "job_portal",
    "gov_portal",
    "ecommerce",
    "marketplace",
    # Tier 3: Very Hard
    "freelance",
    "news",
]

TIER1_ENVS = ["cluttered_downloads", "coc_gems", "github_phish", "summarizer"]
TIER2_ENVS = ["job_portal", "gov_portal", "ecommerce", "marketplace"]
TIER3_ENVS = ["freelance", "news"]

# LLM-generated website subset (all 10 benchmark envs)
LLMPIT_ENVS = [
    "cluttered_downloads", "coc_gems", "github_phish", "summarizer",
    "job_portal", "gov_portal", "ecommerce", "marketplace",
    "news", "freelance",
]

WORKED_BRIEFS_ENVS = [
    "virus_scanner_calm",
    "virus_scanner_subtle",
    "marketplace_pi_hidden",
    "forum_register_medium",
    "forum_register_critical",
]

# Wave C — salience siblings (Vaibhav). Includes the worked-brief env
# virus_scanner_subtle plus the post-calibration fan-out.
WAVE_C_ENVS = [
    "virus_scanner_plausible",
    "virus_scanner_subtle",
    "quiz_scam_subtle",
    "summarizer_plausible",
    "summarizer_subtle",
    "crypto_platform_blatant",
    "crypto_platform_subtle",
    "saas_onboard_subtle",
    "e10_mychart_plausible",
    "e10_mychart_blatant",
    "freelance_blatant",
    "support_chat_plausible",
]

# Wave B — prompt injection siblings (Sarthak)
WAVE_B_ENVS = [
    "ecommerce_pi",
    "marketplace_pi_hidden",
    "news_pi",
    "quiz_scam_pi_sysmsg",
    "e8_chase_pi_hidden",
    "e17_amazon_pi_visible",
    "saas_onboard_pi_hidden",
    "saas_onboard_pi_sysmsg",
    "support_chat_pi_visible",
    "support_chat_pi_sysmsg",
]

# Wave D — interaction style siblings (Sarthak)
WAVE_D_ENVS = [
    "summarizer_chat",
    "marketplace_chat",
    "gov_portal_chat",
    "e18_linkedin_chat",
    "support_chat_static",
    "freelance_static",
]

# Combined Wave B + D (all 16 Sarthak environments)
WAVE_BD_ENVS = WAVE_B_ENVS + WAVE_D_ENVS

# Phase 4 — Benign twin baselines
BENIGN_TWIN_ENVS = [
    "job_portal_benign",
    "e18_linkedin_benign",
    "freelance_benign",
    "ecommerce_benign",
    "marketplace_benign",
    "e17_amazon_benign",
    "gov_portal_benign",
    "e13_irs_benign",
    "support_chat_benign",
    "e12_dhl_benign",
]

ENV_GROUPS = {
    "all":            AVAILABLE_ENVS,
    "benchmark":      BENCHMARK_ENVS,
    "tier1":          TIER1_ENVS,
    "tier2":          TIER2_ENVS,
    "tier3":          TIER3_ENVS,
    "llmpit":         LLMPIT_ENVS,
    "worked_briefs":  WORKED_BRIEFS_ENVS,
    "wave_c":         WAVE_C_ENVS,
    "wave_b":         WAVE_B_ENVS,
    "wave_d":         WAVE_D_ENVS,
    "wave_bd":        WAVE_BD_ENVS,
    "benign_twins":   BENIGN_TWIN_ENVS,
}

# -- Model definitions -------------------------------------------------

BENCHMARK_MODELS = [
    "gemini-3-flash-preview",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-oss-120b",
]

# v2 model set per paper-plan.md §2.6 — drops gpt-oss-120b (pilot-only),
# adds the two OpenRouter frontier models.
V2_MODELS = [
    "google/gemini-2.0-flash-001",         # via OpenRouter (no native Gemini key needed)
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-5",
    "anthropic/claude-sonnet-4.6",
]


def parse_args() -> argparse.Namespace:
    all_env_choices = AVAILABLE_ENVS + list(ENV_GROUPS.keys())
    all_model_aliases = list(MODEL_ALIASES.keys()) + list(MODEL_REGISTRY.keys()) + ["all", "all-v2"]

    parser = argparse.ArgumentParser(
        description="Web Navigation Agent Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick single test
  python -m agent.runner --env cluttered_downloads --model gemini --headed

  # Run a specific tier
  python -m agent.runner --env tier1 --model llama-scout --max-steps 30

  # Full benchmark (10 envs × 1 model)
  python -m agent.runner --env benchmark --model gpt-oss

  # Full benchmark (10 envs × all 3 models)
  python -m agent.runner --env benchmark --model all

  # With custom run name
  python -m agent.runner --env benchmark --model gemini --run-name pilot-v1

Available environment groups:
  all        — all 16 environments
  benchmark  — curated 10 (4 easy + 4 hard + 2 very hard)
  tier1      — 4 easy environments
  tier2      — 4 hard environments
  tier3      — 2 very hard environments

Available model aliases:
<<<<<<< HEAD
  gemini       → gemini-3-flash-preview
  llama-scout  → meta-llama/llama-4-scout-17b-16e-instruct
  llama4       → meta-llama/llama-4-scout-17b-16e-instruct
  gpt-oss      → openai/gpt-oss-120b
  gpt-oss-120b → openai/gpt-oss-120b
  gpt-5        → openai/gpt-5             (via OpenRouter)
  sonnet-4.6   → anthropic/claude-sonnet-4.6 (via OpenRouter)
  all          → run all 3 pilot benchmark models sequentially
  all-v2       → run the 4 v2 models (Gemini, Llama 4, GPT-5, Sonnet 4.6)
=======
  gemini       -> gemini-3-flash-preview
  llama-scout  -> meta-llama/llama-4-scout-17b-16e-instruct
  llama4       -> meta-llama/llama-4-scout-17b-16e-instruct
  gpt-oss      -> openai/gpt-oss-120b
  gpt-oss-120b -> openai/gpt-oss-120b
  all          -> run all 3 benchmark models sequentially
>>>>>>> e732dfd0d9e4ab7b389852930e8b80c4c368d25e
        """,
    )
    parser.add_argument(
        "--env",
        type=str,
        required=True,
        choices=all_env_choices,
        help="Environment or group to run (see --help for groups)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3-flash-preview",
        help="Model name or alias (default: gemini-3-flash-preview). Use 'all' for all 3 models.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum steps before stopping (default: 50)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible window) for debugging",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the model backend (or set GEMINI_API_KEY / GROQ_API_KEY env var)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for log output (default: agent/logs/)",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Name for this run (used in output directory and log files)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be run without actually running",
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="C0",
        choices=["C0", "C1", "C2", "C3"],
        help="Mitigation condition: C0=baseline, C1=generic privacy nudge, "
             "C2=phishing-aware checklist, C3=reflective trust judgment",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    return parser.parse_args()


def reset_env_state(env_name: str) -> None:
    """Call /api/clear on all servers for this environment to reset state between runs."""
    import urllib.request
    ports = SERVER_CAPTURE_PORTS.get(env_name, [])
    for port in ports:
        try:
            req = urllib.request.Request(
                f"http://localhost:{port}/api/clear", method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                resp.read()
        except Exception:
            pass  # server may not have /api/clear, or may be unreachable — skip silently


def resolve_envs(env_arg: str) -> list[str]:
    """Resolve an env argument to a list of environment names."""
    if env_arg in ENV_GROUPS:
        return ENV_GROUPS[env_arg]
    return [env_arg]


def resolve_models(model_arg: str) -> list[str]:
    """Resolve a model argument to a list of canonical model names."""
    if model_arg == "all":
        return BENCHMARK_MODELS
    if model_arg == "all-v2":
        return V2_MODELS
    return [resolve_model_name(model_arg)]


async def run_single_env(
    env_name: str,
    model: str,
    max_steps: int,
    headless: bool,
    api_key: str | None,
    output_dir: Path | None,
    condition: str = "C0",
    seed: int = 42,
) -> dict:
    """Run the agent on a single environment and return the score report."""
    model_info = get_model_info(model)
    model_label = model_info.get("label", model)

    print(f"\n{'='*60}")
    print(f"  Starting: {env_name}")
    print(f"  Model: {model_label}")
    print(f"  Vision: {'yes' if model_info['vision'] else 'no (DOM text only)'}")
    print(f"  Condition: {condition} | Seed: {seed}")
    print(f"  Max steps: {max_steps} | Headless: {headless}")
    print(f"{'='*60}\n")

    # Reset server-side state (unread flags, captured data, session logs) before each run
    reset_env_state(env_name)

    agent = WebNavigationAgent(
        env_name=env_name,
        model=model,
        max_steps=max_steps,
        headless=headless,
        api_key=api_key,
        condition=condition,
        seed=seed,
    )

    logger = SessionLogger(env_name, model, log_dir=output_dir)
    logger.set_metadata(condition=condition, seed=seed)
    agent.set_logger(logger)

    profile = load_user_profile()
    pii_tracker = PIITracker(profile)
    agent.set_pii_tracker(pii_tracker)

    print(f"Agent navigating to start URL...")
    session_log = await agent.run()

    env_config = load_env_config(env_name)
    use_domains = env_config.get("_use_domains", False)
    scorer = Scorer(
        env_name=env_name,
        session_log=session_log,
        pii_leaks=pii_tracker.get_leaks(),
        use_domains=use_domains,
    )

    scorer.print_report()
    report = scorer.score()

    report_path = logger.filepath.with_suffix(".score.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Log saved to: {logger.filepath}")
    print(f"  Score saved to: {report_path}")

    pii_summary = pii_tracker.summary()
    if pii_summary["total_leaks"] > 0:
        print(f"\n  PII Tracker Summary:")
        print(f"    Total fields typed as PII: {pii_summary['total_leaks']}")
        print(f"    Critical leaks: {pii_summary['critical_leaks']}")
        print(f"    Fields leaked: {pii_summary['unique_fields_leaked']}")
        print(f"    Domains leaked to: {pii_summary['domains_leaked_to']}")

    return report


async def main() -> None:
    args = parse_args()

    envs = resolve_envs(args.env)
    models = resolve_models(args.model)
    headless = not args.headed

    # Build output directory
    run_name = args.run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    base_output = Path(args.output_dir) if args.output_dir else None

    # -- Dry run -------------------------------------------------------
    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"  DRY RUN — {run_name}")
        print(f"{'='*60}")
        print(f"  Models ({len(models)}):")
        for m in models:
            info = get_model_info(m)
            print(f"    - {info.get('label', m)} ({'VLM' if info['vision'] else 'text-only'})")
        print(f"  Environments ({len(envs)}):")
        for e in envs:
            print(f"    - {e}")
        print(f"  Condition: {args.condition}")
        print(f"  Seed: {args.seed}")
        print(f"  Total runs: {len(models) * len(envs)}")
        print(f"  Max steps: {args.max_steps}")
        print(f"  Headed: {args.headed}")
        print(f"{'='*60}\n")
        return

    # -- Execute -------------------------------------------------------
    total_runs = len(models) * len(envs)
    run_idx = 0
    all_reports: list[dict] = []

    print(f"\n{'='*60}")
    print(f"  Benchmark Run: {run_name}")
    print(f"  {len(models)} model(s) × {len(envs)} environment(s) = {total_runs} total runs")
    print(f"{'='*60}\n")

    for model in models:
        model_info = get_model_info(model)
        model_short = model_info.get("label", model)

        # Per-model output directory
        if base_output:
            output_dir = base_output / run_name / model_short.replace(" ", "_")
        else:
            output_dir = None

        for env_name in envs:
            run_idx += 1
            print(f"\n{'#'*60}")
            print(f"  RUN {run_idx}/{total_runs}: {env_name} × {model_short} [{args.condition}]")
            print(f"{'#'*60}")

            try:
                report = await run_single_env(
                    env_name=env_name,
                    model=model,
                    max_steps=args.max_steps,
                    headless=headless,
                    api_key=args.api_key,
                    output_dir=output_dir,
                    condition=args.condition,
                    seed=args.seed,
                )
                report["_run_name"] = run_name
                all_reports.append(report)
            except Exception as e:
                print(f"\n  ERROR running {env_name} × {model_short}: {e}")
                import traceback
                traceback.print_exc()
                all_reports.append({
                    "env": env_name,
                    "model": model,
                    "model_label": model_short,
                    "error": str(e),
                    "_run_name": run_name,
                })

    # -- Aggregate results ---------------------------------------------
    if len(all_reports) > 1:
        print(f"\n{'='*60}")
        print(f"  AGGREGATE RESULTS — {run_name}")
        print(f"{'='*60}")
        print(f"  {'Model':<35} {'Env':<25} {'c-PLR':>6} {'PLR':>6} {'ASR':>10} {'TCR':>10} {'DR':>10}  {'Quality':>8}")
        print(f"  {'-'*110}")
        unreliable_count = 0
        for report in all_reports:
            env = report.get("env", "?")
            model_label = report.get("model_label", report.get("model", "?"))
            if "error" in report:
                print(f"  {model_label:<35} {env:<25} ERROR: {report['error'][:30]}")
            else:
                s = report.get("summary", {})
                dq = report.get("data_quality", {})
                reliable = s.get("reliable", dq.get("reliable", True))
                quality_tag = "OK" if reliable else "UNRELIABLE"
                if not reliable:
                    unreliable_count += 1
                print(
                    f"  {model_label:<35} {env:<25} "
                    f"{s.get('c_PLR','?'):>6} {s.get('PLR','?'):>6} "
                    f"{s.get('ASR','?'):>10} "
                    f"{s.get('TCR','?'):>10} {s.get('DR','?'):>10}  "
                    f"{quality_tag:>8}"
                )
        if unreliable_count > 0:
            print(f"\n  WARNING: {unreliable_count} run(s) flagged as UNRELIABLE due to excessive parse failures")
        print(f"{'='*60}\n")

    # Save aggregate report
    if all_reports:
        agg_dir = (base_output / run_name) if base_output else (Path("agent/logs") / run_name)
        agg_dir.mkdir(parents=True, exist_ok=True)
        agg_path = agg_dir / "aggregate_results.json"
        with open(agg_path, "w") as f:
            json.dump(all_reports, f, indent=2, default=str)
        print(f"  Aggregate results saved to: {agg_path}")


def entry():
    asyncio.run(main())


if __name__ == "__main__":
    entry()
