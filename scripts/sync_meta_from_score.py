"""Sync each session's meta.json summary block from the rescored .score.json.

Companion to rescore_critical_plr.py. The parallel_runner caches a copy of
the scorer's summary in meta.json at run-time, but the rescore only patches
.score.json files. Downstream notebooks (compare_gemini_gpt5_llama.ipynb)
load from meta.json, so they were reading stale critical_fields_leaked /
c_PLR until this sync runs.

This script walks every seed dir and copies the rescored fields
(critical_fields_leaked + c_PLR) from .score.json into the sibling
meta.json's summary block. Idempotent: only writes if values differ.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import Counter


def sync_meta(score_path: Path, dry_run: bool = False) -> dict:
    meta_path = score_path.parent / "meta.json"
    if not meta_path.exists():
        return {"changed": False, "reason": "no_meta"}

    score = json.loads(score_path.read_text(encoding="utf-8"))
    score_summary = score.get("summary", {})
    if not score_summary:
        return {"changed": False, "reason": "no_score_summary"}

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta_summary = meta.get("summary", {})
    if not meta_summary:
        return {"changed": False, "reason": "no_meta_summary"}

    fields_to_sync = ["critical_fields_leaked", "c_PLR"]
    needs_write = False
    diff = {}
    for f in fields_to_sync:
        score_v = score_summary.get(f)
        meta_v = meta_summary.get(f)
        if score_v != meta_v:
            diff[f] = (meta_v, score_v)
            meta_summary[f] = score_v
            needs_write = True

    if not needs_write:
        return {"changed": False, "reason": "already_in_sync"}

    if not dry_run:
        backup = meta_path.with_name("meta.json.orig")
        if not backup.exists():
            backup.write_text(json.dumps(json.loads(meta_path.read_text(encoding="utf-8")),
                                         indent=2, default=str), encoding="utf-8")
        meta["summary"] = meta_summary
        meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    return {"changed": True, "diff": diff}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("roots", nargs="*", default=["agent/logs/v2"],
                   help="One or more log roots to recurse into.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    score_files: list[Path] = []
    for r in args.roots:
        root = Path(r)
        if not root.exists():
            print(f"  [skip] {root} does not exist", file=sys.stderr)
            continue
        score_files.extend(p for p in root.rglob("*.score.json")
                           if ".orig" not in p.suffixes)
    print(f"Scanning {len(score_files)} .score.json files")

    by_slice: Counter[str] = Counter()
    n_changed = 0
    n_already = 0
    n_no_meta = 0
    for sp in score_files:
        res = sync_meta(sp, dry_run=args.dry_run)
        if res["changed"]:
            n_changed += 1
            try:
                slice_name = sp.relative_to(Path("agent/logs")).parts[1]
            except ValueError:
                slice_name = "?"
            by_slice[slice_name] += 1
        elif res.get("reason") == "no_meta":
            n_no_meta += 1
        else:
            n_already += 1

    print()
    print(f"{'(DRY RUN) ' if args.dry_run else ''}Updated meta.json: {n_changed}  |  Already in sync: {n_already}  |  No meta.json: {n_no_meta}")
    if by_slice:
        print(f"Changes by slice:")
        for s, n in by_slice.most_common():
            print(f"  {s:32s}  {n} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
