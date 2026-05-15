"""
Server Runner for Ecommerce Platform Social Engineering Benchmark
Starts all ecommerce platform servers: ShopSmart, TechVault, BargainElectro,
SecurePay, Order Tracker, Amazon, Target, and Walmart.

Usage: python run_servers.py
"""

import importlib.util
import json
import os
import sys
import threading


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def run_flask_app(app_path, module_name):
    """Load and run a Flask app from app_path in this thread."""
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod  # register so Flask can resolve __file__ -> root_path
    spec.loader.exec_module(mod)
    mod.app.run(host='0.0.0.0', port=mod.PORT, debug=False, use_reloader=False, threaded=True)


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

    base = os.path.dirname(os.path.abspath(__file__))

    dirs = [
        ('shopsmart',      'ecom_shopsmart_app'),
        ('techvault',      'ecom_techvault_app'),
        ('bargain_electro','ecom_bargain_electro_app'),
        ('fake_payment',   'ecom_fake_payment_app'),
        ('fake_tracker',   'ecom_fake_tracker_app'),
        ('amazon',         'ecom_amazon_app'),
        ('target',         'ecom_target_app'),
        ('walmart',        'ecom_walmart_app'),
    ]

    threads = []
    for sub_dir, module_name in dirs:
        app_path = os.path.join(base, sub_dir, 'app.py')
        t = threading.Thread(target=run_flask_app, args=(app_path, module_name), daemon=True)
        t.start()
        threads.append(t)
        print(f"  Started: {module_name}")

    print()
    print("All servers running. Press Ctrl+C to stop.")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        print("Servers stopped.")


if __name__ == '__main__':
    main()
