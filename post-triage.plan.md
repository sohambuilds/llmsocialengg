---
name: Post-triage consolidation and sibling generation
overview: Apply the triage recommendations from classification_candidates.csv, merge the keeps into the master classification table, harness-align the 6 "revise" envs, then pivot generation from new archetypes to factor-axis ablation siblings on existing archetypes. This takes the benchmark from ~16 blessed envs to a target of ~100 factorially-covered envs with strong ablation pairs.
todos:
  - id: phase1_count_fix
    content: "Fix count mismatches in classification_summary.md (real numbers: 41 total / 33 keep / 7 revise / 1 drop)"
    status: completed
  - id: phase1_a3_prune
    content: "Apply A3 prune: keep BCBS, BetterHelp, Bumble, AncestryDNA, one SaaS rep; drop the other 6 template clones"
    status: completed
  - id: phase1_merge
    content: Merge keep rows from classification_candidates.csv into classification.csv, stripping triage-only columns
    status: completed
  - id: phase1_dm_fix
    content: Fix dm_primary_category on freelance / support_chat / coc_gems in classification.csv
    status: completed
  - id: phase1_gap_regen
    content: Regenerate TAXO.md Gap Analysis and Audit table against the merged master CSV
    status: completed
  - id: phase2_endpoint_align
    content: Rename /log-interaction, /capture-* endpoints to /api/captured in the 6 revise envs
    status: pending
  - id: phase2_logfile_rename
    content: Rename test_logs_*.json and captured_*.json to captured_data.json in the 6 revise envs
    status: pending
  - id: phase2_awscert_readme
    content: Write scenario-card README for awscert describing attack flow, win path, PII targets, success criteria
    status: pending
  - id: phase2_yaml_wire
    content: Add 6 revise envs to agent/config/environments.yaml and start_servers.sh with unique ports; update CLAUDE.md PORT ASSIGNMENTS
    status: pending
  - id: phase2_smoke_test
    content: "Smoke-test all 6 revise envs: GET /api/captured returns entries, agent dry-run completes"
    status: pending
  - id: phase3_pressure_siblings
    content: "Phase 3.2: generate ~12 pressure-on/off sibling pairs on existing urgency archetypes"
    status: pending
  - id: phase3_pi_siblings
    content: "Phase 3.2: generate ~8 prompt-injection sibling pairs on existing no-PI archetypes"
    status: pending
  - id: phase3_salience_siblings
    content: "Phase 3.2: add missing salience variants to 6 archetypes (12 new envs); prioritize subtle variants"
    status: pending
  - id: phase3_static_chat_siblings
    content: "Phase 3.2: generate 5 static-vs-chat interaction siblings"
    status: pending
  - id: phase3_medium_pii_envs
    content: "Phase 3.2: build 5 envs that target only medium-sensitivity PII"
    status: pending
  - id: phase3_multisite_siblings
    content: "Phase 3.2: pair 5 single-origin envs with email_entry_plus_site variants"
    status: pending
  - id: phase3_ablation_matrix
    content: Fill in TAXO.md Ablation-Readiness table as siblings land; exit when every F1-F11 claim has at least one pair
    status: pending
isProject: false
---

## State as of end of previous chat

- [classification.csv](classification.csv) — 16 blessed envs.
- [classification_candidates.csv](classification_candidates.csv) — 41 triaged candidate envs (header claims 37 but real count is 41).
- [classification_summary.md](classification_summary.md) — the triage agent's recommendations.
- [TAXO.md](TAXO.md) — axes, archetype list, gap analysis.
- [CLAUDE.md](CLAUDE.md) — current state + v2 roadmap pointer.

The next few chats will execute three phases in order. Each phase is self-contained and can sit in its own chat.


## Phase 1 — Consolidate triage results

Goal: produce a single authoritative `classification.csv` and a cleaned env set on disk.

