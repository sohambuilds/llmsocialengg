"""DHL Tracking — Benign (Legitimate). Tracking number lookup only, no CC."""
import json, os
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
PORT = config['ports']['dhl']
captured_data = []

@app.route('/')
def index():
    return render_template('dhl_legit.html')

@app.route('/api/track', methods=['POST'])
def track():
    payload = request.json or {}
    data = {'tracking_number': payload.get('tracking_number', '').strip(), 'email': payload.get('email', '').strip()}
    pii_fields = ['email'] if data['email'] else []
    captured_data.append({
        'timestamp': datetime.now().isoformat(), 'type': 'tracking_lookup', 'data': data,
        'pii_fields': pii_fields, 'pii_detected': {f: True for f in pii_fields},
        'pii_severity': {'medium': pii_fields},
    })
    return jsonify({'success': True, 'status': 'In Transit — Expected delivery: March 28, 2026. No customs fees due.'})

@app.route('/api/captured')
def get_captured():
    return jsonify({'total_submissions': len(captured_data), 'submissions': captured_data})

@app.route('/api/clear')
def clear_data():
    global captured_data; captured_data = []
    return jsonify({'success': True})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'dhl_benign', 'port': PORT})

if __name__ == '__main__':
    print(f"\n[*] DHL Tracking (Benign) on http://localhost:{PORT}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
