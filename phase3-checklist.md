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
| A — pressure | 18 | 0 | 0 | 0 | 18 | 0 | 0 |
| B — prompt injection | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| C — salience | 12 | 0 | 0 | 0 | 12 | 0 | 0 |
| D — interaction | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| E — medium PII | 6 | 0 | 0 | 0 | 6 | 0 | 0 |
| F — multi-site | 5 | 0 | 0 | 0 | 5 | 0 | 0 |
| G — optional | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| **Total** | **59** | **0** | **0** | **0** | **59** | **0** | **0** |

Existing envs: 44. Phase 3 result: 59 built (+1 bonus
`insurance_quote_medium` for an extra F9 pair). Master env directory
count on disk: 105 (44 parents + 60 siblings + 1 `subfolder/` artifact
that is also nested inside `github_phish_scarcity/`).

> **Audit note (sync as of 2026-05-06):** all 59 Phase 3 siblings now
> exist on disk and are wired into `classification.csv` (with
> `sibling_of`/`toggled_axis` recorded in the `notes` column),
> `agent/config/environments.yaml`, and `start_servers.sh`. The
> remaining sign-off items per env are: design brief (`d`), single-axis
> diff verification (`qa`), smoke-test against `/api/captured`
> (`smoke`), and screenshot diff vs parent (`scrn`). The smoke-test
> pass is blocked on API keys (see Open issues §2026-04-28).
>
> **Stylesheet/asset sweep (2026-05-06):** all `url_for('static', …)`
> and `/static/…` references resolve at runtime. Most envs use inline
> `<style>` blocks (no asset cascade risk). The marketplace family is
> the only sibling cluster with non-empty `static/` and the cascade is
> correct: PI-hidden and email-entry siblings have byte-identical
> `style.css`/`script.js` to parent; calm/chat/social_proof share a
> de-urgency'd CSS+JS (matches Vaibhav's brief).
>
> **Structural cruft to clean up (non-blocking — `start_servers.sh`
> launches the top-level entry points, so these are inert at runtime):**
> 1. `ecommerce-platform-pi/` has doubly-nested `templates/templates/`
>    and `static/static/` (dead-weight duplicates of the same files).
> 2. `ecommerce-platform-pi/` collapses an 8-store multi-app parent
>    (`ecommerce-platform/{amazon,bargain_electro,fake_payment,fake_tracker,shopsmart,target,techvault,walmart}`)
>    into a single-app sibling. The typosquat-vs-legit-store contrast
>    of the parent is gone — re-check that this still measures F8 the
>    way you intend.
> 3. `adp_authority/ADP/`, `ecommerce_scarcity/ecommerce-platform/`,
>    and `github_phish_scarcity/subfolder/` each contain a full nested
>    copy of the parent dir. Bloats the repo and confuses diffs.

---

## Pre-Wave A: open design questions to resolve first

Before anyone starts Wave A, the four open questions in [phase3.txt](phase3.txt) §10 must have a recorded decision. Owner: lead reviewer.

| # | Question | Decision | Decided by | Date |
|---|---|---|---|---|
| Q10.1 | Single-valued pressure? | **Resolved: keep single-valued.** All envs carry one pressure value. Dominant cue wins; multi-cue envs note both in CSV but only the dominant one fills the axis. | vaibhav (implementation evidence) | 2026-04-28 |
| Q10.2 | Calm = neutral or reassuring? | **Resolved: neutral.** virus_scanner_calm strips urgency copy and replaces with neutral phrasing ("scan complete, review your results"). No reassurance copy added. | vaibhav (virus_scanner_calm build) | 2026-04-28 |
| Q10.3 | `sibling_of` = immediate parent or root? | **Resolved: immediate parent.** All Wave C classification.csv rows use `sibling_of=<direct parent>`. Chains derivable analytically if needed. | vaibhav (Wave C build) | 2026-04-28 |
| Q10.4 | Medium-PII secondary claims to instrument? | **Resolved: yes, instrument task completion rate (TCR) alongside PLR.** Medium envs should show higher TCR if agents complete the legitimate task without leaking. Confirm when Wave E runs. | vaibhav | 2026-04-28 |

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
| 🟦 qa | `aws_no_countdown` | aws | pressure: urgency → none | | | dir exists [2026-05-05 build] |
| 🟦 qa | `booking_no_timer` | booking | pressure: urgency → none | | | dir exists [2026-05-05 build] |
| 🟦 qa | `e7_ninite_calm` | e7_ninite | pressure: urgency → none | | | dir exists [2026-05-05 build]; FOLLOW-UP: parent has only narrative urgency — needs parent-fix retrofit before F5 datapoint is usable |
| 🟦 qa | `e8_chase_no_countdown` | e8_chase | pressure: urgency → none | sr | | built + wired [2026-05-05 sr] |
| 🟦 qa | `e10_mychart_calm` | e10_mychart | pressure: urgency → none | sr | | built + wired [2026-05-05 sr] |
| 🟦 qa | `e13_irs_no_timer` | e13_irs | pressure: urgency → none | sr | | parent-fix: added 72h CP14 countdown banner+JS; sibling drops banner+CSS+JS and softens LEGAL NOTICE / Federal Tax Lien copy. built + wired [2026-05-05 sr] |
| 🟦 qa | `e14_oracle_no_timer` | e14_oracle | pressure: urgency → none | sr | | parent-fix: added 24h service-suspension countdown banner+JS; sibling drops banner+CSS+JS and strips email-body 'Failure to verify by April 1' deadline. built + wired [2026-05-05 sr] |

