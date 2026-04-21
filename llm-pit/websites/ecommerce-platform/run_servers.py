"""
run_servers.py - Start all 8 e-commerce benchmark servers in parallel.

Servers:
  10010  ShopSmart          (deal aggregator)
  10020  TechVault          (sketchy store - collects PII)
  10030  Bargain Electro    (scam store - redirects to fake payment processor)
  10040  SecurePay Gateway  (fake payment processor - collects card PII)
  10050  Order Tracker      (post-purchase PII harvest)
  10060  Amazon             (legitimate - demo mode)
  10070  Target             (legitimate - demo mode)
  10080  Walmart            (legitimate - demo mode)
"""

import multiprocessing
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def run_server(module_path, app_name, port):
    """Import and run a Flask app in a subprocess."""
    import importlib
    mod = importlib.import_module(module_path)
    flask_app = getattr(mod, app_name)
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


SERVERS = [
    ("servers.shopsmart",       "app", 10010, "ShopSmart (shopsmart.com)"),
    ("servers.techvault",       "app", 10020, "TechVault (techvault.com)"),
    ("servers.bargain_electro", "app", 10030, "Bargain Electro (bargain-e1ectro.com)"),
    ("servers.securepay",       "app", 10040, "SecurePay Gateway (securepay-gateway.net)"),
    ("servers.order_tracker",   "app", 10050, "Order Tracker (track.bargain-e1ectro.com)"),
    ("servers.amazon",          "app", 10060, "Amazon (amazon.com)"),
    ("servers.target",          "app", 10070, "Target (target.com)"),
    ("servers.walmart",         "app", 10080, "Walmart (walmart.com)"),
]


if __name__ == "__main__":
    print("=" * 60)
    print("  E-Commerce Phishing Benchmark -- Starting Servers")
    print("=" * 60)

    processes = []
    for module_path, app_name, port, label in SERVERS:
        p = multiprocessing.Process(
            target=run_server,
            args=(module_path, app_name, port),
            name=label,
            daemon=True,
        )
        p.start()
        processes.append(p)
        print(f"  [OK] {label:<45} -> http://localhost:{port}")

    print("=" * 60)
    print("  All servers running. Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        while True:
            time.sleep(1)
            # Restart any crashed processes
            for i, (p, (module_path, app_name, port, label)) in enumerate(
                zip(processes, SERVERS)
            ):
                if not p.is_alive():
                    print(f"  [RESTART] Restarting {label}...")
                    new_p = multiprocessing.Process(
                        target=run_server,
                        args=(module_path, app_name, port),
                        name=label,
                        daemon=True,
                    )
                    new_p.start()
                    processes[i] = new_p
    except KeyboardInterrupt:
        print("\n  Shutting down all servers...")
        for p in processes:
            p.terminate()
        print("  Done.")
