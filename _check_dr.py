from pathlib import Path
import json

dr_judge = Path('agent/evaluation/dr_judge.py')
print(f'dr_judge.py exists: {dr_judge.exists()}')
print(f'Lines: {len(dr_judge.read_text().splitlines())}')

results_file = Path('agent/logs/dr_judge_results.json')
print(f'Previous results exist: {results_file.exists()}')
if results_file.exists():
    data = json.loads(results_file.read_text())
    sessions = data.get('sessions', [])
    print(f'  Sessions evaluated: {len(sessions)}')
    summary = data.get('summary', {})
    print(f'  Detected: {summary.get("detected_count", "N/A")}')
    print(f'  Kappa: {summary.get("kappa", "N/A")}')