"""
Server Runner for e18_linkedin_benign — Benign Twin
Starts the mailbox and legitimate LinkedIn site (no phishing clone).
"""

import json
import os
import subprocess
import sys
import time


def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    config = load_config()
    print("=" * 60)
    print("e18_linkedin_benign — Benign Twin Server Runner")
    print("=" * 60)
    print()
    print(f"  Entry Point:       http://localhost:{config['ports']['mailbox']}")
    print(f"  LinkedIn (legit):  http://localhost:{config['ports']['linkedin']}")
    print()
    print("Benign twin: legitimate LinkedIn easy-apply, no SSN/DOB/bank.")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)
    entry_process = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'mailbox'))
    time.sleep(1)
    # In the benign twin the LinkedIn site directory was renamed from phishing_linkedin
    # but we kept the mailbox. The linkedin site is served from a lightweight app.
    linkedin_process = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'linkedin_legit'))

    try:
        entry_process.wait()
        linkedin_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        entry_process.terminate()
        linkedin_process.terminate()
        print("Stopped.")


if __name__ == '__main__':
    main()
