"""Server Runner for e17_amazon_benign — Benign Twin."""
import json, os, subprocess, sys, time

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path) as f: config = json.load(f)
    print("=" * 60)
    print("e17_amazon_benign — Benign Twin Server Runner")
    print("=" * 60)
    print(f"  Mailbox:    http://localhost:{config['ports']['mailbox']}")
    print(f"  Amazon:     http://localhost:{config['ports']['amazon']}")
    print("Benign: legitimate Amazon returns page, no SSN/DOB.\n")
    base = os.path.dirname(__file__)
    p1 = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'mailbox'))
    time.sleep(1)
    p2 = subprocess.Popen([sys.executable, 'app.py'], cwd=os.path.join(base, 'amazon_legit'))
    try: p1.wait(); p2.wait()
    except KeyboardInterrupt: p1.terminate(); p2.terminate()

if __name__ == '__main__': main()
