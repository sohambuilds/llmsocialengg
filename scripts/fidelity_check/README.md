# Fidelity Check Pipeline

Blind rating study for §3 of the paper: our templated attack environments vs. real phishing pages from [PhreshPhish](https://arxiv.org/abs/2507.10854).

## What this produces
- Mean visual believability / copy quality / trustworthiness scores (1–5) for ours vs. real
- Inter-rater Cohen's κ per rubric
- Which-is-which accuracy (can raters tell ours from real? chance = 50%)
- A ready-to-paste paper paragraph

## Steps

### Step 1 — Screenshot our environments
Requires servers running. Start them first:
```powershell
bash start_servers.sh
```
Then:
```powershell
python scripts/fidelity_check/01_screenshot_ours.py --out-dir scripts/fidelity_check/screenshots
```
Output: `screenshots/ours/<env_key>.png` (20 files)

### Step 2 — Screenshot real phishing pages
Streams PhreshPhish dataset, finds Wayback Machine snapshots, screenshots them.
No servers needed. Requires `pip install datasets`.
```powershell
python scripts/fidelity_check/02_screenshot_real.py --out-dir scripts/fidelity_check/screenshots --n 20
```
Output: `screenshots/real/<sha256>.png` (up to 20 files)

Takes ~10–20 min (Wayback CDX API rate limit). Re-runs are safe (caches snapshots).

### Step 3 — Create blind rating form
Mixes ours + real into numbered PNGs (01.png … 40.png) and creates blank CSV.
```powershell
python scripts/fidelity_check/03_create_rating_form.py --out-dir scripts/fidelity_check/screenshots
```
Output:
- `screenshots/rating_set/01.png … 40.png` — the blind set (share with raters)
- `screenshots/rating_manifest.json` — the answer key (**DO NOT SHARE**)
- `screenshots/rating_sheet_blank.csv` — blank form (share with raters)

### Step 4 — Human rating (manual)
Two raters independently open the `rating_set/` folder and the blank CSV.
For each screenshot (01–40):
- `visual_believability_1to5`: 1 = obviously fake, 5 = looks exactly like the real brand site
- `copy_quality_1to5`: 1 = broken/spammy text, 5 = professional copy indistinguishable from legit
- `would_fool_human_1to5`: 1 = no careful person would fall for this, 5 = would fool most users
- `source_guess_ours_or_real`: type `ours` or `real`

Save as `screenshots/rating_sheet_rater1.csv` and `screenshots/rating_sheet_rater2.csv`.

### Step 5 — Analyze
```powershell
python scripts/fidelity_check/04_analyze_ratings.py `
    --rater1 scripts/fidelity_check/screenshots/rating_sheet_rater1.csv `
    --rater2 scripts/fidelity_check/screenshots/rating_sheet_rater2.csv `
    --manifest scripts/fidelity_check/screenshots/rating_manifest.json `
    --out-json scripts/fidelity_check/screenshots/fidelity_results.json
```
Prints per-rubric means, kappa, which-is-which accuracy, and a ready paper paragraph.

## Notes
- The 20 environments cover all 7 attack vectors and all 3 salience levels.
- The 20 real pages are matched by target brand (Amazon, Netflix, Chase, etc.) so the comparison is fair.
- The Wayback Machine renders pages with original CSS/images, so screenshots reflect the live phishing page at capture time.
- PhreshPhish citation: Dalton et al. (2025), arXiv:2507.10854, CC-BY-4.0.
