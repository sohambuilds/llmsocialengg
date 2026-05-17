"""Confirm the C0 orphan-session theory: are the unscored .json files all
from an earlier run, with a later scored survivor for each env?"""
import re
from collections import defaultdict
from pathlib import Path

C0 = Path(__file__).parent / "Llama_4_Scout_17B_(Groq)" / "C0"

# Group by env_key, separate scored survivor from orphans
def env_of(name: str) -> str:
    return name.split("_meta-llama_")[0]

def ts_of(name: str) -> str:
    m = re.search(r"(\d{8}_\d{6})", name)
    return m.group(1) if m else ""

scored_pair_ts: dict[str, str] = {}
all_session_ts: dict[str, list[str]] = defaultdict(list)

for p in C0.iterdir():
    if p.name.endswith(".score.json"):
        scored_pair_ts[env_of(p.name)] = ts_of(p.name)
    elif p.name.endswith(".json"):
        all_session_ts[env_of(p.name)].append(ts_of(p.name))

print(f"unique envs (scored): {len(scored_pair_ts)}")
print(f"unique envs (any session): {len(all_session_ts)}")

orphan_count = 0
orphan_later_than_survivor = []
for env, tss in all_session_ts.items():
    survivor = scored_pair_ts.get(env)
    for t in tss:
        if t == survivor:
            continue
        orphan_count += 1
        if survivor is not None and t > survivor:
            orphan_later_than_survivor.append((env, t, survivor))

print(f"total orphan session.json files: {orphan_count}")
print(f"orphans LATER than their scored survivor: {len(orphan_later_than_survivor)}")
if orphan_later_than_survivor:
    print("  (these would be suspicious — would mean we kept the older one)")
    for env, orph, surv in orphan_later_than_survivor[:10]:
        print(f"    {env}: orphan {orph} > survivor {surv}")

# Multi-orphan envs
multi = {e: len(t) for e, t in all_session_ts.items() if len(t) > 2}
print(f"\nenvs with >2 session.json files (started 3+ times): {len(multi)}")
for e, n in multi.items():
    print(f"  {e}: {n} session files")
