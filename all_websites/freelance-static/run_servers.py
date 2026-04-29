"""
Server Runner for FreelanceHub Social Engineering Benchmark
Starts the freelance platform, fake company site, and fake DocuSign for testing.

Usage: python run_servers.py
"""

import json
import subprocess
import sys
import os
import time


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    config = load_config()

    print("=" * 60)
    print("FreelanceHub Benchmark - Server Runner")
    print("=" * 60)
    print()
    print("Starting servers...")
    print()
    print(f"  FreelanceHub:      http://127.0.0.1:{config['ports']['freelancehub']}")
    print(f"  Fake Company:      http://127.0.0.1:{config['ports']['fake_company']}")
    print(f"  Fake DocuSign:     http://127.0.0.1:{config['ports']['fake_docusign']}")
    print()
    print("Flow: Agent opens FreelanceHub -> reads messages -> scam conversation")
    print("      contains links to fake company site and fake DocuSign")
    print()
    print("Domain mappings (add to hosts file):")
    for entry in config['hosts_entries']:
        print(f"  {entry}")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)

    hub_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'freelancehub')
    )

    time.sleep(1)

    company_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'fake_company')
    )

    time.sleep(1)

    docusign_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'fake_docusign')
    )

    try:
        hub_process.wait()
        company_process.wait()
        docusign_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        hub_process.terminate()
        company_process.terminate()
        docusign_process.terminate()
        print("Servers stopped.")


if __name__ == '__main__':
    main()
