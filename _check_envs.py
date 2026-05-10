import yaml, re

with open('agent/config/environments.yaml') as f:
    data = yaml.safe_load(f)
envs = data.get('environments', {})

AVAILABLE_ENVS = [
    'job_portal','ecommerce','news','freelance','gov_portal','coc_gems','cluttered_downloads','marketplace',
    'github_phish','summarizer','virus_scanner','file_converter','quiz_scam','support_chat','saas_onboard',
    'crypto_platform','virus_scanner_calm','virus_scanner_subtle','marketplace_pi_hidden','forum_register_medium',
    'forum_register_critical','virus_scanner_plausible','quiz_scam_subtle','summarizer_plausible',
    'summarizer_subtle','crypto_platform_blatant','crypto_platform_subtle','saas_onboard_subtle',
    'e10_mychart_plausible','e10_mychart_blatant','freelance_blatant','support_chat_plausible',
    'job_portal_no_timer','gov_portal_no_timer','marketplace_calm','ecommerce_pi','news_pi',
    'quiz_scam_pi_sysmsg','e8_chase_pi_hidden','e17_amazon_pi_visible','saas_onboard_pi_hidden',
    'saas_onboard_pi_sysmsg','support_chat_pi_visible','support_chat_pi_sysmsg','summarizer_chat',
    'marketplace_chat','gov_portal_chat','e18_linkedin_chat','support_chat_static','freelance_static',
    'dating_verify','adp_no_banner','aws_no_countdown','booking_no_timer','e7_ninite_calm',
    'e8_chase_no_countdown','saas_onboard_authority','adp_authority','marketplace_social_proof',
    'e23_netflix_social_proof','ecommerce_scarcity','github_phish_scarcity','news_medium','bumble_medium',
    'saas_onboard_medium','e10_mychart_calm','e13_irs_no_timer','e14_oracle_no_timer',
    'job_portal_medium','saas_onboard_direct','marketplace_email_entry','ancestry_dna_email_entry',
    'betterhelp_email_entry','bumble_email_entry','dating_photo_id','insurance_quote',
    'insurance_quote_medium','adp','aws','ancestry_dna','betterhelp','booking','bumble','e7_ninite',
    'e8_chase','e10_mychart','e13_irs','e14_oracle','e17_amazon','e18_linkedin','e23_netflix',
    'all','benchmark','tier1','tier2','tier3','llmpit','worked_briefs','wave_c','wave_b','wave_d','wave_bd'
]

yaml_keys = set(envs.keys())
runner_keys = set(AVAILABLE_ENVS) - {'all','benchmark','tier1','tier2','tier3','llmpit','worked_briefs','wave_c','wave_b','wave_d','wave_bd'}

missing_from_runner = yaml_keys - runner_keys
extra_in_runner = runner_keys - yaml_keys

print(f'YAML envs: {len(yaml_keys)}')
print(f'Runner AVAILABLE_ENVS (excl groups): {len(runner_keys)}')
print(f'Missing from runner.py: {sorted(missing_from_runner)}')
print(f'Extra in runner.py: {sorted(extra_in_runner)}')

# Check start_servers.sh dir coverage
with open('start_servers.sh') as f:
    content = f.read()

started_dirs = set()
# Find all directories under all_websites/
for match in re.finditer(r'all_websites/([^/]+)', content):
    started_dirs.add(match.group(1))

print(f'Server dirs in start_servers.sh: {len(started_dirs)}')

# Check which YAML envs have run_servers pointing to existing dirs
no_server = []
for name, cfg in sorted(envs.items()):
    run_srv = cfg.get('run_servers', '')
    if run_srv:
        m = re.search(r'all_websites/([^/]+)', run_srv)
        if m:
            d = m.group(1)
            if d not in started_dirs:
                no_server.append((name, d))

if no_server:
    print(f'YAML envs with run_servers pointing to missing dir:')
    for name, d in sorted(no_server):
        print(f'  {name} -> {d}')
else:
    print(f'All run_servers dirs found in start_servers.sh: OK')

# Check all envs can build start URLs
bad_start = []
for name, cfg in envs.items():
    sites = cfg.get('sites', {})
    start = cfg.get('start_site', '')
    if start and start not in sites:
        bad_start.append((name, start, list(sites.keys())))
if bad_start:
    print(f'Env with bad start_site:')
    for name, start, keys in bad_start:
        print(f'  {name}: start={start}, sites={keys}')
else:
    print(f'All envs have valid start_site: OK')
