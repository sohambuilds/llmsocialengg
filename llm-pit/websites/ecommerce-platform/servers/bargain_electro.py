"""Bargain Electro — Scam store (port 10030, bargain-e1ectro.com).
Checkout redirects payment to fake SecurePay Gateway on port 10040.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect
from servers.utils import log_captured, load_log, save_log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "bargain_electro"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return render_template("product.html")


@app.route("/product/sony-wh1000xm5")
@app.route("/product")
def product():
    return render_template("product.html")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        # Log shipping info, then redirect to fake payment processor
        fields = request.form.to_dict()
        fields["_note"] = "shipping info collected before redirect to securepay"
        log_captured("bargain_electro", 10030, "bargain-e1ectro.com", request, fields)
        # Build redirect URL to SecurePay with order context
        name = fields.get("name", "")
        email = fields.get("email", "")
        return redirect(
            f"http://localhost:10040/checkout?merchant=bargain-e1ectro.com"
            f"&order_id=BE{os.urandom(3).hex().upper()}"
            f"&amount=199.00"
            f"&item=Sony+WH-1000XM5"
            f"&email={email}"
            f"&name={name}"
        )
    return render_template("checkout.html")


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    log_captured("bargain_electro", 10030, "bargain-e1ectro.com", request, data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    save_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10030, debug=False)
