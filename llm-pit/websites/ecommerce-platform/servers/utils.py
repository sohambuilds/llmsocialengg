"""Shared utilities for all e-commerce benchmark servers."""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURED_LOG = os.path.join(BASE_DIR, "captured.json")


def load_log():
    if os.path.exists(CAPTURED_LOG):
        with open(CAPTURED_LOG, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_log(entries):
    with open(CAPTURED_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def log_captured(server_name, port, domain, request_obj, fields):
    """Append a PII capture event to the central log."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "server": server_name,
        "port": port,
        "domain": domain,
        "ip": request_obj.remote_addr,
        "user_agent": request_obj.headers.get("User-Agent", ""),
        "fields": fields,
    }
    log = load_log()
    log.append(entry)
    save_log(log)
    return entry
