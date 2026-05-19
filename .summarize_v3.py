import json, glob, re
from pathlib import Path
from collections import Counter, defaultdict

rows = []
for f in sorted(glob.glob('agent/logs/v2/gpt5mini_v3/*/GPT-5_mini_*/C*/seed_1/*.score.json')):
    p = Path(f)
    env = p.parts[-5]
    cond = p.parts[-3]
    d = json.load(open(f))
    s = d.get('summary', d)
    rows.append({
        'env': env,
        'cond': cond,
        'PLR': s.get('PLR', 'NA'),
        'c_PLR': s.get('c_PLR', 'NA'),
        'ASR': s.get('ASR', 'NA'),
        'TCR': s.get('TCR', 'NA'),
        'DR': s.get('DR', 'NA'),
        'reached_trap': s.get('reached_trap', 'NA'),
        'defended': s.get('defended', 'NA'),
        'steps_used': s.get('steps_used', 'NA'),
        'critical_fields_leaked': s.get('critical_fields_leaked', []),
        'session_path': f.replace('.score.json', '.json'),
    })

print(f"{'env':<24}{'cond':<5}{'PLR':<7}{'c_PLR':<7}{'ASR':<11}{'TCR':<12}{'DR':<12}{'trap':<7}{'def':<7}{'steps':<6}{'critical_leaked':<40}")
print('-' * 130)
for r in rows:
    crit = ','.join(r['critical_fields_leaked'][:3]) if isinstance(r['critical_fields_leaked'], list) and r['critical_fields_leaked'] else ''
    print(f"{r['env']:<24}{r['cond']:<5}{str(r['PLR']):<7}{str(r['c_PLR']):<7}{str(r['ASR']):<11}{str(r['TCR']):<12}{str(r['DR']):<12}{str(r['reached_trap']):<7}{str(r['defended']):<7}{str(r['steps_used']):<6}{crit:<40}")

# Aggregates
print()
print('=== Aggregates ===')
print(f"reached_trap=False count: {sum(1 for r in rows if r['reached_trap'] is False)}  / {len(rows)}")
print(f"TCR=LOOPING count: {sum(1 for r in rows if r['TCR'] == 'LOOPING')}  / {len(rows)}")
print(f"TCR=INCOMPLETE count: {sum(1 for r in rows if r['TCR'] == 'INCOMPLETE')}  / {len(rows)}")
print(f"TCR=REFUSED count: {sum(1 for r in rows if r['TCR'] == 'REFUSED')}  / {len(rows)}")
print(f"TCR=COMPLETED count: {sum(1 for r in rows if r['TCR'] == 'COMPLETED')}  / {len(rows)}")
print(f"TCR=BROWSER_ERROR count: {sum(1 for r in rows if r['TCR'] == 'BROWSER_ERROR')}  / {len(rows)}")
print()
# By condition: PLR_crit
print('=== By condition: c_PLR mean (crit-PLR), reached_trap rate, ASR=SUCCEEDED rate ===')
by_cond = defaultdict(list)
for r in rows:
    by_cond[r['cond']].append(r)
for c in ['C0', 'C1', 'C2', 'C3']:
    cs = by_cond.get(c, [])
    if not cs:
        continue
    plr_c_vals = []
    for r in cs:
        v = r['c_PLR']
        if isinstance(v, str) and v.endswith('%'):
            plr_c_vals.append(float(v[:-1]))
    mean_plr_c = sum(plr_c_vals) / len(plr_c_vals) if plr_c_vals else 0
    trap_rate = sum(1 for r in cs if r['reached_trap'] is True) / len(cs)
    asr_rate = sum(1 for r in cs if r['ASR'] == 'SUCCEEDED') / len(cs)
    print(f"  {c}: c_PLR mean = {mean_plr_c:.2f}% | trap_rate = {trap_rate*100:.0f}% | ASR success = {asr_rate*100:.0f}%")
