"""
Server Runner for freelance_benign — Benign Twin
Starts only the FreelanceHub platform (no fake_company or fake_docusign).
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
    print("Freelance Platform (Benign Twin) - Server Runner")
    print("=" * 60)
    print()
    print(f"  FreelanceHub:  http://localhost:{config['ports']['freelancehub']}")
    print()
    print("Benign twin: legit freelance hub only, no fake company or DocuSign.")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)

    hub_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=os.path.join(base, 'freelancehub')
    )

    try:
        hub_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        hub_process.terminate()
        print("Stopped.")


if __name__ == '__main__':
    main()
