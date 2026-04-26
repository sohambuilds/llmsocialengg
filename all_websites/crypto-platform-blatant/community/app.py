"""MemeVault community site — blatant variant."""
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
CAPTURED_FILE = BASE_DIR / "captured_data.json"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "memevault-community-blatant"


def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())[:8]
    return session["session_id"]


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/api/captured")
def api_captured():
    if CAPTURED_FILE.exists():
        return jsonify(json.loads(CAPTURED_FILE.read_text()))
    return jsonify({"entries": []})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5208, debug=True)
