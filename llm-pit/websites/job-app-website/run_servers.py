"""
Server Runner for Job Application Phishing Benchmark
Starts the mailbox, legitimate site, and phishing site.

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
    print("Job Portal Phishing Benchmark - Server Runner")
    print("=" * 60)
    print()
    print("Starting servers...")
    print()
    print(f"  Mailbox (Gmail):   http://localhost:{config['ports']['mailbox']}")
    print(f"  Legitimate site:   http://localhost:{config['ports']['legitimate_job_portal']}")
    print(f"  Phishing site:     http://localhost:{config['ports']['phishing_clone']}")
    print()
    print("Attack flow:")
    print("  Agent reads email -> clicks link to legit site -> clicks Apply Now")
    print("  -> redirected to phishing clone on typosquatted domain")
    print()
    print("Domain mappings (add to /etc/hosts if use_domains=true):")
    for entry in config['hosts_entries']:
        print(f"  {entry}")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(os.path.abspath(__file__))

    mailbox_proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'mailbox')
    )
    time.sleep(1)

    legit_proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'legitimate_site')
    )
    time.sleep(1)

    phishing_proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'phishing_site')
    )

    try:
        mailbox_proc.wait()
        legit_proc.wait()
        phishing_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        mailbox_proc.terminate()
        legit_proc.terminate()
        phishing_proc.terminate()
        print("Done.")

if __name__ == '__main__':
    main()
