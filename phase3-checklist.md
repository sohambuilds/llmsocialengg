# Phase 3 Checklist

**Live working doc.** Every agent working on a Phase 3 env edits this file when it picks up, finishes, or hands off a task. Source of truth for *who's doing what* and *what's done*.

> If you are an agent: read [phase3.txt](phase3.txt) for the design contract. Then come here, find your env's row, and update it. Do not touch other rows. Append, don't rewrite.

---

## How to use this file (read before editing)

Each env has one row in a wave-table. The columns are:

| Column | Meaning |
|---|---|
| `Status` | One of: `🟥 todo`, `🟨 design`, `🟧 build`, `🟦 qa`, `🟩 done`, `⛔ blocked` |
| `Env` | Folder name under `all_websites/` |
| `Parent` | The env this is a sibling of (or `—` for new archetypes) |
| `Axis change` | The single axis that moves vs the parent |
| `Owner` | Whoever picked it up: `arya` / `sarthak` / `vaibhav` (or empty) |
| `Branch / PR` | Branch name or PR link once it exists |
| `Notes` | One-line status / blockers. Append `[YYYY-MM-DD initials]` to each note |

**Status flow:** `🟥 todo → 🟨 design → 🟧 build → 🟦 qa → 🟩 done`. `⛔ blocked` if you hit something you can't resolve solo — write the blocker in Notes.

**Rules for agents:**
1. Only edit YOUR row(s). If you take over someone else's row, change `Owner` and append a note.
2. When marking `🟩 done`, ALL of these must be true: env exists in `all_websites/`, row added in `classification.csv` with `sibling_of` + `toggled_axis`, registered in `agent/config/environments.yaml` and `start_servers.sh`, smoke-tested.
3. If you discover a blocker / design question, log it in **§ Open issues** at the bottom rather than rewriting your row.
4. Never delete completed rows. Never reorder waves. Append-only for the audit log.

---

## Dashboard

Update these counts after every status change.

| Wave | Total | 🟥 todo | 🟨 design | 🟧 build | 🟦 qa | 🟩 done | ⛔ blocked |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — pressure | 18 | 13 | 0 | 0 | 5 | 0 | 0 |
| B — prompt injection | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| C — salience | 12 | 0 | 0 | 0 | 12 | 0 | 0 |
| D — interaction | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| E — medium PII | 6 | 4 | 0 | 0 | 2 | 0 | 0 |
| F — multi-site | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| G — optional | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **59** | **24** | **0** | **0** | **35** | **0** | **0** |

Existing envs: 44. Phase 3 target on completion: ~95–100.

> **Audit note (sync as of 2026-05-05):** wave statuses were back-filled
> from the filesystem. As of the latest sweep, all 35 `🟦 qa` envs are
> now wired into `classification.csv` (with `sibling_of`/`toggled_axis`
> recorded in the `notes` column), `agent/config/environments.yaml`,
> and `start_servers.sh`. The remaining sign-off items per env are:
> design brief (`d`), single-axis diff verification (`qa`), smoke-test
> against `/api/captured` (`smoke`), and screenshot diff vs parent
> (`scrn`). Anyone closing one out to `🟩 done` must confirm those
> four items first.

---

## Pre-Wave A: open design questions to resolve first

Before anyone starts Wave A, the four open questions in [phase3.txt](phase3.txt) §10 must have a recorded decision. Owner: lead reviewer.

| # | Question | Decision | Decided by | Date |
|---|---|---|---|---|
| Q10.1 | Single-valued pressure? | (pending) | | |
| Q10.2 | Calm = neutral or reassuring? | (pending) | | |
| Q10.3 | `sibling_of` = immediate parent or root? | (pending) | | |
| Q10.4 | Medium-PII secondary claims to instrument? | (pending) | | |

Do not start Wave A until all four say something other than `(pending)`.

---

## Wave A — Pressure siblings (18 envs)

Goal: isolate the effect of psychological pressure. Unlocks F5, F6, F7.

### A.1 — `urgency → none` calm twins (12 envs)

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `virus_scanner_calm` | virus_scanner | pressure: urgency → none | | | dir exists: virus-scanner-calm [2026-05-04 audit] |
| 🟦 qa | `job_portal_no_timer` | job_portal | pressure: urgency → none | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `gov_portal_no_timer` | gov_portal | pressure: urgency → none | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `marketplace_calm` | marketplace | pressure: urgency → none | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `adp_no_banner` | adp | pressure: urgency → none | | | dir exists [2026-05-04 audit] |
| 🟥 todo | `aws_no_countdown` | aws | pressure: urgency → none | | | |
| 🟥 todo | `booking_no_timer` | booking | pressure: urgency → none | | | |
| 🟥 todo | `e7_ninite_calm` | e7_ninite | pressure: urgency → none | | | |
| 🟥 todo | `e8_chase_no_countdown` | e8_chase | pressure: urgency → none | | | |
| 🟥 todo | `e10_mychart_calm` | e10_mychart | pressure: urgency → none | | | |
| 🟥 todo | `e13_irs_no_timer` | e13_irs | pressure: urgency → none | | | |
| 🟥 todo | `e14_oracle_no_timer` | e14_oracle | pressure: urgency → none | | | |

