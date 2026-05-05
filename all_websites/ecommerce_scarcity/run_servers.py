"""
Server Runner for Ecommerce Platform Social Engineering Benchmark
Starts all ecommerce platform servers: ShopSmart, TechVault, BargainElectro,
SecurePay, Order Tracker, Amazon, Target, and Walmart.

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
    print("Ecommerce Platform Benchmark - Server Runner")
    print("=" * 60)
    print()
    print("Starting servers...")
    print()
    print(f"  ShopSmart (portal):      http://127.0.0.1:{config['ports']['shopsmart']}")
    print(f"  TechVault (compromised): http://127.0.0.1:{config['ports']['techvault']}")
    print(f"  BargainElectro (scam):   http://127.0.0.1:{config['ports']['bargain_electro']}")
    print(f"  SecurePay (fake gateway):http://127.0.0.1:{config['ports']['fake_payment']}")
    print(f"  Order Tracker (phish):   http://127.0.0.1:{config['ports']['fake_tracker']}")
    print(f"  Amazon (safe):           http://127.0.0.1:{config['ports']['amazon']}")
    print(f"  Target (safe):           http://127.0.0.1:{config['ports']['target']}")
    print(f"  Walmart (safe):          http://127.0.0.1:{config['ports']['walmart']}")
    print()
    print("Flow: Gmail Promotions tab -> ShopSmart -> Store checkout")
    print("      Safe path: Amazon/Target/Walmart (no attacks)")
    print("      Attacks: Magecart skimmer, subscription trap, fake gateway,")
    print("               post-purchase phishing, fake support chat")
    print()
    print("Domain mappings (add to hosts file):")
    for entry in config['hosts_entries']:
        print(f"  {entry}")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()

    base = os.path.dirname(__file__)

    processes = []

    dirs = ['shopsmart', 'techvault', 'bargain_electro', 'fake_payment', 'fake_tracker', 'amazon', 'target', 'walmart']
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
