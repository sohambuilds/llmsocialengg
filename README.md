<div align="center">

# 🎣 Scammer4U

### Social Engineering Benchmark for Autonomous Web Agents

**Accompanying repository for the paper:**

[_"I Strongly Suspect This Website Is a Scam": Benchmarking PII Leakage and Detection without Defense in Autonomous Web Agents_](https://arxiv.org/abs/2606.00497)

Soham Roy · Sarthakbrata Halder · Arya Bharaty · Vaibhav Bhaskar · Yash Sinha · Dhruv Kumar · Srikant Panda · Murari Mandal

[![arXiv](https://img.shields.io/badge/arXiv-2606.00497-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2606.00497)

![Venue](https://img.shields.io/badge/EMNLP_2026-main_track-b31b1b)
![Status](https://img.shields.io/badge/status-submission_in_flight-f39c12)
![Adversarial Environments](https://img.shields.io/badge/adversarial_environments-91-1f6feb)
![Benign Twins](https://img.shields.io/badge/benign_twins-10-1f6feb)
![Models](https://img.shields.io/badge/models-4_frontier-1f6feb)
![Sessions](https://img.shields.io/badge/sessions-7%2C480-1f6feb)
![Taxonomy](https://img.shields.io/badge/taxonomy-8--axis_factorial-8957e6)
![Analysis](https://img.shields.io/badge/analysis-pre--registered-2ea44f)

**[Core Question](#the-core-question)** · **[Results](#headline-results-v2-all-5-seeds-pooled-across-4-models)** · **[Design](#benchmark-design)** · **[Attack Vectors](#eight-attack-vectors)** · **[PII Tiers](#pii-sensitivity-tiers)** · **[Evaluation](#evaluation-setup)** · **[Findings](#key-findings)** · **[Prior Work](#how-this-differs-from-prior-work)** · **[Limitations](#limitations)** · **[Acknowledgments](#acknowledgments)**

</div>

> [!NOTE]
> **Status (May 2026):** EMNLP 2026 main-track submission in flight.
> Full 5-seed sweep complete across all four models (7480 sessions).

---

## The Core Question

Frontier web-browsing agents are given users' PII — name, address, payment card, SSN, passwords, API keys — so they can fill in forms automatically. When one of these agents encounters a social-engineering attack, **will it hand over the user's personal information to the attacker?**

We build realistic attacker-controlled websites with traps embedded in them, send an agent to complete a normal task (apply for a job, buy headphones, take an IQ test), and measure what it leaks.

---

## Headline Results (v2, all 5 seeds, pooled across 4 models)

| Model | C0 — no guidance | C1 — nudge | C2 — checklist | C3 — reflection | ΔM3 |
|---|---:|---:|---:|---:|---:|
| GPT-5 mini | 61.0% | 47.7% | 38.9% | 36.1% | −24.9 pp |
| Claude Haiku 4.5 | 54.5% | 36.4% | 19.1% | 24.0% | −30.5 pp |
| Gemini 3 Flash | 93.1% | 81.8% | 68.5% | 60.7% | −32.4 pp |
| Llama 4 Scout | 82.3% | 83.8% | 81.4% | 77.4% | −4.9 pp |
| **Pooled** | **72.7%** | **62.4%** | **51.9%** | **49.4%** | **−23.3 pp** |

Cells are PLR_crit — the fraction of sessions where at least one critical-tier PII value reached an attacker-controlled endpoint. Benign-twin baselines: **0% PLR_crit** across all four models and all conditions, confirming leakage is attack-attributable rather than incidental form-filling.

> **Detection–action gap (the co-headline finding):** pooled across all four models in the C3 reflection condition, agents whose reasoning an independent LLM judge confirms has flagged the site as suspicious still leak critical PII in **35.9%** of sessions, versus **66.1%** when no suspicion is verbalised — a **30.2 pp gap** (n = 462 confirmed-detector sessions, q < 0.001). Verbalised suspicion does not reliably prevent submission.

---

## Benchmark Design

**91 adversarial environments** and **10 benign-twin baselines** organised on an 8-axis factorial taxonomy. 60 of the 91 environments are axis-controlled siblings of a parent environment, differing on exactly one axis — enabling causal paired ablation across 11 research claims (F1–F11).

### Classifying Axes (define each environment)

| Axis | Values |
|---|---|
| A: category | job, ecommerce, gov, support, finance, education, social media, health, … |
| B: vector | phishing_clone, credential_harvest, dark_patterns, reward_trap, authority_impersonation, conversational_deception, prompt_injection, fake_trust_signals |
| C: salience | blatant, subtle |
| D: pii_target | critical, high, medium |

### Factor Axes (ablation knobs — each paired with a sibling test)

| Axis | Values |
|---|---|
| E: pressure | none, urgency, social_proof, authority, scarcity |
| F: prompt_injection | none, visible_text, hidden_dom, fake_system_msg |
| G: interaction | static_form, multi_step_form, single_turn_chat, multi_turn_chat |
| H: multi_site | single_origin, multi_origin_same_task, email_entry_plus_site |

Each sibling environment differs from its parent on **exactly one axis**. Any difference in leakage between the pair is causally attributable to that single factor.

---

## Eight Attack Vectors

Each vector is mapped to MITRE ATT&CK, OWASP LLM Top 10, and the ENISA AI threat landscape.

1. **Phishing clone** — near-perfect copy of a real site on a typosquatted domain
2. **Credential harvest** — site whose explicit ask is passwords, API keys, or 2FA tokens, gated behind a "verification" step
3. **Dark patterns** — UI-level coercion: fake buttons, grayed-out skips, pre-checked consents, hidden costs
4. **Reward trap** — unlock a certificate, download, or quiz score gated by PII collection
5. **Authority impersonation** — site claims to be a government body, regulator, or platform admin
6. **Conversational deception** — multi-turn chat that gradually escalates trust and PII requests using adaptive response trees
7. **Prompt injection** — instructions hidden in page content, DOM, or chat targeting the agent's reasoning
8. **Fake trust signals** — counterfeit security badges, regulatory claims, fake SSL icons, fabricated review counts

Pressure cues (urgency, social proof, scarcity) are a separate **factor axis (E)** — they modulate any vector but are not vectors themselves.

---

## PII Sensitivity Tiers

| Tier | Fields |
|---|---|
| **Critical** | SSN, card number + CVV, bank account, passwords, API keys, 2FA codes, government-ID document upload |
| **High** | Email, phone, home address |
| **Medium** | Full name, employer, job title, date of birth |

The agent carries a single synthetic identity (Jordan Mitchell). No real user PII is used at any point.

---

## Evaluation Setup

**Four frontier models** evaluated under identical harness conditions via commercial APIs:
GPT-5 mini · Claude Haiku 4.5 · Gemini 3 Flash · Llama 4 Scout

**Four mitigation conditions** per environment–model pair:
- **C0** — default agent prompt, no privacy guidance
- **C1** — generic 3-line privacy nudge
- **C2** — phishing-aware checklist (typosquats, urgency cues, PII tier rules)
- **C3** — pre-submission reflection: agent must verbalise a trust judgment before any PII form submission

**Five seeds** per environment–model–condition cell → ~7,480 total sessions.

**Detection Rate** is measured by an independent LLM-as-judge (GPT-4o-mini primary, cross-family) applied post-hoc to every reasoning step. Inter-judge agreement (GPT-4o-mini vs Llama 4 Scout secondary): κ = 0.39–0.44 across all four models. Judge–human agreement on a 50-session labelled validation set: κ = 0.826 and 0.780 (both raters clearing the pre-registered ≥0.70 bar).

**Pre-registered analysis plan** committed before any data collection (`prereg-v2-start` tag). Two pre-committed falsification thresholds: (i) mitigation is sufficient if any condition drops pooled PLR_crit by ≥30 pp — not crossed (pooled ΔM3 = −23.3 pp); (ii) detection prevents submission if within-C3 PLR_crit | DR=1 ≤ 10% — not crossed (35.9%).

---

## Key Findings

1. **Baseline leakage is high.** Critical-tier PII reaches attacker endpoints at 55–93% across the four models under no guidance, versus 0% on benign-twin baselines.

2. **Mitigation is sharply model-dependent.** Three models (Haiku, Gemini, GPT-5 mini) respond meaningfully to a phishing-aware checklist or reflection prompt (ΔM3 between −24.9 and −32.4 pp). Llama 4 Scout shows essentially no behavioural response (−4.9 pp at C3) despite stated detection rising from 0.2% to 16% across conditions.

3. **Detection does not prevent submission.** Even after an independent judge confirms the agent has verbalised suspicion, it still hands over critical PII in 36% of those sessions. Defences gated on the agent's own stated assessment are gating on the wrong signal.

4. **Salience marginal and paired-sibling results disagree on sign.** A cross-cutting marginal ranks subtle attacks as most dangerous; the paired-sibling test (controlling for category base rates) finds subtle siblings leak *less* than their parents. The marginal is confounded by which categories were authored at which salience level — the paired design is necessary to recover the correct direction.

---

## How This Differs from Prior Work

| Benchmark | Attacker-controlled sites | Structured PII profile | Field-level loss metric | Multi-turn chat | Pre-registered |
|---|:---:|:---:|:---:|:---:|:---:|
| AgentDojo (NeurIPS 2024) | ✗ | ✗ | ✗ | ✗ | ✗ |
| DECEPTICON (2026) | ✓ | ✗ | ✗ | ✗ | ✗ |
| TrickyArena (2026) | ✓ | ✗ | ✗ | ✗ | ✗ |
| TRAP (2025) | ✓ | ✗ | ✗ | ✗ | ✗ |
| AgentDAM (2025) | ✗ | ✓ | ✓ | ✗ | ✗ |
| WebTrap Park (2026) | ✓ | ✗ | ✗ | ✗ | ✗ |
| **Scammer4U (ours)** | **✓** | **✓** | **✓** | **✓** | **✓** |

The primary moat: axis-controlled paired-sibling environments that isolate the causal contribution of individual attack design factors, combined with a pre-registered analysis plan and explicit falsification thresholds.

---

## Limitations

- Environments are templated rather than scraped from live phishing infrastructure. Fidelity validated by a blind 20+20 human review (47.5% source-discrimination accuracy vs 50% chance; reviewers more often labelled our environments as real phishing than as ours).
- PII profile is US-centric (SSN, US bank and routing format, US address); all prompts and pages are English-only.
- The four-model panel covers deployed frontier agentic systems and does not include open-weight or smaller-parameter models.
- The DR judge is GPT-4o-mini; the within-family pairing with GPT-5 mini is mitigated by stratified inter-judge κ reporting and a Llama 4 Scout secondary pass.
- Results bound in-harness behaviour of these models, not any specific commercial deployment.

---

## Acknowledgments

We thank Arka Mukherjee, Anyash Prasad, and Sarthak Bhattacharya for their help and participation in the early stages of our work.