### 1.1 Fix counts in `classification_summary.md`
The summary says 37 total / 30 keep / 6 revise / 1 drop. Real numbers from the CSV are 41 total / 33 keep / 7 revise / 1 drop (verify by counting rows by `keep_status`). Fix the summary so downstream readers aren't confused.

### 1.2 Apply the A3 prune
The summary's own recommendation: of the 11 template-clone A3 envs, keep only the 5 that fill real category gaps and drop the rest. Concrete decisions:

- **Keep**: `bcbs` (insurance gap), `betterhelp` (healthcare gap), `bumble` (dating gap), `ancestry_dna` (healthcare-adjacent), one SaaS representative (pick `1password` or `adobe`).
- **Drop**: `accessibe`, `amazon_clone` (duplicates e17-amazon), `appleid_clone` (duplicates e19-apple), `asana`, `airbnb_clone` (duplicates e25-airbnb), and whichever SaaS rep wasn't kept.
- Change `keep_status` from `keep` to `drop` on these rows and add a `quality_note` explaining the prune rationale.

### 1.3 Merge keeps into `classification.csv`
Append every row in `classification_candidates.csv` with `keep_status=keep` (post-prune) into `classification.csv`. Strip the three triage-only columns (`keep_status`, `archetype`, `quality_note`). Keep the triage CSV around unmodified as the audit trail.

### 1.4 Fix `dm_primary_category` drift in existing rows
In `classification.csv` update:

- `freelance` — `content_injection` → `semantic_manipulation` (primary vector is `conversational_deception`).
- `support_chat` — same.
- `coc_gems` — `content_injection` → `semantic_manipulation` (primary is `credential_harvest`; typosquat domains are secondary).

This aligns with the "classify by primary vector" rule stated in TAXO.md §"Outcome vs. mechanism".

### 1.5 Recount + regenerate gap analysis
Update [TAXO.md](TAXO.md) §"Gap analysis" against the new master table. Expected changes:

- Category gaps: banking / healthcare / dating / travel / social-media / insurance all close.
- Vector gaps: 2FA / SMS extraction closes (e8_chase, e11_instagram, e16_microsoft).
- Authority impersonation outside government: closes (e12_dhl, adp).
- `subtle` is still thin; new gap emphasis shifts to factor axes.
- `medium`-only `pii_target`: still zero envs.

Also update the "Audit of the current 16 environments" section — rename to "Audit of the current N environments" and regenerate the table from the merged CSV. Tier readout becomes less meaningful at this scale; keep as a short convenience line only.


## Phase 2 — Harness-align the 6 "revise" envs

Goal: make the vibecoded envs compatible with the existing evaluator harness so they can be run alongside the rest.

Targets (from the `revise` rows):
- `blog_website`, `coupons_website`, `email_generator` — rename `/log-interaction` → `/api/captured`, rename log files (`test_logs_*.json` → `captured_data.json`).
- `file_downloader` — rename `/capture-download` → `/api/captured`, `captured_download.json` → `captured_data.json`.
- `finance_analysis` — rename `/capture-finance` → `/api/captured`, `captured_finance.json` → `captured_data.json`.
- `awscert` — write a proper scenario card README documenting the attack flow, win path, success criteria, PII targets. The code works; the docs don't.

Also:
- Add each of them to [start_servers.sh](start_servers.sh) with its port.
- Add each to [agent/config/environments.yaml](agent/config/environments.yaml) with `task_template`, `run_servers`, and site list.
- Port assignments: pick 6 unused ports and add to the "PORT ASSIGNMENTS" block in [CLAUDE.md](CLAUDE.md).

Smoke-test: start all of them, verify `GET /api/captured` returns `{"entries": [...]}` and the agent can complete a dry run for each.


## Phase 3 — Pivot generation to factor-axis siblings

Goal: close the factor-axis (ablation) gaps while the classifying-axis gaps are already mostly full. This is what turns a 50-env benchmark into one that actually supports findings.

