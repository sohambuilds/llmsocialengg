"""
Server Runner for News Content Site Benchmark (ENV 4)
Starts the news site and billing portal for testing.

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
    print("LLM PII Benchmark - News Content Site (ENV 4)")
    print("=" * 60)
    print()
    print("Starting servers...")
    print()
    print(f"  News Site:       http://localhost:{config['ports']['news_site']}")
    print(f"  Billing Portal:  http://localhost:{config['ports']['billing_portal']}")
    print()
    print("Flow: Agent opens news site -> cookie consent -> paywall/account")
    print("      -> billing portal (free trial) -> newsletter -> comment")
    print()
    print("Domain mappings (add to hosts file):")
    for entry in config['hosts_entries']:
        print(f"  {entry}")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    news_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base_dir, 'news_site')
    )

    time.sleep(1)

    billing_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base_dir, 'billing_portal')
    )

    try:
        news_process.wait()
        billing_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        news_process.terminate()
        billing_process.terminate()
        print("Servers stopped.")


if __name__ == '__main__':
    main()
