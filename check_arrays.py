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
    elif in_names and clean and not clean.startswith('#'): names.append(clean)
    
    if clean.startswith('CMDS=('): in_cmds = True
    elif in_cmds and clean == ')': in_cmds = False
    elif in_cmds and clean and not clean.startswith('#'): cmds.append(clean)
    
    if clean.startswith('PORTS=('): in_ports = True
    elif in_ports and clean == ')': in_ports = False
    elif in_ports and clean and not clean.startswith('#'): ports.append(clean)

print(f"NAMES: {len(names)}")
print(f"CMDS:  {len(cmds)}")
print(f"PORTS: {len(ports)}")

# Print out side by side to see the mismatch
for i in range(max(len(names), len(cmds), len(ports))):
    n = names[i] if i < len(names) else "---MISSING---"
    c = cmds[i] if i < len(cmds) else "---MISSING---"
    p = ports[i] if i < len(ports) else "---MISSING---"
    print(f"{i:02d} | {n[:25]:<25} | {p:<5} | {c[:40]}")
