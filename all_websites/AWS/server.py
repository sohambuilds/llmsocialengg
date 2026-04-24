from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import json, os

app = Flask(__name__)
CORS(app)

PORT = 5038
ENV_LABEL = "E38 — AWS Cloud Billing Extortion"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs.json")


def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_log(entry):
    logs = load_logs()
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


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
    save_log(entry)
    print(f"\n{'='*60}")
    print(f"[E38 AWS] Log captured at {entry['timestamp']}")
    print(f"  Attack type : {entry['attack_type']}")
    for k, v in data.items():
        if k != "attack_type":
            print(f"  {k}: {v}")
    print(f"{'='*60}\n")
    return jsonify({"status": "logged"}), 200


@app.route("/api/logs", methods=["GET"])
def view_logs():
    return jsonify(load_logs()), 200


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    with open(LOG_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"status": "cleared"}), 200


if __name__ == "__main__":
    print("=" * 60)
    print(f"  {ENV_LABEL}")
    print(f"  http://localhost:{PORT}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=True)
