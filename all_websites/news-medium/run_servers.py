"""
Server Runner for News Content Site (Medium PII variant)
Starts the news site only — no billing portal.
The medium-PII attack surface is the newsletter signup, which collects
email + employer + industry + job_title with a pre-ticked marketing-consent
dark pattern. No critical PII (CC, SSN, bank, password) is asked anywhere.
"""

import json
import subprocess
import sys
import os


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    config = load_config()

    print("=" * 60)
    print("LLM PII Benchmark - News Site (Medium PII)")
    print("=" * 60)
    print()
    print(f"  News Site: http://localhost:{config['ports']['news_site']}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    news_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base_dir, 'news_site')
    )

    try:
        news_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        news_process.terminate()


if __name__ == '__main__':
    main()
