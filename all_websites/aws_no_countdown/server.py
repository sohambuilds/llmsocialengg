from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import json, os

app = Flask(__name__)
CORS(app)

PORT = 5109
ENV_LABEL = "E38 — AWS Cloud Billing (Calm)"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captured_data.json")


def ensure_captured_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            json.dump({"entries": []}, f, indent=2)


def save_captured(entry: dict):
    ensure_captured_file()
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
    data['entries'].append(entry)
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@app.route("/")
def index():
    return send_file("AWS.html")


@app.route("/api/log", methods=["POST"])
def log_data():
    data = request.get_json(silent=True) or {}
    entry = {
        "timestamp": datetime.now().isoformat(),
        "environment": ENV_LABEL,
        "attack_type": data.get("attack_type", "cloud_billing_extortion"),
        "captured_data": data,
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
    }
    save_captured(entry)
    print(f"\n{'='*60}")
    print(f"[E38 AWS Calm] Log captured at {entry['timestamp']}")
    print(f"  Attack type : {entry['attack_type']}")
    for k, v in data.items():
        if k != "attack_type":
            print(f"  {k}: {v}")
    print(f"{'='*60}\n")
    return jsonify({"status": "logged"}), 200


@app.route("/api/captured", methods=["GET"])
def view_logs():
    ensure_captured_file()
    with open(LOG_FILE, 'r') as f:
        return jsonify(json.load(f)), 200


@app.route("/api/clear", methods=["GET", "POST"])
def clear_logs():
    ensure_captured_file()
    with open(LOG_FILE, "w") as f:
        json.dump({"entries": []}, f, indent=2)
    return jsonify({"status": "cleared"}), 200


if __name__ == "__main__":
    print("=" * 60)
    print(f"  {ENV_LABEL}")
    print(f"  http://localhost:{PORT}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=True)
