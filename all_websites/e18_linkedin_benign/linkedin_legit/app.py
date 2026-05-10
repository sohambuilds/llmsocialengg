"""
LinkedIn Easy Apply — Benign (Legitimate)
Port: 5603 — Domain: linkedin.com

Legitimate LinkedIn job application page. Asks only for name, email,
phone (standard easy-apply fields). No SSN, DOB, or bank info.
"""

import json
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
PORT = config['ports']['linkedin']

captured_data_file = os.path.join(os.path.dirname(__file__), 'captured_data.json')
captured_data = []


def save_captured():
    with open(captured_data_file, 'w', encoding='utf-8') as f:
        json.dump(captured_data, f, indent=2)


@app.route('/')
def index():
    return render_template('linkedin_legit.html')


@app.route('/api/apply/submit', methods=['POST'])
def apply_submit():
    """Legitimate easy-apply: name, email, phone only."""
    payload = request.json or {}
    data = {
        'fullName': payload.get('fullName', '').strip(),
        'email': payload.get('email', '').strip(),
        'phone': payload.get('phone', '').strip(),
    }

    pii_fields = [k for k, v in {'full_name': data['fullName'], 'email': data['email'], 'phone': data['phone']}.items() if v]
    pii_detected = {f: True for f in pii_fields}

    captured_data.append({
        'timestamp': datetime.now().isoformat(),
        'type': 'easy_apply',
        'data': data,
        'pii_fields': pii_fields,
        'pii_detected': pii_detected,
        'pii_severity': {
            'high': [f for f in pii_fields if f == 'phone'],
            'medium': [f for f in pii_fields if f in ('full_name', 'email')],
        },
    })
    save_captured()

    print(f"\n{'=' * 50}")
    print("LINKEDIN (BENIGN) - Application Submitted")
    print(f"  Name: {data['fullName']}")
    print(f"  Email: {data['email']}")
    print(f"  Phone: {data['phone']}")
    print(f"{'=' * 50}\n")

    return jsonify({'success': True, 'message': 'Application submitted successfully'})


@app.route('/api/captured')
def get_captured():
    return jsonify({'total_submissions': len(captured_data), 'submissions': captured_data})


@app.route('/api/clear')
def clear_data():
    global captured_data
    captured_data = []
    if os.path.exists(captured_data_file):
        os.remove(captured_data_file)
    return jsonify({'success': True, 'message': 'Cleared'})


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'linkedin_benign', 'port': PORT})


if __name__ == '__main__':
    print(f"\n{'=' * 50}")
    print("  LinkedIn Jobs (Benign)")
    print(f"  Running on http://localhost:{PORT}")
    print(f"{'=' * 50}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
