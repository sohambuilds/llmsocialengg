import json
data = json.load(open('agent/logs/dr_judge_results.json'))
print(f'Sessions evaluated: {data.get("num_sessions")}')
print(f'Inter-judge kappa: {data.get("inter_judge_kappa")}')

# Count detected by primary
primary = data.get('primary_judge', {})
detected = sum(1 for s in primary.values() if any(p.get('detected') for p in s))
print(f'Detected by primary (GPT-4o): {detected}/{data.get("num_sessions")}')

# Count detected by secondary
secondary = data.get('secondary_judge', {})
detected2 = sum(1 for s in secondary.values() if any(p.get('detected') for p in s))
print(f'Detected by secondary (Llama 4): {detected2}/{data.get("num_sessions")}')