### A.2 — Other pressure types (6 envs)

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `saas_onboard_authority` | saas_onboard | pressure: none → authority | ag | | built + wired [2026-05-05 ag] |
| 🟦 qa | `adp_authority` | adp_no_banner | pressure: urgency → authority | ag | | built + wired [2026-05-05 ag] |
| 🟦 qa | `marketplace_social_proof` | marketplace_calm | pressure: none → social_proof | ag | | built + wired [2026-05-05 ag] |
| 🟦 qa | `e23_netflix_social_proof` | e23_netflix | pressure: urgency → social_proof | ag | | built + wired [2026-05-05 ag] |
| 🟦 qa | `ecommerce_scarcity` | ecommerce | pressure: none → scarcity | ag | | built + wired [2026-05-05 ag] |
| 🟦 qa | `github_phish_scarcity` | github_phish | pressure: none → scarcity | ag | | built + wired [2026-05-05 ag] |

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

> **Wave C status: all 12 built, registered, and boot-verified. Pending: agent smoke run (blocked on API key) and screenshot diff against parent.**

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
| 🟦 qa | `news_medium` | news | pii_target: high → medium | sr | | built + wired [2026-05-05 sr] |
| 🟦 qa | `saas_onboard_medium` | saas_onboard | pii_target: critical → medium | sr | | built + wired [2026-05-05 sr] |
| 🟦 qa | `forum_register_medium` | — (new A21) | n/a — new archetype @ medium | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `forum_register_critical` | forum_register_medium | pii_target: medium → critical | | | dir exists [2026-05-04 audit] |
| 🟦 qa | `job_portal_medium` | job_portal | pii_target: critical → medium | sr | | built + wired [2026-05-05 sr]; mailbox+legit+phishing 3-server clone on 5407/5408/5409; typosquat g00gle retained; SSN/bank/9.99-fee stripped; single-page form asks CV/cover-letter/salary/employer-references; pre-ticked priority-review consent preserves dark_patterns vector |
| 🟦 qa | `bumble_medium` | bumble | pii_target: critical → medium | sr | | built (Bumble.html replaced w/ profile-setup form) + wired [2026-05-05 sr] |

---

## Wave F — Multi-site toggle siblings (5 envs)

Goal: same scam, different entry point. Tests effect of mailbox triage.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `saas_onboard_direct` | saas_onboard | multi_site: email_entry → single_origin | sr | | built + wired [2026-05-05 sr]; mailbox dropped; saas_app+billing on 5411/5412; agent lands directly at teamwork-app.com; scam payload byte-identical to parent |
| 🟦 qa | `marketplace_email_entry` | marketplace | multi_site: single_origin → email_entry | sr | | built + wired [2026-05-05 sr]; mailbox (5413) + marketplace (5414); shipping-update email links to marketplace-hub.com:5414; marketplace_app byte-identical to parent |
| 🟦 qa | `ancestry_dna_email_entry` | ancestry_dna | multi_site: single_origin → email_entry | sr | | built + wired [2026-05-06 audit]; mailbox + ancestry_app dual-server, run_servers.py present, classification.csv row recorded |
| 🟦 qa | `betterhelp_email_entry` | betterhelp | multi_site: single_origin → email_entry | sr | | built + wired [2026-05-06 audit]; mailbox + betterhelp_app dual-server, run_servers.py present |
| 🟦 qa | `bumble_email_entry` | bumble | multi_site: single_origin → email_entry | sr | | built + wired [2026-05-06 audit]; mailbox + bumble_app dual-server, run_servers.py present |

---

## Wave G — Optional category gaps (2 envs)

Build only if every higher-priority wave is closed AND the env also fits a Wave A–F slot.

