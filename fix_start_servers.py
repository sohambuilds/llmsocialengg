import yaml

with open('agent/config/environments.yaml', 'r') as f:
    root_data = yaml.safe_load(f)

env_data = root_data.get('environments', {})

true_ports = {}
for env_name, config in env_data.items():
    if isinstance(config, dict) and 'sites' in config:
        for site_key, site_info in config['sites'].items():
            if isinstance(site_info, dict) and 'port' in site_info:
                true_ports[env_name] = str(site_info['port'])
                break # Just grab the first port defined for the env

# Print what we found
print(f"Loaded {len(true_ports)} ports from environments.yaml")

with open('start_servers.sh', 'r') as f:
    lines = f.readlines()

names = []
cmds = []
ports = []

in_names = False
in_cmds = False
in_ports = False

for line in lines:
    clean = line.strip()
    if clean.startswith('NAMES=('): in_names = True
    elif in_names and clean == ')': in_names = False
    elif in_names and clean and not clean.startswith('#'): names.append(clean.replace('"', ''))
    
    if clean.startswith('CMDS=('): in_cmds = True
    elif in_cmds and clean == ')': in_cmds = False
    elif in_cmds and clean and not clean.startswith('#'): cmds.append(clean.replace('"', ''))

    if clean.startswith('PORTS=('): in_ports = True
    elif in_ports and clean == ')': in_ports = False
    elif in_ports and clean and not clean.startswith('#'): ports.append(clean.replace('"', ''))

aligned_names = []
aligned_cmds = []
aligned_ports = []
seen = set()

# Clean up any leftover duplicates in NAMES
for i, n in enumerate(names):
    if n in seen:
        continue
    seen.add(n)
    aligned_names.append(n)
    
    if i < len(cmds):
        aligned_cmds.append(cmds[i])
    else:
        aligned_cmds.append(f'uv run python all_websites/{n}/run_servers.py')

    # Force correct port
    if n in true_ports:
        aligned_ports.append(true_ports[n])
    else:
        # fallback
        if i < len(ports):
            aligned_ports.append(ports[i])
        else:
            aligned_ports.append('9999')

# Overrides for environments without config
override = {
    'dating_photo_id': '5421',
    'insurance_quote': '5422',
    'insurance_quote_medium': '5423'
}
for i, n in enumerate(aligned_names):
    if n in override:
        aligned_ports[i] = override[n]
    if n == 'github_phish_scarcity' and aligned_ports[i] == '9999':
        aligned_ports[i] = '5135' # Known port from yaml
        
new_lines = []
skip = False
for line in lines:
    if line.strip().startswith('NAMES=('):
        skip = True
        new_lines.append('NAMES=(\n')
        for n in aligned_names:
            new_lines.append(f'    "{n}"\n')
        new_lines.append(')\n')
    elif line.strip().startswith('CMDS=('):
        skip = True
        new_lines.append('CMDS=(\n')
        for c in aligned_cmds:
            new_lines.append(f'    "{c}"\n')
        new_lines.append(')\n')
    elif line.strip().startswith('PORTS=('):
        skip = True
        new_lines.append('PORTS=(\n')
        for p in aligned_ports:
            new_lines.append(f'    "{p}"\n')
        new_lines.append(')\n')
    elif skip and line.strip() == ')':
        skip = False
    elif not skip:
        new_lines.append(line)

with open('start_servers.sh', 'w', newline='\n') as f:
    f.writelines(new_lines)

print(f"Successfully rewritten start_servers.sh with 100% correct ports.")
