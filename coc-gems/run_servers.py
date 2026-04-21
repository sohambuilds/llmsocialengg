"""
COC Gems Scam Benchmark - Server Runner

Launches the search-engine entry point and the three phishing sub-sites on
four distinct ports so the agent sees genuinely different origins when it
clicks search results:

  5051  searchly.com            (main search engine + info + supercell store)
  5058  cocgemshub.com          (gems generator phishing)
  5059  supercell-rewards.net   (supercell credential phishing)
  5060  gamerewards-hub.com     (survey/verification phishing)

Usage: python coc-gems/run_servers.py
"""

import os
import subprocess
import sys
import time


SERVERS = [
    ("Search engine (searchly.com)",           "app.py",                 5051),
    ("Gems generator (cocgemshub.com)",        "phishing_generator.py",  5058),
    ("Supercell login (supercell-rewards.net)", "phishing_login.py",      5059),
    ("Survey verify (gamerewards-hub.com)",    "phishing_survey.py",     5060),
]


def main() -> None:
    base = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("COC Gems Scam Benchmark - Server Runner")
    print("=" * 60)
    for label, _, port in SERVERS:
        print(f"  {label:44s} http://localhost:{port}")
    print()
    print("Flow: agent lands on search engine, clicks a result, is sent to")
    print("one of the three phishing ports (distinct origins).")
    print("=" * 60)
    print()

    processes = []
    try:
        for _, script, _ in SERVERS:
            proc = subprocess.Popen(
                [sys.executable, script],
                cwd=base,
            )
            processes.append(proc)
            time.sleep(0.4)

        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down coc-gems servers...")
        for proc in processes:
            try:
                proc.terminate()
            except Exception:
                pass
        print("Stopped.")


if __name__ == "__main__":
    main()
