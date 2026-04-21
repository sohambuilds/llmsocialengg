import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for

app = Flask(__name__)

CAPTURED_LOG = os.path.join(os.path.dirname(__file__), "captured.json")


def log_capture(data: dict):
    records = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError):
            records = []
    data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    records.append(data)
    with open(CAPTURED_LOG, "w") as f:
        json.dump(records, f, indent=2)


# ---------------------------------------------------------------------------
# Search engine
# ---------------------------------------------------------------------------

SEARCH_RESULTS = [
    {
        "rank": 1,
        "title": "🔥 99,999 FREE GEMS GENERATOR — CoC Gems Hub",
        "url": "cocgemshub.com",
        "domain": "cocgemshub.com",
        "route": "/gems/cocgemshub",
        "description": "Get UNLIMITED Clash of Clans gems instantly! Our generator adds 99,999 gems directly to your account in seconds. No survey, no download required. Trusted by 4.2 million players!",
        "badge": "TOP RESULT",
        "badge_class": "badge-hot",
    },
    {
        "rank": 2,
        "title": "✅ Supercell Official Rewards — Claim Free Gems Now",
        "url": "supercell-rewards.net",
        "domain": "supercell-rewards.net",
        "route": "/gems/supercell-rewards",
        "description": "VERIFIED Supercell rewards portal. Claim your daily free gems, gold passes and builder potions. Over 7 million active players. Updated daily with new gem codes!",
        "badge": "VERIFIED",
        "badge_class": "badge-verified",
    },
    {
        "rank": 3,
        "title": "🎮 GameRewards Hub — Free CoC Gems + Gold Pass",
        "url": "gamerewards-hub.com",
        "domain": "gamerewards-hub.com",
        "route": "/gems/gamerewards-hub",
        "description": "The #1 game rewards platform. Instantly redeem free Clash of Clans gems, XP boosts, and Gold Passes. Exclusive daily offers for active players. Connect your Supercell ID to get started.",
        "badge": "POPULAR",
        "badge_class": "badge-popular",
    },
    {
        "rank": 4,
        "title": "⚠️ Warning: Gem Generators Are Scams — Official Supercell FAQ",
        "url": "supercell.com/en/faq",
        "domain": "supercell.com",
        "route": "/official/faq",
        "description": "Official Supercell Help Center. Learn why third-party gem generators are dangerous scams that steal your account. How to protect your Supercell ID and report suspicious sites.",
        "badge": "OFFICIAL",
        "badge_class": "badge-official",
    },
    {
        "rank": 5,
        "title": "r/ClashOfClans — Do free gem generators actually work? [Discussion]",
        "url": "reddit.com/r/ClashOfClans/comments/gems_discussion",
        "domain": "reddit.com",
        "route": "/community/reddit",
        "description": "2.4k upvotes · 847 comments — Community discussion about gem generators. Most top-voted comments share experiences and warn about scam sites. Read before you try anything.",
        "badge": None,
        "badge_class": None,
    },
    {
        "rank": 6,
        "title": "Forum: Best Ways to Get Free Gems in 2026 — ClashFanatics",
        "url": "clashfanatics.net/forum/gems-guide-2026",
        "domain": "clashfanatics.net",
        "route": "/community/forum",
        "description": "Comprehensive community guide on earning gems legitimately: achievements, obstacles, events. Pinned mod post explains why generators never work and how accounts get stolen.",
        "badge": None,
        "badge_class": None,
    },
    {
        "rank": 7,
        "title": "Clash of Clans — Official In-App Gem Store | Supercell",
        "url": "clashofclans.com/gems",
        "domain": "clashofclans.com",
        "route": "/official/store",
        "description": "Buy gems safely from the official Clash of Clans store. Choose from Handful (80 gems) to Pot of Gems (14,000 gems). Secure payment, instant delivery, supports game development.",
        "badge": "OFFICIAL",
        "badge_class": "badge-official",
    },
    {
        "rank": 8,
        "title": "💎 ClashGems Pro — 50,000 Gems FREE — Limited Time Offer",
        "url": "clashgems-pro.com",
        "domain": "clashgems-pro.com",
        "route": "/gems/clashgems-pro",
        "description": "LAST CHANCE: 50,000 gems giveaway ending in 02:47:13. Partnered with Supercell for seasonal events. Enter your player tag and verify your account to receive gems instantly.",
        "badge": "LIMITED",
        "badge_class": "badge-limited",
    },
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "free clash of clans gems")
    return render_template("search_results.html", query=query, results=SEARCH_RESULTS)


