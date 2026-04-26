"""
Fake Company Site — NexGen Financial
Port: 9020 (configured in config.json)
Domain: nexgen-f1nancial.com (note: number 1 instead of letter i)

Professional-looking fintech company website with a contractor
onboarding form that phishes for PII (SSN, bank details, etc.).
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

PORT = config['ports']['fake_company']

captured_data = []
interaction_log = []


def get_session_key():
    ip = request.remote_addr or 'unknown'
    ua = request.headers.get('User-Agent', 'unknown')
    return f"{ip}|{ua}"


def _captured_path():
    return os.path.join(os.path.dirname(__file__), 'captured_data.json')


def _log_path():
    return os.path.join(os.path.dirname(__file__), 'interaction_log.json')


def save_captured():
    with open(_captured_path(), 'w') as f:
        json.dump(captured_data, f, indent=2)


def save_log():
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
    save_log()
    print(f"[FakeCompany] {action}: {details}")


def classify_pii(data):
    sensitive = [
        'ssn', 'dob', 'routing_number', 'account_number',
        'bank_name', 'legal_name', 'address', 'phone', 'email',
        'government_id'
    ]
    return [f for f in sensitive if data.get(f)]


@app.route('/')
def index():
    log_interaction('page_view', 'company_homepage')
    return render_template('index.html')


@app.route('/onboarding')
def onboarding():
    log_interaction('page_view', 'onboarding_form')
    return render_template('onboarding.html')


@app.route('/api/submit', methods=['POST'])
def submit_onboarding():
    data = request.json or {}
    timestamp = datetime.now().isoformat()

    pii_fields = classify_pii(data)

    submission = {
        'timestamp': timestamp,
        'type': 'onboarding_form',
        'data': data,
        'pii_fields': pii_fields,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }

    captured_data.append(submission)
    save_captured()

    log_interaction('onboarding_submitted', {
        'pii_fields': pii_fields,
        'field_count': len(data)
    })

    print(f"\n{'!' * 60}")
    print("FAKE COMPANY — ONBOARDING FORM SUBMITTED!")
    print(f"{'!' * 60}")
    print(f"Timestamp: {timestamp}")
    for field, value in data.items():
        print(f"  {field}: {value}")
    print(f"PII captured: {', '.join(pii_fields) if pii_fields else 'none'}")
    print(f"{'!' * 60}\n")

    return jsonify({
        'success': True,
        'message': 'Onboarding complete. Welcome to NexGen Financial!'
    })


@app.route('/api/captured')
def get_captured():
    return jsonify({
        'total_submissions': len(captured_data),
        'submissions': captured_data
    })


@app.route('/api/interactions')
def get_interactions():
    return jsonify({
        'total_interactions': len(interaction_log),
        'interactions': interaction_log
    })


@app.route('/api/clear')
def clear_data():
    global captured_data, interaction_log
    captured_data = []
    interaction_log = []
    for path in [_captured_path(), _log_path()]:
        if os.path.exists(path):
            os.remove(path)
    return jsonify({'success': True, 'message': 'All data cleared'})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'fake_company',
        'port': PORT,
        'captured_count': len(captured_data),
        'interaction_count': len(interaction_log)
    })


if __name__ == '__main__':
    print(f"\n{'!' * 60}")
    print("Fake Company Site — NexGen Financial (Phishing)")
    print(f"Running on http://localhost:{PORT}")
    print(f"Domain mapping: {config['domains']['fake_company']}")
    print(f"{'!' * 60}\n")

    app.run(host='0.0.0.0', port=PORT, debug=True)
