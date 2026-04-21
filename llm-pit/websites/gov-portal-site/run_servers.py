"""
Gov Portal - IRS Phishing Benchmark
Starts two Flask servers:
  - Mailbox     -> http://localhost:8050
  - IRS Phishing Portal -> http://localhost:8051
"""
import subprocess
import sys
import os
import signal
import time


BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    print("[gov_portal] Starting IRS phishing benchmark servers...")

    mailbox_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "mailbox", "app.py")],
        cwd=os.path.join(BASE, "mailbox"),
    )
    time.sleep(0.8)

    phishing_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "phishing_site", "app.py")],
        cwd=os.path.join(BASE, "phishing_site"),
    )

    print("[gov_portal] Email Inbox        -> http://localhost:8050")
    print("[gov_portal] IRS Phishing Portal -> http://localhost:8051  (domain: irs-tax-refunds.com)")
    print("[gov_portal] Press Ctrl+C to stop both servers.\n")

    def _stop(sig, frame):
        print("\n[gov_portal] Stopping servers...")
        mailbox_proc.terminate()
        phishing_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    mailbox_proc.wait()
    phishing_proc.wait()


if __name__ == "__main__":
    main()
