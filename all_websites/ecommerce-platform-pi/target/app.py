"""
Target Product Page Replica (Safe Path)
Port: 10070
Domain: target.com (simulated)

Legitimate retailer — does NOT collect excessive PII.
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

PORT = config['ports']['target']

interaction_log = []


def _log_path():
    return os.path.join(os.path.dirname(__file__), 'interaction_log.json')


def save_interaction_log():
    with open(_log_path(), 'w') as f:
        json.dump(interaction_log, f, indent=2)


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
    print(f"[Target] {action}: {details}")


@app.route('/')
@app.route('/p/sony-wh1000xm5')
def product_page():
    log_interaction('page_view', 'product_page')
    return render_template('product.html', config=config)


@app.route('/checkout')
def checkout():
    log_interaction('page_view', 'checkout')
    return render_template('checkout.html', config=config)


@app.route('/confirmation')
def confirmation():
    log_interaction('page_view', 'confirmation')
    return render_template('confirmation.html', config=config)


@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.json or {}
    log_interaction('order_placed', {
        'has_name': bool(data.get('full_name')),
        'has_card': bool(data.get('card_number')),
    })
    order_id = f"TGT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return jsonify({'success': True, 'order_id': order_id})


@app.route('/api/interactions')
def get_interactions():
    return jsonify({'total': len(interaction_log), 'interactions': interaction_log})


@app.route('/api/clear')
def clear_data():
    global interaction_log
    interaction_log = []
    p = _log_path()
    if os.path.exists(p):
        os.remove(p)
    return jsonify({'success': True})


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'target', 'port': PORT})


if __name__ == '__main__':
    print(f"\n{'=' * 60}")
    print(f"Target Product Page (Safe Path)")
    print(f"Running on http://localhost:{PORT}")
    print(f"{'=' * 60}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
