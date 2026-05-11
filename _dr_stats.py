import json
data = json.load(open('agent/logs/dr_judge_results.json'))
sessions = data.get('sessions', [])
print(f'Sessions: {len(sessions)}')

# Count sessions with at least one detection
detected_sessions = 0
for sess in sessions:
    primary = sess.get('primary', [])
    if any(step.get('detected') for step in primary):
        detected_sessions += 1

print(f'Sessions with at least 1 detection: {detected_sessions}')
print(f'DR (detection rate): {detected_sessions/len(sessions)*100:.1f}%')