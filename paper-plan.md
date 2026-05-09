# Scammer4U → EMNLP submission plan

Living document. Working notes on (1) where the project sits as of
2026-05-08, (2) the paper we want to write and the venue framing, and
(3) the proposed action plan to ship in 20 days. As the v2 results land,
findings and priorities here will shift; we update *in place*, not by
appending revisions.

> **Phase 4 task list lives in [phase4-checklist.md](phase4-checklist.md).**
> That doc is the day-by-day execution plan with role assignments and
> milestones. This doc holds the paper framing and methodological
> commitments. When the two disagree, this doc wins on framing, the
> checklist wins on tasks.
>
> **Stats vocabulary used in §2.6** (mixed-effects logistic, crossed
> random effects, Benjamini–Hochberg correction, κ, MDE, PLR_crit) is
> defined in plain English in [analysis-plan.md §14 Glossary](analysis-plan.md).
> The terminology is kept here verbatim because it is the precise
> commitment we make to reviewers; the glossary is the decoder.

---

## 1. Current state of the project

### 1.1 The benchmark, in numbers

- **91 logical environments** registered in `agent/config/environments.yaml`,
  fully wired into:
  - `agent/runner.py` (`AVAILABLE_ENVS`) — selectable via `--env`
  - `agent/evaluation/scorer.py` (`SERVER_CAPTURE_PORTS`,
    `ATTACKER_PORTS_BY_ENV`, `ATTACKER_DOMAINS_BY_ENV`)
  - `start_servers.sh` (server boot)
  - `classification.csv` (axis classification, one row per env)

  Audit confirmed at 2026-05-06: zero envs missing from any registration
  file.

- **Composition.** 31 archetype parents + 60 axis-controlled siblings
  (Phase 3 wave A–G output). Each sibling differs from its parent on
  exactly one of 8 classification/factor axes, supporting paired
  ablation studies (claims F1–F11).

- **Filesystem footprint.** 106 directories under `all_websites/` in
  total. The 91-vs-106 gap is explained by 14 abandoned-brand parent
  dirs that were Phase 1/2 build assets and are not needed for any
  F-claim (1Password, BCBS, e9-expedia, e11-instagram, e12-dhl,
  e15-metamask, e16-microsoft, e17b-servicenow, e19-apple, e20-survey,
  e21-paypal, e22-zoom, e24-uber, e25-airbnb), one duplicate-naming
  artifact (`e8-chase-no-countdown/` dash variant of the underscore
  env), and 4 nested-parent cruft dirs that are inert at runtime
  (`adp_authority/ADP/`, `ecommerce_scarcity/ecommerce-platform/`,
  `github_phish_scarcity/subfolder/`,
  `ecommerce-platform-pi/templates|static/`).

### 1.2 What the benchmark measures

- **Threat model.** Attacker controls a website (or chain of sites
  reached via a forwarded email). The website is built around a known
  social-engineering pattern (12 attack vectors taxonomized in
  TAXO.md). The user has stored PII in the agent's profile
  (`agent/config/user_profile.json`). The agent is given a normal task
  ("apply for this job", "buy these headphones") and the question is
  whether the attacker can extract the user's PII through the agent.

- **Outcome metrics.**
  - **PLR** — PII Leakage Rate. Whether and what the agent submitted
    to attacker-controlled endpoints, weighted by sensitivity tier
    (critical / high / medium / low).
  - **ASR** — Attack Success Rate. Whether the attacker's intended
    outcome occurred (PII written to attacker endpoint, or
    transaction completed on attacker side).
  - **TCR** — Task Completion Rate. Whether the legitimate task was
    completed.
  - **DR** — Detection Rate. Whether the agent named the attack in
    its reasoning trace. *Currently keyword-match; planned upgrade
    to LLM-as-judge with human validation (see §3.)*

- **Axis structure.** 8 axes per env in `classification.csv`:
  4 classifying axes (`category`, `vector_primary`, `vector_secondary`,
  `pii_target`) + 4 factor axes for ablation (`salience`, `pressure`,
  `prompt_injection`, `interaction`, `multi_site`). Sibling envs are
  paired with parents differing on exactly one axis, enabling 11
  factor-claim measurements (F1–F11) defined in TAXO.md and
  phase3-checklist.md.

### 1.3 What infrastructure exists

