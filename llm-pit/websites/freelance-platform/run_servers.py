"""
Freelance Platform - Conversational Deception Benchmark
Starts three Flask servers:
  - FreelanceHub      -> http://localhost:9010
  - NexGen Financial  -> http://localhost:9020  (fake company, typosquatted)
  - Fake DocuSign     -> http://localhost:9030  (fake NDA signing portal)
"""
import subprocess
import sys
import os
import signal
import time


BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    print("[freelance] Starting freelance platform benchmark servers...")

    hub_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "freelancehub", "app.py")],
        cwd=os.path.join(BASE, "freelancehub"),
    )
    time.sleep(0.8)

    nexgen_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "nexgen_financial", "app.py")],
        cwd=os.path.join(BASE, "nexgen_financial"),
    )
    time.sleep(0.5)

    docusign_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "fake_docusign", "app.py")],
        cwd=os.path.join(BASE, "fake_docusign"),
    )

    print("[freelance] FreelanceHub       -> http://localhost:9010")
    print("[freelance] NexGen Financial   -> http://localhost:9020  (domain: nexgen-f1nancial.com)")
    print("[freelance] Fake DocuSign      -> http://localhost:9030  (domain: docu-sign-secure.com)")
    print("[freelance] Press Ctrl+C to stop all servers.\n")

    def _stop(sig, frame):
        print("\n[freelance] Stopping servers...")
        hub_proc.terminate()
        nexgen_proc.terminate()
        docusign_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    hub_proc.wait()
    nexgen_proc.wait()
    docusign_proc.wait()


if __name__ == "__main__":
    main()
