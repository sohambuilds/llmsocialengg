"""
ShopSmart - Price Comparison / Deal Aggregator
Port: 10010 (configured in config.json)
Domain: shopsmart.com

Entry point for the ecommerce social engineering benchmark.
Aggregates product listings from multiple stores (some legitimate, some malicious).
Also serves post-purchase phishing notifications.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

PORT = config['ports']['shopsmart']

products_path = os.path.join(os.path.dirname(__file__), 'products.json')
with open(products_path, 'r', encoding='utf-8') as f:
    products = json.load(f)

notifications_path = os.path.join(os.path.dirname(__file__), 'notifications.json')
with open(notifications_path, 'r', encoding='utf-8') as f:
    notifications = json.load(f)

captured_data = []
interaction_log = []
purchase_completed = False


def _log_path():
    return os.path.join(os.path.dirname(__file__), 'interaction_log.json')


def _captured_path():
    return os.path.join(os.path.dirname(__file__), 'captured_data.json')


def save_interaction_log():
    with open(_log_path(), 'w') as f:
        json.dump(interaction_log, f, indent=2)


def save_captured():
    with open(_captured_path(), 'w') as f:
        json.dump(captured_data, f, indent=2)


def log_interaction(action, details):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else None
    }
    interaction_log.append(entry)
    save_interaction_log()
    print(f"[ShopSmart] {action}: {details}")


# ── Page routes ──────────────────────────────────────────────

@app.route('/')
def dashboard():
    log_interaction('page_view', 'dashboard')
    return render_template('dashboard.html',
                           product=products['target_product'],
                           listings=products['listings'],
                           reviews=products['reviews'],
                           config=config)


@app.route('/product/<listing_id>')
def product_detail(listing_id):
    listing = next((l for l in products['listings'] if l['id'] == listing_id), None)
    if not listing:
        return "Listing not found", 404

    log_interaction('product_view', {
        'listing_id': listing_id,
        'store': listing['store_name'],
        'is_malicious': listing.get('is_malicious', False)
    })

    store_reviews = products['reviews'].get(listing_id, [])
    return render_template('product.html',
                           product=products['target_product'],
                           listing=listing,
                           reviews=store_reviews,
                           config=config)


@app.route('/notifications')
def notifications_page():
    global purchase_completed
    log_interaction('page_view', 'notifications')

    visible = [n for n in notifications if not n.get('triggered_after_purchase') or purchase_completed]
    return render_template('notifications.html',
                           notifications=visible,
                           config=config)


# ── API routes ───────────────────────────────────────────────

@app.route('/api/purchase-complete', methods=['POST'])
def mark_purchase_complete():
    """Called by store checkout pages to trigger post-purchase notifications."""
    global purchase_completed
    purchase_completed = True

    data = request.json or {}
    log_interaction('purchase_completed', {
        'store': data.get('store', 'unknown'),
        'order_id': data.get('order_id', 'unknown')
    })
    return jsonify({'success': True})


@app.route('/api/log', methods=['POST'])
def log_event():
    data = request.json or {}
    log_interaction(data.get('action', 'unknown'), data.get('details', {}))
    return jsonify({'success': True})


@app.route('/api/captured')
def get_captured():
    return jsonify({
        'total_entries': len(captured_data),
        'entries': captured_data
    })


@app.route('/api/interactions')
def get_interactions():
    return jsonify({
        'total_interactions': len(interaction_log),
        'interactions': interaction_log
    })


@app.route('/api/clear')
def clear_data():
    global captured_data, interaction_log, purchase_completed
    captured_data = []
    interaction_log = []
    purchase_completed = False

    for path in [_log_path(), _captured_path()]:
        if os.path.exists(path):
            os.remove(path)

    return jsonify({'success': True, 'message': 'All data cleared'})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'shopsmart',
        'port': PORT,
        'captured_count': len(captured_data),
        'interaction_count': len(interaction_log)
    })


if __name__ == '__main__':
    print(f"\n{'=' * 60}")
    print("ShopSmart - Price Comparison Aggregator")
    print(f"Running on http://localhost:{PORT}")
    print(f"Domain mapping: {config['domains']['shopsmart']}")
    print(f"{'=' * 60}\n")

    app.run(host='0.0.0.0', port=PORT, debug=True)
