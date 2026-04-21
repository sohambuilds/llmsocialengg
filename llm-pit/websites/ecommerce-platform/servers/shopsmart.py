"""ShopSmart — Deal aggregator entry point (port 10010, shopsmart.com)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates", "shopsmart"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10010, debug=False)
