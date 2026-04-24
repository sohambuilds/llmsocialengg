"""
Server Runner for LLM PII Benchmark
Starts the mailbox, legitimate site, and phishing site for testing.

Usage: python run_servers.py
"""

import json
import subprocess
import sys
import os
import time
from threading import Thread

def load_config():
    """Load port configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    config = load_config()

    print("="*60)
    print("LLM PII Benchmark - Server Runner")
    print("="*60)
    print()
    print("Starting servers...")
    print()
    print(f"  Mailbox (Gmail):   http://localhost:{config['ports']['mailbox']}")
    print(f"  Legitimate site:   http://localhost:{config['ports']['legitimate_job_portal']}")
    print(f"  Phishing site:     http://localhost:{config['ports']['phishing_clone']}")
    print()
    print("Flow: Agent opens Mailbox -> reads phishing email -> clicks link -> Phishing site")
    print()
    print("Domain mappings (add to hosts file):")
    for entry in config['hosts_entries']:
        print(f"  {entry}")
    print()
    print("Press Ctrl+C to stop all servers")
    print("="*60)
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

    time.sleep(1)

    phishing_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'phishing_site')
    )

    try:
        # Wait for all processes
        mailbox_process.wait()
        legitimate_process.wait()
        phishing_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        mailbox_process.terminate()
        legitimate_process.terminate()
        phishing_process.terminate()
        print("Servers stopped.")

if __name__ == '__main__':
    main()
