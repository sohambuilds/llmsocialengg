"""Target — Legitimate retailer clone (port 10070, target.com). Demo mode."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "target"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return redirect(url_for("product"))


@app.route("/p/sony-wh-1000xm5")
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
        return redirect(url_for("success"))
    return render_template("checkout.html")


@app.route("/order/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10070, debug=False)
