"""
Server Runner for ecommerce_benign — Benign Twin
Starts only the legitimate stores: ShopSmart, Amazon, Target, Walmart.
No bargain_electro, fake_payment, fake_tracker, or techvault.
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
    print("Ecommerce Platform (Benign Twin) - Server Runner")
    print("=" * 60)
    print()
    print(f"  ShopSmart (portal):  http://127.0.0.1:{config['ports']['shopsmart']}")
    print(f"  Amazon (safe):       http://127.0.0.1:{config['ports']['amazon']}")
    print(f"  Target (safe):       http://127.0.0.1:{config['ports']['target']}")
    print(f"  Walmart (safe):      http://127.0.0.1:{config['ports']['walmart']}")
    print()
    print("Benign twin: only legitimate stores, no scam sites.")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)

    processes = []
    dirs = ['shopsmart', 'amazon', 'target', 'walmart']
    for d in dirs:
        p = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd=os.path.join(base, d)
        )
        processes.append(p)
        time.sleep(1)

    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        for p in processes:
            p.terminate()
        print("Servers stopped.")


if __name__ == '__main__':
    main()