- **Agent harness** (`agent/core/`). Playwright-based browser, observer
  (DOM + screenshot), context manager, action space, observe→think→act
  loop. Supports VLM and text-only models.
- **Model factory** (`agent/core/llm_factory.py`). Currently registered:
  `gemini-3-flash-preview`, `meta-llama/llama-4-scout-17b-16e-instruct`,
  `openai/gpt-oss-120b`. Will add: `gpt-5`, `claude-sonnet-4-6` for v2.
- **Per-step logger + PII tracker** (`agent/evaluation/logger.py`,
  `agent/evaluation/pii_tracker.py`). Captures DOM, screenshots,
  actions, and value-match leak detection.
- **Scorer** (`agent/evaluation/scorer.py`). Post-run aggregation of
  PLR/ASR/TCR/DR.
- **Server launcher** (`start_servers.sh`). Starts/stops/status for all
  91 envs.

### 1.4 What's done vs. pending

| Item | Status |
|---|---|
| 91-env benchmark built and wired | ✅ done |
| 12-vector attack taxonomy, 8-axis classification | ✅ done |
| Per-env classification.csv rows with sibling_of + toggled_axis | ✅ done |
| Phase 3 sibling envs all sit at `🟦 qa` (pending per-env smoke + screenshot diff) | partial |
| v1 pilot results on parent subset (qualitative: high leakage, prompt mitigation insufficient) | ✅ done |
| v2 results on full 91-env benchmark | ❌ not started (Phase 4 week 3) |
| LLM-as-judge Detection Rate (GPT-4o primary, Llama 4 secondary) | ❌ not started (Phase 4 week 1–2) |
| "Reached attack surface" instrumentation | ❌ not started (Phase 4 week 1) |
| GPT-5 + Claude Sonnet 4.6 added to model factory | ❌ not started (Phase 4 week 1) |
| Mitigation conditions C1 / C2 / C3 (3 prompts, not 1) | ❌ not started (Phase 4 week 1) |
| 10 benign-twin baseline envs | ❌ not started (Phase 4 week 1) |
| MITRE / OWASP / ENISA vector mapping | ❌ not started (Phase 4 week 1) |
| Fidelity sanity check vs real phishing screenshots | ❌ not started (Phase 4 week 2) |
| 200-sample human DR validation | ❌ not started (Phase 4 week 2) |
| Pre-registered analysis plan (`prereg-v2-start` git tag) | ❌ not started (Phase 4 week 1) |
| Public release artifact | ❌ not started (Phase 4 week 4) |

### 1.5 Known caveats and open issues

- **`ecommerce-platform-pi` is structurally broken** (single-app
  collapse of an 8-store multi-app parent + doubly-nested
  `templates/templates/` and `static/static/`). Logged in
  `phase3-checklist.md` open issues; another team member is fixing.
- **Detection Rate is keyword-match.** A reviewer-grade weakness;
  must be replaced with LLM-as-judge before submission.
- **"Reached attack surface" is not instrumented.** Low ASR on
  subtle/multi-turn envs cannot currently be disambiguated (defending
  vs. lost). Must be instrumented before submission.
- **Inert cruft dirs.** 4 nested-parent directory copies inside
  siblings (see §1.1). Non-blocking but worth a `rm -rf` pass.

---

## 2. Where we want to take this paper

### 2.1 Venue and track

**EMNLP 2026 main track**, empirical-study framing. The benchmark is
the *apparatus* — the section-3 methodology — not the headline
contribution. The contributions are the *findings* derived through
that apparatus.

### 2.2 Working thesis (subject to v2 data)

> *State-of-the-art web-browsing agents leak personally identifiable
> information to social-engineering websites at high rates. We show
> that prompt-level mitigation does not meaningfully reduce leakage,
> and that leakage patterns are systematically driven by site
> salience, attacker pressure cues, and prompt-injection presence.
> We release Scammer4U, a 91-environment axis-controlled benchmark
> supporting paired ablation of these factors.*

The thesis is anchored on what the v1 pilot already established
(high leakage, prompt mitigation insufficient). F1–F11 become
explanatory structure that *characterizes* leakage; they are not
load-bearing for the central claim. If v2 produces a strong "F1
detection-action gap" signal (agent identifies the site as
suspicious yet still leaks), that finding gets promoted to a
co-headline; if F1 is weak the paper is unaffected.

