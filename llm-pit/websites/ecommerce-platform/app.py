"""app.py — Convenience entry point. Delegates to run_servers.py."""

import runpy
import os

if __name__ == "__main__":
    runpy.run_path(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_servers.py"),
        run_name="__main__",
    )
