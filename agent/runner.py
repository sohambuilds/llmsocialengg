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


# ── Environment definitions ───────────────────────────────────────────

AVAILABLE_ENVS = [
    "job_portal", "ecommerce", "news", "freelance", "gov_portal",
    "coc_gems", "cluttered_downloads",
    "marketplace", "github_phish", "summarizer",
    "virus_scanner", "file_converter", "quiz_scam",
    "support_chat", "saas_onboard", "crypto_platform",
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

ENV_GROUPS = {
    "all":       AVAILABLE_ENVS,
    "benchmark": BENCHMARK_ENVS,
    "tier1":     TIER1_ENVS,
    "tier2":     TIER2_ENVS,
    "tier3":     TIER3_ENVS,
    "llmpit":    LLMPIT_ENVS,
}

# ── Model definitions ─────────────────────────────────────────────────

BENCHMARK_MODELS = [
    "gemini-3-flash-preview",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-oss-120b",
]


def parse_args() -> argparse.Namespace:
    all_env_choices = AVAILABLE_ENVS + list(ENV_GROUPS.keys())
    all_model_aliases = list(MODEL_ALIASES.keys()) + list(MODEL_REGISTRY.keys()) + ["all"]

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
  gemini       → gemini-3-flash-preview
  llama-scout  → meta-llama/llama-4-scout-17b-16e-instruct
  llama4       → meta-llama/llama-4-scout-17b-16e-instruct
  gpt-oss      → openai/gpt-oss-120b
  gpt-oss-120b → openai/gpt-oss-120b
  all          → run all 3 benchmark models sequentially
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
    return [resolve_model_name(model_arg)]


async def run_single_env(
    env_name: str,
    model: str,
    max_steps: int,
    headless: bool,
    api_key: str | None,
    output_dir: Path | None,
) -> dict:
    """Run the agent on a single environment and return the score report."""
    model_info = get_model_info(model)
    model_label = model_info.get("label", model)

    print(f"\n{'='*60}")
    print(f"  Starting: {env_name}")
    print(f"  Model: {model_label}")
    print(f"  Vision: {'yes' if model_info['vision'] else 'no (DOM text only)'}")
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
    )

    logger = SessionLogger(env_name, model, log_dir=output_dir)
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

    # ── Dry run ───────────────────────────────────────────────────────
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
        print(f"  Total runs: {len(models) * len(envs)}")
        print(f"  Max steps: {args.max_steps}")
        print(f"  Headed: {args.headed}")
        print(f"{'='*60}\n")
        return

    # ── Execute ───────────────────────────────────────────────────────
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
            print(f"  RUN {run_idx}/{total_runs}: {env_name} × {model_short}")
            print(f"{'#'*60}")

            try:
                report = await run_single_env(
                    env_name=env_name,
                    model=model,
                    max_steps=args.max_steps,
                    headless=headless,
                    api_key=args.api_key,
                    output_dir=output_dir,
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

    # ── Aggregate results ─────────────────────────────────────────────
    if len(all_reports) > 1:
        print(f"\n{'='*60}")
        print(f"  AGGREGATE RESULTS — {run_name}")
        print(f"{'='*60}")
        print(f"  {'Model':<35} {'Env':<25} {'PLR':>5} {'ASR':>5} {'TCR':>5} {'DR':>5}  {'Quality':>8}")
        print(f"  {'-'*90}")
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
                    f"{s.get('PLR','?'):>5} {s.get('ASR','?'):>5} "
                    f"{s.get('TCR','?'):>5} {s.get('DR','?'):>5}  "
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
