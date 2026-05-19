"""Scan v3 session logs for residual contamination signals in agent reasoning."""
import json, glob, re
from pathlib import Path
from collections import defaultdict

# Patterns to flag in reasoning text
PATTERNS = {
    'localhost': re.compile(r'\blocalhost\b', re.IGNORECASE),
    'no_https': re.compile(r'\b(no[ -]?https|plain[ -]?http|not?[ -]?(using|over)?[ -]?https|missing https|http[ -]?(not|isn.t)[ -]?https)\b', re.IGNORECASE),
    'non_standard_port': re.compile(r'\b(non[ -]?standard|unusual|unusual[- ]port|odd port|port\s*\d{4,5}|:\d{4,5}\b)', re.IGNORECASE),
    'sandbox': re.compile(r'\b(sandbox|test environment|dev environment|benchmark environment)\b', re.IGNORECASE),
    '127_0_0_1': re.compile(r'127\.0\.0\.1', re.IGNORECASE),
    'colon_port_only': re.compile(r':\s*\d{4,5}\b'),
}

# Track per-env per-condition counts
hits_per_pattern = defaultdict(int)
hits_per_env_pattern = defaultdict(lambda: defaultdict(int))
sessions_with_any_hit = 0
total_sessions = 0
example_hits = defaultdict(list)

for f in sorted(glob.glob('agent/logs/v2/gpt5mini_v3/*/GPT-5_mini_*/C*/seed_1/*.json')):
    if '.score.' in f or 'meta.json' in f:
        continue
    p = Path(f)
    env = p.parts[-5]
    cond = p.parts[-3]
    try:
        sess = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f"ERROR reading {f}: {e}")
        continue
    total_sessions += 1

    # Extract all reasoning text from the session
    # Walk steps and gather any text field that looks like agent reasoning
    text_blob = ''
    if isinstance(sess, dict):
        steps = sess.get('steps', sess.get('session_log', []))
        for step in steps if isinstance(steps, list) else []:
            for k in ('reasoning', 'thought', 'thinking', 'llm_response_text', 'raw_response'):
                v = step.get(k) if isinstance(step, dict) else None
                if isinstance(v, str):
                    text_blob += '\n' + v
                elif isinstance(v, dict):
                    # nested
                    text_blob += '\n' + json.dumps(v)
            # Also actions array may carry reasoning per action
            actions = step.get('actions') if isinstance(step, dict) else None
            if isinstance(actions, list):
                for a in actions:
                    if isinstance(a, dict):
                        for k in ('reasoning', 'trust_score', 'site_url'):
                            v = a.get(k)
                            if isinstance(v, str):
                                text_blob += '\n' + v

    any_hit_this_session = False
    for label, pat in PATTERNS.items():
        matches = pat.findall(text_blob)
        if matches:
            hits_per_pattern[label] += len(matches)
            hits_per_env_pattern[env][label] += len(matches)
            any_hit_this_session = True
            if len(example_hits[label]) < 3:
                # Pull a 200-char window around the first match
                m = pat.search(text_blob)
                if m:
                    s = max(0, m.start() - 80)
                    e = min(len(text_blob), m.end() + 80)
                    snippet = text_blob[s:e].replace('\n', ' ')[:260]
                    example_hits[label].append(f"  [{env}/{cond}] ...{snippet}...")
    if any_hit_this_session:
        sessions_with_any_hit += 1

print(f"=== Reasoning-trace contamination scan ===")
print(f"Total sessions scanned: {total_sessions}")
print(f"Sessions with any flagged-pattern hit: {sessions_with_any_hit} ({100*sessions_with_any_hit/total_sessions:.1f}%)")
print()
print(f"Hit counts by pattern:")
for label, n in sorted(hits_per_pattern.items(), key=lambda x: -x[1]):
    print(f"  {label}: {n} occurrences")

print()
print(f"Hit counts by env (any pattern):")
for env, d in sorted(hits_per_env_pattern.items()):
    total = sum(d.values())
    print(f"  {env}: {total} ({', '.join(f'{k}={v}' for k, v in sorted(d.items()))})")

print()
print("=== Example snippets (first 3 per pattern) ===")
for label, examples in example_hits.items():
    print(f"\n--- {label} ---")
    for ex in examples:
        print(ex)
