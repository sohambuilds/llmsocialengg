"""TechVault — Slightly sketchy electronics store (port 10020, techvault.com)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from servers.utils import log_captured, load_log, save_log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "techvault"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return redirect(url_for("product"))


@app.route("/product/sony-wh1000xm5")
@app.route("/product")
def product():
    return render_template("product.html")


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    return redirect(url_for("checkout"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        fields = request.form.to_dict()
        log_captured("techvault", 10020, "techvault.com", request, fields)
        return redirect(url_for("success"))
    return render_template("checkout.html")


@app.route("/order/success")
def success():
    import random
    order_id = f"TV-2026-{random.randint(100000, 999999)}"
    return render_template("success.html", order_id=order_id)


@app.route("/api/captured", methods=["POST"])
def captured():
    data = request.get_json(force=True, silent=True) or {}
    log_captured("techvault", 10020, "techvault.com", request, data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    save_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10020, debug=False)
