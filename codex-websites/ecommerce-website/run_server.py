"""
Run the e-commerce checkout benchmark server.
Usage: python run_server.py
"""

import os
import subprocess
import sys


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print('=' * 60)
    print('LLM Social Engineering Benchmark - E-commerce Checkout')
    print('=' * 60)
    print('Checkout app: http://localhost:8060')
    print('Press Ctrl+C to stop')
    print('=' * 60)

    process = subprocess.Popen([sys.executable, 'app.py'], cwd=base_dir)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == '__main__':
    main()
