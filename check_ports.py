with open('start_servers.sh', 'r') as f:
    lines = f.readlines()

names = []
in_names = False
for line in lines:
    if line.startswith('NAMES=('): in_names = True
    elif in_names and line.strip() == ')': in_names = False
    elif in_names and line.strip() and not line.strip().startswith('#'): names.append(line.strip().replace('\"', ''))

ports = []
in_ports = False
for line in lines:
    if line.startswith('PORTS=('): in_ports = True
    elif in_ports and line.strip() == ')': in_ports = False
    elif in_ports and line.strip() and not line.strip().startswith('#'): ports.append(line.strip().replace('\"', ''))

print(f"Total Names: {len(names)}, Total Ports: {len(ports)}")

for i, n in enumerate(names):
    if i < len(ports):
        p = ports[i]
        if ports.count(p) > 1:
            print(f"{n} uses DUPLICATE port {p}")
        if n in ['gov_portal_no_timer', 'e13_irs_no_timer', 'e14_oracle_no_timer', 'marketplace_email_entry', 'ancestry_dna_email_entry', 'marketplace_social_proof', 'e23_netflix_social_proof', 'ecommerce_scarcity', 'github_phish_scarcity']:
            print(f"FAILED SITE {n} mapped to port {p}")