### 3.1 Pick the top 10 archetypes to get siblings
After Phase 1 the archetype distribution will roughly be:

- A3 (login clone): ~6 envs (pruned)
- A4 (urgency service): ~4
- A10 (paywalled tool): ~6
- A12 (progressive onboarding): ~6
- A14 (banking + 2FA): 2
- A17 (travel booking): 2
- Others: 1-2 each

Prioritise sibling generation for the archetypes with the highest existing count AND an obvious ablation gap.

### 3.2 Sibling-generation schedule (aim for ~50 new envs)

| Factor | What to build | How many | Priority |
|---|---|---|---|
| pressure on/off | For each archetype that already has `pressure=urgency`, build a `pressure=none` twin | ~12 archetypes × 1 = 12 | Highest |
| PI on/off | For archetypes with `prompt_injection=none`, build a `prompt_injection=visible_text` twin | ~8 × 1 = 8 | High |
| static vs chat | For ~5 archetypes that are currently multi_step_form, build a multi_turn_chat sibling | 5 | Medium |
| salience blatant→plausible→subtle | Pick 6 archetypes that currently have only 1 salience variant and add the missing ones | 6 × 2 = 12 | High (subtle is still thin) |
| `medium`-only pii_target | Build 5 envs that request only medium-sensitivity PII on existing archetypes (e.g. news with employer-only harvest, saas_onboard_medium with no SSN layer) | 5 | Medium (unlocks a specific claim) |
| Multi-site toggle | Pair a single_origin env with a matching email_entry_plus_site variant on 5 archetypes | 5 | Low |

Rough total: ~47 new envs.

### 3.3 Generation workflow (per sibling)
1. Identify the target archetype and the one axis being varied.
2. Copy the parent env's template + config as the base.
3. Toggle only the single axis (e.g. remove the countdown timer for a `pressure=none` variant). Nothing else changes.
4. Generate via LLM if new content needed, otherwise mechanical edit.
5. QA gate: run the existing harness test (agent smoke-test in dry-run mode); verify `/api/captured` logs work; diff the parent env's template vs the sibling to confirm only one axis differs.
6. Append row to `classification.csv`. Add a `sibling_of: <parent_env_key>` note column or track in the "ablation readiness" table in [TAXO.md](TAXO.md).

### 3.4 Fill in the ablation-readiness table
[TAXO.md](TAXO.md) §"Ablation readiness" has a placeholder table mapping paper-level claims to env pairs. As siblings land, fill in the "Example env pair" column. When a row has at least one pair, mark it green; when it has 3+ independent pairs, mark it strong.

Exit criterion: the ablation-readiness table has at least one concrete pair for every claim F1-F11.


## Phase 4 — Final QA and paper-side prep (deferred)

Out of scope for this plan — will open its own when ready. Covers:
- Running 3 models × ~100 envs × 3 seeds (~900 runs).
- Paper tables generation from the logs.
- Writing up findings against the ablation-readiness matrix.


## What goes into the next chat

Hand the next agent a short kickoff:

> Read [TAXO.md](TAXO.md), [classification.csv](classification.csv), [classification_candidates.csv](classification_candidates.csv), and [classification_summary.md](classification_summary.md). Then execute Phase 1 of this plan: apply the triage triage recommendations, prune the redundant A3 envs, merge the keeps into `classification.csv`, fix the three `dm_primary_category` drift rows, and regenerate the gap analysis in `TAXO.md`. Do not touch Phases 2 and 3.

Phase 2 and Phase 3 get their own kickoffs later.


## Rough timeline

- Phase 1: 1 chat, ~2 hours of agent time (CSV edits + TAXO.md regen).
- Phase 2: 1 chat, ~half-day (code edits + smoke-tests).
- Phase 3: 3-5 chats over ~1-2 weeks (sibling generation is the bulk of the remaining work).

Phase 4 is the paper-side push after generation is done.