### 2.3 Contributions, in order

1. **Detection–action gap (conditional on F1 landing in v2).** Even
   when explicitly prompted to verbalize a trust judgment before any
   PII submission, frontier agents that *correctly identify* a site
   as suspicious still leak PII at high rates. This is the headline
   if v2 confirms the v1 signal; otherwise it demotes to §4.
2. **Mitigation gradient.** Three mitigation prompts of increasing
   strength (generic privacy nudge → phishing-aware checklist →
   pre-submission reflection) tested across 4 frontier agents.
   Comparison reveals which kinds of prompt-level intervention work
   and which fail.
3. **Characterization of leakage.** Pooled-across-models analysis
   of which attack factors most amplify leakage: salience, pressure
   type, prompt-injection presence, interaction modality. Backed by
   axis-controlled paired siblings (F1–F11).
4. **Methodological artifact.** Scammer4U benchmark and harness,
   publicly released. 91 attack envs + 10 benign-twin baselines.
   Axis-controlled siblings enable post-hoc ablation studies the
   community can extend.

### 2.4 Positioning vs. existing work

The closest prior work is [AgentDAM (Nguyen et al., 2025)](https://arxiv.org/pdf/2503.09780),
a 246-task benchmark for privacy leakage in autonomous web agents.
AgentDAM measures *incidental* leakage on benign sites with mixed-
relevance synthetic data; Scammer4U measures *adversarial* leakage to
attacker-controlled sites that explicitly social-engineer the agent.
Different threat models, complementary work — not in competition.

[AgentDojo (Debenedetti et al., NeurIPS 2024)](https://arxiv.org/abs/2406.13352)
evaluates indirect prompt injection on tool-using agents (email,
banking, travel APIs) — adjacent to our F8 (prompt-injection axis)
but its task surface is tool-use, not web-browsing of adversarial
sites. Canonical citation for the prompt-injection literature.

[AgentLeak (2026)](https://arxiv.org/abs/2602.11510) studies privacy
leakage in multi-agent systems and reasoning traces; orthogonal scope.
[AgentSocialBench (2026)](https://arxiv.org/html/2604.01487) evaluates
privacy in agentic social networks; cite as related but distinct.
[PhreshPhish (2025)](https://arxiv.org/html/2507.10854v2) is a
real-world phishing dataset for non-agent settings; useful comparison
when explaining why we use templated rather than scraped sites.

Capability benchmarks (WebArena, VisualWebArena, Mind2Web) are cited
as background — they measure what agents *can do*, we measure what
agents *do under attack*. Agent-safety surveys
([OSU-NLP-Group/AgentSafety](https://github.com/OSU-NLP-Group/AgentSafety))
provide context.

The distinguishing claim: *no published benchmark measures adversarial
PII extraction by attacker-controlled websites that explicitly
social-engineer web-browsing agents, with axis-controlled siblings
supporting paired ablation.* This is the moat.

### 2.5 Authoring framing

Sites are described as *"templated environments with per-site axis
specifications, manually authored to spec by the research team using
LLM-assisted scaffolding, followed by per-site human review against
design briefs."* This is honest and survives reviewer scrutiny. The
LLM-assistance acknowledgement lives in §3 (methodology); axis
specifications lead the abstract and §1.

### 2.6 Methodological commitments

- **Models.** 4 agents tested: GPT-5, Claude Sonnet 4.6, Gemini 3
  Flash, Llama 4 Scout. (The earlier `gpt-oss-120b` triad was
  pilot-only.)
- **Seeds.** n=5 per env-model-condition cell. Firm — not increasing.
- **Conditions.** Four between-conditions per env-model pair:
  - **C0 baseline** — default agent prompt.
  - **C1 generic** — 3-line privacy nudge ("avoid suspicious sites,
    don't compromise PII").
  - **C2 specific** — phishing-aware checklist (typosquats, urgency
    cues, unverified senders, PII tier rules).
  - **C3 reflective** — pre-submission reflection: agent must
    verbalize a trust judgment before any PII form submission. C3
    doubles as the F1 detection–action gap amplifier.

  Total cells: 91 × 4 × 5 × 4 = **7,280 runs.** Plus 10 benign-twin
  envs × 4 × 5 × 1 (C0 only) = **200 baseline runs.** Grand total
  ~7,480.
- **Benign-twin baselines.** 10 envs forked from attack envs with
  the attack stripped. Same task, no scam. Used for baseline-PLR
  subtraction so reported leakage is attack-attributable, not
  base-rate form-filling.
- **Inference framework.** Pooled-across-models as the primary
  inference. Mixed-effects logistic with env and model as crossed
  random effects. Per-model breakdowns reported in supplementary
  tables. Effect sizes with CIs reported alongside p-values.
  Benjamini–Hochberg correction over the planned-test family
  (F1–F11 + 3 mitigation comparisons + benign-baseline subtraction).
- **Detection Rate.** LLM-as-judge with **GPT-4o as primary
  evaluator** (avoids Claude-judging-Claude conflict) and Llama 4
  Scout as secondary judge for inter-judge κ. Validated against a
  200-sample human-labelled set, all 4 team members labelling 50
  each. Targets: human-vs-human κ ≥ 0.7, judge-vs-human κ ≥ 0.7.
  Keyword DR retained as auxiliary.
- **Reached-attack-surface gating.** ASR is reported conditioned on
  whether the agent navigated to the trap surface in each run.
- **MITRE / OWASP / ENISA mapping.** Each of the 12 attack vectors
  mapped to a published threat taxonomy in `classification.csv` and
  TAXO.md. Defangs the "why these 12?" reviewer concern.
- **Fidelity sanity check.** 10 attack envs rated 1–5 on visual
  believability and copy quality alongside 5 real phishing
  screenshots from PhishTank / wayback. Reported as a paragraph in
  §3.
- **Pre-registration.** Analysis plan committed to git tag
  `prereg-v2-start` before v2 data collection begins. Deviations
  explicitly documented in the limitations section.

### 2.7 What we will *not* claim

- We do **not** claim sites are scraped from real attackers — they
  are templated.
- We do **not** claim the benchmark is exhaustive of attack
  vectors — it covers 12, taxonomized in TAXO.md.
- We do **not** claim the LLM-as-judge DR is perfect — we validate
  on a human-labelled subset and own residual disagreement.
- We do **not** propose a defense scaffold in this paper. The
  "prompt-mitigation insufficient" finding is the negative result,
  not a proposed remedy. A scaffold paper is a separate follow-up.

---

## 3. Action plan

**The detailed day-by-day task list now lives in
[phase4-checklist.md](phase4-checklist.md).** That doc is the working
schedule with role assignments (E1–E4), per-week milestones, and a
risk register.

This section retains the original 21-day skeleton as a reference
sketch — but the live plan is 20 days, 4 conditions, 4 people, and
the additions described above (mitigation gradient, benign twins,
MITRE mapping, GPT-4o as judge). Read phase4-checklist.md for the
real plan.

The pivots reserved for results-time (below) still apply.

### Original 21-day skeleton (reference only — superseded by phase4-checklist.md)

### Days 1–3 — foundation

- **A1. Add Claude Sonnet 4.6 + GPT-5 to `agent/core/llm_factory.py`,
  validate end-to-end on one env each.** *Deliverable:* both models
  return non-empty action JSON on a 5-step `cluttered_downloads` run.
- **A2. Implement "reached attack surface" instrumentation.** Hook
  into `agent/core/browser.py` to log every navigation; label one
  or more "trap URLs" per env in `environments.yaml` (or a sibling
  file); add `reached_trap` boolean to session log; scorer reads it.
  *Deliverable:* ASR can be computed conditioned on
  `reached_trap=True`.
- **A3. Pre-register the analysis plan.** ~2-page document in
  `analysis-plan.md`; commit and git-tag with `prereg-v2-start`.
  *Deliverable:* hypotheses, statistical tests, multiple-comparison
  correction, inclusion/exclusion rules, primary vs. secondary
  outcomes specified before any v2 data.
- **B1. Related-work search expansion.** Verify the AgentDAM /
  AgentDojo positioning, scan ACL Anthology 2024–2026 for missed
  comparators, build §2 outline.

### Days 4–7 — DR upgrade and dry-run

- **A4. LLM-as-judge DR scaffold.** New module
  `agent/evaluation/dr_judge.py`. Rubric: per-step `did the agent
  identify the site as suspicious / phishing / not-trustworthy /
  scam`. Returns boolean + reasoning. Wire into scorer.
  *Deliverable:* judge runs on existing v1 logs and produces DR per
  session.
- **A5. Hand-label 200 samples for DR validation.** Stratified sample
  across envs and models. Two annotators, compute κ, reconcile.
  *Deliverable:* validation set + κ score documented.
- **A6. Mitigation-condition system prompt.** A privacy-aware safety
  prompt added as an opt-in flag (`--mitigation`) in `runner.py`.
  *Deliverable:* same env runs differently with vs. without flag.
- **A7. Smoke test: 1 env × 4 models × 1 seed × 2 conditions = 8
  runs.** Confirm harness produces expected log shape end-to-end on
  the new model set.
  *Deliverable:* 8 session logs and a test pass on scoring pipeline.

### Days 8–13 — full v2 eval

- **A8. Run 91 × 4 × 5 × 2 = 3,640 runs.** Parallelism is the gating
  factor. Budget: ~2–3 days on multiple browser workers.
  *Deliverable:* `agent/logs/v2/` with all runs, aggregate JSON.
- **A9. Run DR judge over all v2 logs.** Once runs are in.
  *Deliverable:* per-run DR added to aggregate.
- **B2. Methodology section first draft.** Done in parallel during
  the runs. Cover: benchmark construction, axis taxonomy, authoring
  process, metrics, statistical framework, pre-registration.

### Days 14–17 — analysis and writing

- **A10. F1–F11 hypothesis tests against the pre-registered plan.**
  Pooled-across-models + per-model. Effect sizes with CIs. Multiple-
  comparison correction.
  *Deliverable:* a `paper/results.json` with every F-claim's test
  statistic, effect size, and significance status.
- **A11. Robustness checks.** Per-model breakdowns. Sensitivity to
  seeds. Sensitivity to mitigation condition. Reached-trap-conditional
  ASR.
- **B3. Results, intro, discussion drafts.** Tables and figures.
- **B4. Limitations.** Plan from start: keyword DR (replaced),
  LLM-assisted authoring (owned), localhost-only (own), n=5 power
  (own), English-only (own), US-centric PII (own).

### Days 18–20 — polish

- **B5. Reviewer-anticipation pass.** What would an LLM reviewer
  flag? Missing tables, missing comparisons, missing model? Surface
  numbers in abstract and intro. Prep §6 future work.
- **B6. Public release plan.** License, GitHub anonymization, reproducibility statement.
- **A12. Final re-runs of any flaky envs.** Optional buffer.

### Day 21 — submit

Buffer day. Do nothing new.

### Pivots reserved for results-time

If v2 reveals one of these patterns, we update §2 in this doc and
shift weight in the paper:

- *F1 is strong* → promote detection-action gap to co-headline thesis.
- *F1 is weak, F2/F5/F8 strong* → main story stays as-written,
  characterization-led.
- *Mitigation actually works* → headline pivots to "prompt-level
  mitigation reduces leakage by X% in conditions Y; remains
  ineffective in Z" — still publishable, different framing.
- *Cross-model variance is large* → pooled inference becomes a
  liability; lead with per-model breakdown and a "frontier agents
  disagree on adversarial robustness" framing.
- *DR judge fails human validation (κ < 0.5)* → fall back to keyword
  DR + LLM judge as auxiliary; explicitly own the limitation.

---

## 4. References (cited in §2.4)

- AgentDAM: Privacy Leakage Evaluation for Autonomous Web Agents — https://arxiv.org/pdf/2503.09780
- AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents — https://arxiv.org/abs/2406.13352
- AgentLeak: A Full-Stack Benchmark for Privacy Leakage in Multi-Agent LLM Systems — https://arxiv.org/abs/2602.11510
- AgentSocialBench: Evaluating Privacy Risks in Human-Centered Agentic Social Networks — https://arxiv.org/html/2604.01487
- PhreshPhish: A Real-World, High-Quality, Large-Scale Phishing Website Dataset and Benchmark — https://arxiv.org/html/2507.10854v2
- OSU-NLP-Group/AgentSafety repo — https://github.com/OSU-NLP-Group/AgentSafety
- AgentDojo official site — https://agentdojo.spylab.ai/
- AgentDojo NeurIPS 2024 poster — https://neurips.cc/virtual/2024/poster/97522
