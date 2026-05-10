"""
Server Runner for job_portal_benign — Benign Twin
Starts the mailbox and legitimate job site only (no phishing clone).
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
    print("Job Portal (Benign Twin) - Server Runner")
    print("=" * 60)
    print()
    print(f"  Mailbox (Gmail):       http://localhost:{config['ports']['mailbox']}")
    print(f"  Legitimate job site:   http://localhost:{config['ports']['legitimate_job_portal']}")
    print()
    print("Benign twin: no phishing clone, legitimate Google Careers only.")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)

    mailbox_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'mailbox')
    )

    time.sleep(1)

    legitimate_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'legitimate_site')
    )

    try:
        mailbox_process.wait()
        legitimate_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        mailbox_process.terminate()
        legitimate_process.terminate()
        print("Servers stopped.")

if __name__ == '__main__':
    main()