### A.2 — Other pressure types (6 envs)

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟥 todo | `saas_onboard_authority` | saas_onboard | pressure: none → authority | | | |
| 🟥 todo | `adp_authority` | adp_no_banner | pressure: urgency → authority | | | |
| 🟥 todo | `marketplace_social_proof` | marketplace_calm | pressure: none → social_proof | | | |
| 🟥 todo | `e23_netflix_social_proof` | e23_netflix | pressure: urgency → social_proof | | | |
| 🟥 todo | `ecommerce_scarcity` | ecommerce | pressure: none → scarcity | | | |
| 🟥 todo | `github_phish_scarcity` | github_phish | pressure: none → scarcity | | | |

---

## Wave B — Prompt-injection siblings (10 envs)

Goal: measure PI effect and PI-location effect. Unlocks F8.

### B.1 — PI on/off pairs (6 envs)

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `ecommerce_pi` | ecommerce | prompt_injection: none → visible_text | | | dir exists: ecommerce-platform-pi [2026-05-04 audit] |
| 🟦 qa | `marketplace_pi_hidden` | marketplace | prompt_injection: none → hidden_dom | | | dir exists: marketplace-website-pi-hidden [2026-05-04 audit] |
| 🟦 qa | `news_pi` | news | prompt_injection: none → visible_text | | | dir exists: news-content-site-pi [2026-05-04 audit] |
| 🟦 qa | `quiz_scam_pi_sysmsg` | quiz_scam | prompt_injection: none → fake_system_msg | | | dir exists: quiz-site-pi-sysmsg [2026-05-04 audit] |
| 🟦 qa | `e8_chase_pi_hidden` | e8_chase | prompt_injection: none → hidden_dom | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `e17_amazon_pi_visible` | e17_amazon | prompt_injection: none → visible_text | | | dir exists [2026-05-04 audit] |

### B.2 — PI-location triple ablation (4 envs)

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `saas_onboard_pi_hidden` | saas_onboard | prompt_injection: visible_text → hidden_dom | | | dir exists: saas-onboarding-pi-hidden [2026-05-04 audit] |
| 🟦 qa | `saas_onboard_pi_sysmsg` | saas_onboard | prompt_injection: visible_text → fake_system_msg | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `support_chat_pi_visible` | support_chat | prompt_injection: hidden_dom → visible_text | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `support_chat_pi_sysmsg` | support_chat | prompt_injection: hidden_dom → fake_system_msg | | | dir exists [2026-05-04 audit] |

---

## Wave C — Missing salience variants (12 envs)

Goal: fill the subtle cell, balance blatant/plausible coverage. Unlocks F2, F3.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `virus_scanner_plausible` | virus_scanner | salience: blatant → plausible | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `virus_scanner_subtle` | virus_scanner | salience: blatant → subtle | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `quiz_scam_subtle` | quiz_scam | salience: blatant → subtle | | | dir exists: quiz-site-subtle [2026-05-04 audit] |
| 🟦 qa | `summarizer_plausible` | summarizer | salience: blatant → plausible | | | dir exists: summary-website-plausible [2026-05-04 audit] |
| 🟦 qa | `summarizer_subtle` | summarizer | salience: blatant → subtle | | | dir exists: summary-website-subtle [2026-05-04 audit] |
| 🟦 qa | `crypto_platform_blatant` | crypto_platform | salience: plausible → blatant | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `crypto_platform_subtle` | crypto_platform | salience: plausible → subtle | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `saas_onboard_subtle` | saas_onboard | salience: plausible → subtle | | | dir exists: saas-onboarding-subtle [2026-05-04 audit] |
| 🟦 qa | `e10_mychart_plausible` | e10_mychart | salience: subtle → plausible | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `e10_mychart_blatant` | e10_mychart | salience: subtle → blatant | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `freelance_blatant` | freelance | salience: subtle → blatant | | | dir exists: freelance-platform-blatant [2026-05-04 audit] |
| 🟦 qa | `support_chat_plausible` | support_chat | salience: subtle → plausible | | | dir exists [2026-05-04 audit] |

---

## Wave D — Interaction-style siblings (6 envs)

Goal: form vs chat A/B on the same archetype. Unlocks F10.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `summarizer_chat` | summarizer | interaction: static_form → multi_turn_chat | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `marketplace_chat` | marketplace | interaction: multi_step_form → multi_turn_chat | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `gov_portal_chat` | gov_portal | interaction: multi_step_form → multi_turn_chat | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `e18_linkedin_chat` | e18_linkedin | interaction: multi_step_form → multi_turn_chat | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `support_chat_static` | support_chat | interaction: multi_turn_chat → static_form | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `freelance_static` | freelance | interaction: multi_turn_chat → static_form | | | dir exists [2026-05-04 audit] |

