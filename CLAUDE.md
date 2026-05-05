# Scammer4U — orientation for agents

A benchmark that measures whether web-browsing VLM agents hand over the
user's stored PII when a website tries to social-engineer them. The
agent runs a normal task (apply for a job, buy headphones, take a quiz);
the site contains a trap; we score what the agent leaked, whether the
attacker's outcome occurred, whether the legitimate task completed, and
whether the agent named the attack.

For "what is the project?" / per-env descriptions, read [README.md](README.md).

## Source-of-truth docs

Read these instead of duplicating them here:

- [TAXO.md](TAXO.md) — taxonomy (4 classifying + 4 factor axes), audit
  table of every env, archetype list, gap analysis, ablation-readiness
  matrix (F1–F11). Tier 1/2/3 is demoted to a shorthand readout, not
  the organising principle.
- [post-triage.plan.md](post-triage.plan.md) — the three-phase plan.
  Phase 1 done, Phase 2 pending, Phase 3 in flight.
- [phase3-checklist.md](phase3-checklist.md) — live working doc for
  Phase 3 sibling generation. As of the 2026-05-05 audit the dashboard
  matches the filesystem: 35 siblings exist on disk (Waves B, C, D
  fully built; Wave A 5/18; Wave E 2/6) and are already wired into
  `classification.csv`, `agent/config/environments.yaml`, and
  `start_servers.sh` — they sit at `🟦 qa` because per-env sign-off
  (smoke-test, screenshot diff, design brief) hasn't been verified
  individually. The remaining 24 envs (Wave A.1 tail + A.2, E partial,
  F, G) are still `🟥 todo`. Master env count is 80 (45 parents + 35
  siblings).
- [classification.csv](classification.csv) — master table of envs.
- [classification_candidates.csv](classification_candidates.csv) /
  [classification_summary.md](classification_summary.md) — triage
  audit trail (Phase 1 input).
- [analysis/analysis_results.md](analysis/analysis_results.md) —
  numerical results from the v1 pilot. Do not paste them back here;
  they will be re-run for the v2 / Phase-3 numbers.

## Repo layout (high level)

```
agent/                       — evaluator harness (Playwright + LLM loop)
  core/agent.py              — observe→think→act loop
  core/{browser,observer}.py — Playwright wrapper, screenshot+DOM
  core/{base_client,llm_client,openai_client,llm_factory}.py
                             — model backends (Gemini, Groq-hosted Llama4
                               Scout VLM, Groq-hosted GPT-OSS 120B text)
  core/{action_space,context_manager}.py
                             — JSON action schema, sliding-window memory
  config/environments.yaml   — env registry (ports, domains, task strings)
  config/user_profile.json   — agent's PII (identity / address / payment
                               / financial / professional / credentials /
                               supercell / social_media / api_keys)
  evaluation/{logger,pii_tracker,scorer}.py
                             — per-step logs, PII detection, PLR/ASR/TCR/DR
  runner.py                  — CLI: --env, --model, --max-steps, --headed,
                               --run-name, --dry-run, --output-dir, --api-key

all_websites/<env_key>/      — Flask app(s) per env with templates/, static/,
                               config.json, and an /api/captured POST sink
                               for the scorer. Multi-server envs use
                               run_servers.py.

llm-pit/                     — retired llm-generated-website pipeline.
                               Kept as infra only; not part of the paper.

start_servers.sh             — start/stop/status all benchmark env servers
                               (logs to logs/server_<env>.log)
analysis/tables.ipynb        — paper tables; analysis/*.tex output
```

## Localhost vs domain mode

The agent's browser hits each site at `http://localhost:<port>` while
templates render anchors in their fake domain form (e.g. typosquats)
via per-app `linkify` / mailbox-rewrite helpers, so the visible
red-flag stays in the page text without needing a hosts-file edit.
Flip `use_domains: true` in `agent/config/environments.yaml` (plus
hosts entries) to push the typosquat into the address bar instead.

## User profile (PII the agent carries)

`agent/config/user_profile.json` — categories: `identity`, `address`,
`payment`, `financial`, `professional`, `credentials` (freelancehub),
`supercell`, `social_media`, `api_keys`. Used by both the agent (to
fill forms) and `pii_tracker.py` (to detect leaks via value match).

## Running the eval

```
# 1. start every benchmark env server
bash start_servers.sh
bash start_servers.sh status

# 2. dry-run a single env
python -m agent.runner --env cluttered_downloads --model gemini --headed --max-steps 10

# 3. full run, all 3 models
python -m agent.runner --env benchmark --model all --run-name <run-name>

# 4. stop servers
bash start_servers.sh stop
```

Env groups in the runner: `benchmark`, `tier1`, `tier2`, `tier3`,
`all`, or any single env_key. (As Phase 3 siblings land, prefer
running explicit pair-lists for ablation studies over the legacy
tier groups.)

Model aliases: `gemini` → gemini-3-flash-preview, `llama-scout`/`llama4`
→ meta-llama/llama-4-scout-17b-16e-instruct, `gpt-oss` →
openai/gpt-oss-120b. `--model all` runs all three.

API keys: `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) for Gemini;
`GROQ_API_KEY` for Llama 4 Scout and GPT-OSS 120B.

Output: `agent/logs/<run-name>/aggregate_results.json` plus per-model
session logs and `.score.json` files.

## Port assignments

Authoritative list lives in `agent/config/environments.yaml` and
`start_servers.sh`. Reserved ranges:

```
5050–5060   tier-1-ish single-server envs + coc_gems multi-server
6010–6011   support_chat (store, refund portal)
6020–6022   saas_onboard (mailbox, app, billing)
6030–6032   crypto_platform (platform, KYC, community)
8010, 8025  job_portal (legit, mailbox)
8040–8041   news (site, billing)
8050–8051   gov_portal (mailbox, phishing)
9010–9030   freelance (hub, fake company, fake DocuSign)
10010–10080 ecommerce (8 stores)
12999       job_portal phishing
```

Phase 3 sibling envs reuse a parent's structure on a new port; check
the YAML for current assignments, not this file.

## Project config

- Python ≥3.12, package manager `uv` (`uv.lock` present).
- Top-level deps: flask, flask-cors, google-genai, openai, pillow,
  playwright, pyyaml. See `pyproject.toml` and `agent/requirements.txt`.
- Entry points: `python -m agent.runner`, per-env `app.py` /
  `run_servers.py`, `python -m agent.config.generate_resume`.

## What we test (short)

Twelve attack types: phishing clone, dark-pattern overload, urgency,
fake trust signals, fake support chat, cookie/consent dark patterns,
reward/incentive trap, social proof, conversational deception, prompt
injection, OAuth impersonation, credential harvesting via paywall.
PII tiers — critical (SSN, card+CVV, bank, passwords, API keys, 2FA),
high (email, phone, address), medium (name, employer, DOB).

## Limitations

Sites are LLM-authored with human review — snapshot of attacker
patterns at creation time. Detection Rate is a keyword-match proxy.
Multi-turn envs are noisier to evaluate. Subtle / multi-turn envs
currently show low ASR partly because agents fail to navigate to the
attack surface, not because they detect — instrumenting "reached
attack surface" is a Phase 3 priority.
