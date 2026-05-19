"""Pull task description + first-step reasoning + last-step reasoning for problem cells."""
import json, glob
from pathlib import Path

problem_cells = [
    ('cluttered_downloads', 'C0', 'LOOPING'),
    ('marketplace', 'C0', 'LOOPING'),
    ('job_portal', 'C0', 'reached_trap=False'),
    ('gov_portal', 'C0', 'reached_trap=False'),
    ('summarizer', 'C0', 'PLR=100% api_key'),
]

for env, cond, tag in problem_cells:
    pattern = f'agent/logs/v2/gpt5mini_v3/{env}/GPT-5_mini_*/{cond}/seed_1/*_openai_gpt-5-mini_*.json'
    matches = [f for f in glob.glob(pattern) if '.score.' not in f and 'meta' not in f]
    if not matches:
        print(f"\n=== {env} / {cond} / {tag} === NO SESSION FOUND")
        continue
    f = matches[0]
    sess = json.load(open(f, encoding='utf-8'))

    print(f"\n=== {env} / {cond} ({tag}) ===")

    # Task description
    task = sess.get('task_description', sess.get('task', sess.get('metadata', {}).get('task_description', None)))
    if task:
        print(f"  TASK: {task[:250]}")

    # First N reasoning entries
    steps = sess.get('steps', sess.get('session_log', []))
    if not isinstance(steps, list):
        print(f"  (no steps list)")
        continue
    print(f"  Total steps in log: {len(steps)}")
    # First step
    if steps:
        first = steps[0]
        if isinstance(first, dict):
            url = first.get('observation', {}).get('url', first.get('url', 'NA'))
            r = first.get('reasoning', first.get('thought', ''))
            if not r:
                actions = first.get('actions', [])
                if actions and isinstance(actions, list):
                    r = actions[0].get('reasoning', '') if isinstance(actions[0], dict) else ''
            print(f"  STEP 1 url: {url}")
            print(f"  STEP 1 reasoning: {str(r)[:300]}")
    # Last 2 steps
    for i, step in enumerate(steps[-2:]):
        idx = len(steps) - 2 + i
        if isinstance(step, dict):
            url = step.get('observation', {}).get('url', step.get('url', 'NA'))
            r = step.get('reasoning', step.get('thought', ''))
            if not r:
                actions = step.get('actions', [])
                if actions and isinstance(actions, list):
                    r = actions[0].get('reasoning', '') if isinstance(actions[0], dict) else ''
            print(f"  STEP {idx+1} url: {url}")
            print(f"  STEP {idx+1} reasoning: {str(r)[:300]}")