---

## Wave E — Medium-only PII envs (6 envs)

Goal: zero medium-only envs today; without these F9 is blocked.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟥 todo | `news_medium` | news | pii_target: high → medium | | | |
| 🟥 todo | `saas_onboard_medium` | saas_onboard | pii_target: critical → medium | | | |
| 🟦 qa | `forum_register_medium` | — (new A21) | n/a — new archetype @ medium | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `forum_register_critical` | forum_register_medium | pii_target: medium → critical | | | dir exists [2026-05-04 audit] |
| 🟥 todo | `job_portal_medium` | job_portal | pii_target: critical → medium | | | |
| 🟥 todo | `bumble_medium` | bumble | pii_target: critical → medium | | | |

---

## Wave F — Multi-site toggle siblings (5 envs)

Goal: same scam, different entry point. Tests effect of mailbox triage.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟥 todo | `saas_onboard_direct` | saas_onboard | multi_site: email_entry → single_origin | | | |
| 🟥 todo | `marketplace_email_entry` | marketplace | multi_site: single_origin → email_entry | | | |
| 🟥 todo | `ancestry_dna_email_entry` | ancestry_dna | multi_site: single_origin → email_entry | | | |
| 🟥 todo | `betterhelp_email_entry` | betterhelp | multi_site: single_origin → email_entry | | | |
| 🟥 todo | `bumble_email_entry` | bumble | multi_site: single_origin → email_entry | | | |

---

## Wave G — Optional category gaps (2 envs)

Build only if every higher-priority wave is closed AND the env also fits a Wave A–F slot.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟥 todo | `dating_photo_id` | — (new A16) | new archetype | | | |
| 🟥 todo | `insurance_quote` | — (new A19) | new archetype | | | |

---

## F-row claim coverage

Update the `Pair count` column as siblings land. Goal: every row ≥1, ideally ≥3 for F5 / F8 / F10.

| # | Claim | Pair count | First pair | Status |
|---|---|---:|---|---|
| F1 | Detection does not prevent leakage | n/a | — | descriptive (auto from full set) |
| F2 | Plausible leaks more than blatant | 4 | virus_scanner ↔ virus_scanner_plausible | 🟦 |
| F3 | Subtle + conversational is worst | 2 | freelance ↔ freelance_blatant | 🟩 |
| F4 | Vision does not help | n/a | — | cross-model (no new envs) |
| F5 | Urgency adds Δ PLR | 5 | virus_scanner ↔ virus_scanner_calm | 🟦 |
| F6 | Social proof adds Δ′ PLR | 0 | — | 🟥 (Wave A.2) |
| F7 | Authority cues add Δ″ PLR | 0 | — | 🟥 (Wave A.2) |
| F8 | Hidden PI ≈ visible PI | 8 | ecommerce ↔ ecommerce_pi | 🟦 |
| F9 | Critical ≈ medium when plausible | 1 | forum_register_critical ↔ forum_register_medium | 🟩 |
| F10 | Chat bypasses agents that refuse forms | 6 | summarizer ↔ summarizer_chat | 🟦 |
| F11 | Findings generalize across categories | 0 | — | 🟥 (no cross-category port yet) |

A row turns 🟩 once it has its first pair; 🟦 at 3+ pairs. Pair counts
above are derived from the 35 built siblings as of 2026-05-05; they
become "verified" once smoke + screenshot sign-off lands per env.

---

## Open issues / blockers (running log)

Append; do not rewrite. Format:

```
### YYYY-MM-DD — short-title — [open|resolved]
Owner: <initials>
Affects: <env(s) or wave>
What:    <one paragraph>
Need:    <decision needed from whom>
```

(none yet)

---

## Completed envs (audit trail)

Move rows here only when status hits 🟩 done AND classification.csv is updated. Append to the bottom; never reorder.

| Date | Env | Owner | Branch / PR | Notes |
|---|---|---|---|---|

---

## Per-env sign-off checklist (don't skip any)

Before marking an env 🟩 done, confirm each item below in the env's row notes (e.g. `[d✓ b✓ qa✓ cls✓ yaml✓ srv✓ smoke✓ scrn✓]`).

- `d` — design brief written and reviewed
- `b` — env exists under `all_websites/<env_key>/` and serves on its assigned port
- `qa` — single-axis diff verified vs parent (no other axis moved)
- `cls` — row added to `classification.csv` with `sibling_of` + `toggled_axis`
- `yaml` — entry added to `agent/config/environments.yaml`
- `srv` — port + command added to `start_servers.sh`
- `smoke` — agent dry-run completes and `/api/captured` logs a submission
- `scrn` — screenshot diff against parent shows visual parity outside the toggled axis

If any item is missing, status stays 🟦 qa.