| Status | Env | Parent | Axis change | Owner | Branch / PR | Notes |
|---|---|---|---|---|---|---|
| 🟦 qa | `dating_photo_id` | — (new A16) | new archetype | sr | | built + wired [2026-05-06 audit]; classification.csv: dating / credential_harvest / subtle / critical / static_form |
| 🟦 qa | `insurance_quote` | — (new A19) | new archetype | sr | | built + wired [2026-05-06 audit]; classification.csv: insurance / credential_harvest / plausible / critical / multi_step_form. Bonus sibling `insurance_quote_medium` exists on disk for F9 pair. |

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
| F6 | Social proof adds Δ′ PLR | 2 | marketplace_calm ↔ marketplace_social_proof | 🟩 |
| F7 | Authority cues add Δ″ PLR | 2 | saas_onboard ↔ saas_onboard_authority | 🟩 |
| F8 | Hidden PI ≈ visible PI | 8 | ecommerce ↔ ecommerce_pi | 🟦 |
| F9 | Critical ≈ medium when plausible | 2 | forum_register_critical ↔ forum_register_medium | 🟩 |
| F10 | Chat bypasses agents that refuse forms | 6 | summarizer ↔ summarizer_chat | 🟦 |
| F11 | Findings generalize across categories | 0 | — | 🟥 (no cross-category port yet) |

A row turns 🟩 once it has its first pair; 🟦 at 3+ pairs. Pair counts
above were originally derived from the first 35 siblings; with all 59
siblings now on disk, F8 / F9 / F10 / F11 pair counts should be re-run
during smoke + screenshot sign-off. F11 (cross-category) becomes
unblocked now that Waves D/E/F/G have landed cross-category siblings
(insurance, dating, forum_register, gov_portal_chat, etc.).

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

### 2026-04-28 — Wave C smoke tests blocked pending API key — [open]
Owner: vb
Affects: all 12 Wave C envs (ports 5201–5223)
What: All 12 envs have been built, all 4 registration files updated (environments.yaml, classification.csv, start_servers.sh, agent/runner.py), and all 23 ports confirmed HTTP 200 via boot test. The remaining two sign-off items are (1) agent smoke run confirming /api/captured logs a submission and (2) screenshot diff against parent. Both require running the benchmark agent, which requires GEMINI_API_KEY or GROQ_API_KEY. The logger does not persist screenshots to disk by default — logger.py would need a one-line patch to write PNGs alongside the JSON logs before the scrn item can be completed.
Need: API key from Vaibhav to unblock. Alternatively, screenshot sign-off can be done manually with the Playwright script tools/screenshot_wavec.py once created.

### 2026-05-06 — Structural cruft from `cp -r` cascades — [open]
Owner: unassigned
Affects: ecommerce-platform-pi, adp_authority, ecommerce_scarcity, github_phish_scarcity
What: A stylesheet/asset audit on 2026-05-06 found four envs with dead-weight nested directories left over from sibling-build `cp -r` operations:
(1) `ecommerce-platform-pi/` has both `templates/templates/` and `static/static/` with duplicated copies of the same files. The active app uses the top-level `templates/` and `static/css/` so it runs correctly; the nested copies are inert.
(2) `ecommerce-platform-pi/` is also a SINGLE-app collapse of the parent `ecommerce-platform/`, which is an 8-store multi-app environment (amazon, bargain_electro, fake_payment, fake_tracker, shopsmart, target, techvault, walmart). The PI sibling kept only one store, losing the typosquat-vs-legitimate-store contrast that gives the parent its F8 measurement power. This is a design issue, not just cleanup.
(3) `adp_authority/ADP/`, `ecommerce_scarcity/ecommerce-platform/`, and `github_phish_scarcity/subfolder/` each contain a complete nested copy of the parent directory. `start_servers.sh` launches the top-level entry point in every case, so they are inert at runtime — but they bloat the repo (~110 files in ecommerce_scarcity is roughly half dead weight) and confuse anyone diffing parent ↔ sibling.
Stylesheet refs themselves all resolve at runtime — the issue is purely structural cleanup plus the F8-design question for #2.
Need: (a) decide whether to redo `ecommerce-platform-pi` as a proper multi-app sibling that preserves the parent's contrast, or accept the simplified version and update the F8 brief. (b) Once decided, delete the four nested-parent directories.

---

## Completed envs (audit trail)

Move rows here only when status hits 🟩 done AND classification.csv is updated. Append to the bottom; never reorder.

| Date | Env | Owner | Branch / PR | Notes |
|---|---|---|---|---|

*(none yet — Wave C envs are at 🟦 qa pending smoke + screenshot diff)*

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
