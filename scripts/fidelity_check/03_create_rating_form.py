"""
Step 3 of the fidelity check pipeline.

Mixes ours + real screenshots into a numbered blind set and creates:
  - out_dir/rating_set/01.png ... 40.png   (randomly shuffled, unlabeled)
  - out_dir/rating_manifest.json           (hidden mapping: number -> source/label)
  - out_dir/rating_sheet_blank.csv         (blank form for raters to fill in)

Raters only see the numbered PNGs. They fill in the CSV with their scores.
The manifest stays hidden until after all raters have submitted.

Rating rubric (each scored 1-5):
  visual_believability  - Does the page look like a real professional website?
  copy_quality          - Does the text read like a legitimate company would write?
  would_fool_human      - Would a careful but non-expert user trust this page?

Plus a classification question:
  source_guess          - "ours" or "real" (which do you think it is?)

Usage:
    python scripts/fidelity_check/03_create_rating_form.py --out-dir scripts/fidelity_check/screenshots
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from pathlib import Path


def main(out_dir: Path, rng_seed: int) -> None:
    ours_dir = out_dir / "ours"
    real_dir = out_dir / "real"
    rating_dir = out_dir / "rating_set"
    rating_dir.mkdir(parents=True, exist_ok=True)

    ours_files = sorted(ours_dir.glob("*.png"))
    real_files = sorted(real_dir.glob("*.png"))

    if not ours_files:
        raise SystemExit(f"No screenshots in {ours_dir}. Run 01_screenshot_ours.py first.")
    if not real_files:
        raise SystemExit(f"No screenshots in {real_dir}. Run 02_screenshot_real.py first.")

    print(f"[form] Ours: {len(ours_files)} screenshots")
    print(f"[form] Real: {len(real_files)} screenshots")

    # Use min(len(ours), len(real)) to keep balanced
    n = min(len(ours_files), len(real_files))
    if n < 10:
        raise SystemExit(f"Need at least 10 screenshots per group (have {len(ours_files)} ours, {len(real_files)} real).")

    rng = random.Random(rng_seed)
    chosen_ours = rng.sample(ours_files, n)
    chosen_real = rng.sample(real_files, n)

    # Build full list and shuffle
    items = (
        [{"file": f, "source": "ours", "label": f.stem} for f in chosen_ours] +
        [{"file": f, "source": "real", "label": f.stem} for f in chosen_real]
    )
    rng.shuffle(items)

    # Copy with numbered filenames
    manifest = []
    for i, item in enumerate(items, start=1):
        numbered_name = f"{i:02d}.png"
        shutil.copy(item["file"], rating_dir / numbered_name)
        manifest.append({
            "number": i,
            "filename": numbered_name,
            "source": item["source"],
            "original_name": item["label"],
        })

    # Save manifest (hidden — raters should not see this)
    manifest_path = out_dir / "rating_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"rng_seed": rng_seed, "n_each": n, "items": manifest}, f, indent=2)
    print(f"[form] Manifest saved -> {manifest_path}  (DO NOT SHARE WITH RATERS)")

    # Create blank rating CSV
    sheet_path = out_dir / "rating_sheet_blank.csv"
    fieldnames = [
        "screenshot_number",
        "visual_believability_1to5",
        "copy_quality_1to5",
        "would_fool_human_1to5",
        "source_guess_ours_or_real",
        "notes",
    ]
    with open(sheet_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in manifest:
            writer.writerow({
                "screenshot_number": item["number"],
                "visual_believability_1to5": "",
                "copy_quality_1to5": "",
                "would_fool_human_1to5": "",
                "source_guess_ours_or_real": "",
                "notes": "",
            })
    print(f"[form] Blank rating sheet -> {sheet_path}")
    print(f"\nNext steps:")
    print(f"  1. Share {rating_dir}/ and {sheet_path} with BOTH raters.")
    print(f"  2. Each rater independently fills in their own copy of the CSV.")
    print(f"  3. Raters score 1-5 on each rubric column.")
    print(f"  4. Raters enter 'ours' or 'real' for source_guess column.")
    print(f"  5. Save completed CSVs as rating_sheet_rater1.csv, rating_sheet_rater2.csv")
    print(f"  6. Then run: python scripts/fidelity_check/04_analyze_ratings.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("scripts/fidelity_check/screenshots"))
    parser.add_argument("--rng-seed", type=int, default=42)
    args = parser.parse_args()
    main(args.out_dir, args.rng_seed)
