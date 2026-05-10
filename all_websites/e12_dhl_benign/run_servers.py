"""Server Runner for e12_dhl_benign — Benign Twin."""
import json, os, subprocess, sys, time

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path) as f: config = json.load(f)
    print("=" * 60)
    print("e12_dhl_benign — Benign Twin Server Runner")
    print("=" * 60)
    print(f"  Mailbox:  http://localhost:{config['ports']['mailbox']}")
    print(f"  DHL:      http://localhost:{config['ports']['dhl']}")
    print("Benign: legitimate DHL tracking, no customs fee CC form.\n")
    base = os.path.dirname(__file__)
    p1 = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'mailbox'))
    time.sleep(1)
    p2 = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'dhl_legit'))
    try: p1.wait(); p2.wait()
    except KeyboardInterrupt: p1.terminate(); p2.terminate()

if __name__ == '__main__': main()
