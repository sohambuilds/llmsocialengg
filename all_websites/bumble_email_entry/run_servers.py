"""Launch the bumble_email_entry servers (Wave F: mailbox added)."""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).parent
config = json.loads((ROOT / "config.json").read_text())

servers = [
    ("mailbox", ROOT / "mailbox"),
    ("bumble_app", ROOT / "bumble_app"),
]

procs = []
for name, cwd in servers:
    port = config["ports"][name]
    print(f"Starting {name} on port {port} …")
    entry = "app.py" if (cwd / "app.py").exists() else "server.py"
    p = subprocess.Popen([sys.executable, entry], cwd=str(cwd))
    procs.append((name, p))
    time.sleep(1)

print("\nAll servers running:")
for name, _ in servers:
    port = config["ports"][name]
    domain = config["domains"][name]
    print(f"  {name}: http://localhost:{port}  ({domain})")

print("\nPress Ctrl+C to stop all servers.")
try:
    for _, p in procs:
        p.wait()
except KeyboardInterrupt:
    for _, p in procs:
        p.terminate()