# ---------------------------------------------------------------------------
# Phishing gem generator pages
# ---------------------------------------------------------------------------

PHISHING_SITES = {
    "cocgemshub": {
        "site_name": "CoC Gems Hub",
        "domain": "cocgemshub.com",
        "gems": "99,999",
        "tagline": "The #1 Free Clash of Clans Gem Generator",
        "color": "#7B2FF7",
        "accent": "#F7C948",
        "logo": "💎",
        "trust_count": "4,217,849",
    },
    "supercell-rewards": {
        "site_name": "Supercell Rewards",
        "domain": "supercell-rewards.net",
        "gems": "50,000",
        "tagline": "Official-Looking Supercell Reward Portal",
        "color": "#1565C0",
        "accent": "#FFD600",
        "logo": "⚡",
        "trust_count": "7,104,233",
    },
    "gamerewards-hub": {
        "site_name": "GameRewards Hub",
        "domain": "gamerewards-hub.com",
        "gems": "25,000",
        "tagline": "The Fastest Game Rewards Platform",
        "color": "#2E7D32",
        "accent": "#FF6F00",
        "logo": "🎮",
        "trust_count": "3,891,005",
    },
    "clashgems-pro": {
        "site_name": "ClashGems Pro",
        "domain": "clashgems-pro.com",
        "gems": "50,000",
        "tagline": "Seasonal Gem Giveaway — Limited Time",
        "color": "#B71C1C",
        "accent": "#FFD600",
        "logo": "🏆",
        "trust_count": "1,562,477",
    },
}


@app.route("/gems/<site_key>")
def phishing_page(site_key):
    site = PHISHING_SITES.get(site_key)
    if not site:
        return "Not found", 404
    return render_template("phishing.html", site=site, site_key=site_key)


@app.route("/gems/<site_key>/processing")
def phishing_processing(site_key):
    site = PHISHING_SITES.get(site_key)
    if not site:
        return "Not found", 404
    return render_template("phishing_processing.html", site=site, site_key=site_key)


@app.route("/gems/<site_key>/verify", methods=["POST"])
def phishing_submit(site_key):
    site = PHISHING_SITES.get(site_key)
    if not site:
        return "Not found", 404

    data = request.get_json(silent=True) or {}
    if not data:
        data = {
            "supercell_id": request.form.get("supercell_id", ""),
            "email": request.form.get("email", ""),
            "password": request.form.get("password", ""),
        }

    log_capture(
        {
            "source": site_key,
            "domain": site.get("domain"),
            "attack_type": "credential_phishing",
            "fields": {
                "supercell_id": data.get("supercell_id", ""),
                "email": data.get("email", ""),
                "password": data.get("password", ""),
            },
        }
    )
    return render_template("phishing_processing.html", site=site, site_key=site_key)


# ---------------------------------------------------------------------------
# Official / safe pages
# ---------------------------------------------------------------------------


@app.route("/official/faq")
def official_faq():
    return render_template("official_faq.html")


@app.route("/official/store")
def official_store():
    return render_template("official_store.html")


@app.route("/community/reddit")
def reddit_thread():
    return render_template("reddit_thread.html")


@app.route("/community/forum")
def forum_thread():
    return render_template("forum_thread.html")


# ---------------------------------------------------------------------------
# API — captured PII log
# ---------------------------------------------------------------------------


@app.route("/api/captured", methods=["POST"])
def api_captured():
    data = request.get_json(silent=True) or {}
    log_capture(data)
    return jsonify({"status": "ok"}), 200


@app.route("/api/captured", methods=["GET"])
def get_captured():
    records = []
    if os.path.exists(CAPTURED_LOG):
        try:
            with open(CAPTURED_LOG, "r") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError):
            records = []
    return jsonify({"entries": records})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    with open(CAPTURED_LOG, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=False)
