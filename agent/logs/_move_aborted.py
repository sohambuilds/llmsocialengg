"""Move historical clutter under agent/logs/ into agent/logs/_aborted/.

Whitelist (kept in place): items referenced by paper-plan.md,
phase4-checklist.md, pilot-v2-plan.md, analysis/pilot_v2_findings.md,
or CLAUDE.md as evidence of completed work, plus the latest Llama 4
Scout dress-rehearsal slice.

Idempotent: re-running is a no-op once everything is moved.
"""
from __future__ import annotations
import shutil
from pathlib import Path

LOGS = Path(__file__).parent
ABORTED = LOGS / "_aborted"
KEEP = {
    "llamarun2soham",                # paper-plan §1.4, CLAUDE.md, this run
    "pilot_llama4_v2_overnight",     # analysis/pilot_v2_findings.md, pilot-v2-plan.md
    "smoke-matrix",                  # phase4-checklist Week 2 E2 (projection)
    "v2",                            # phase4-checklist Week 2 E1, paper-plan §3
    "dr_judge_results.json",         # phase4-checklist Week 1 E2 (κ=0.82)
    "dr_labeling_results.json",      # phase4-checklist Week 2 E2 (200-sample)
    "dr_labeling_samples.json",      # input pool for the above
    "dr_human_judge_kappa.json",     # phase4-checklist Week 2 E2 (κ=1.0)
    "phase3_page_load_smoke.json",   # phase4-checklist Week 1 E3 (101/101 ok)
    "_aborted",                      # destination itself
    "_move_aborted.py",              # this script
}

ABORTED.mkdir(exist_ok=True)

moved_dirs = 0
moved_files = 0
skipped = 0
for entry in LOGS.iterdir():
    if entry.name in KEEP:
        skipped += 1
        continue
    dest = ABORTED / entry.name
    if dest.exists():
        # Already moved on a previous run; second copy of same name appearing
        # would mean something was recreated -- merge would be risky, leave alone.
        print(f"  SKIP (dest exists): {entry.name}")
        continue
    shutil.move(str(entry), str(dest))
    if dest.is_dir():
        moved_dirs += 1
    else:
        moved_files += 1

print(f"Moved {moved_dirs} dirs and {moved_files} files into {ABORTED.relative_to(LOGS.parent)}/")
print(f"Kept in place: {sorted(KEEP - {'_aborted', '_move_aborted.py'})}")
remaining = sorted(p.name for p in LOGS.iterdir())
print(f"agent/logs/ now has {len(remaining)} top-level entries: {remaining}")
