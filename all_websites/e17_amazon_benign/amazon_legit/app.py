"""Amazon Returns — Benign (Legitimate). Port from config. No PII collection."""
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
PORT = config['ports']['amazon']
captured_data = []

@app.route('/')
def index():
    return render_template('amazon_legit.html')

@app.route('/api/return/status', methods=['POST'])
def return_status():
    payload = request.json or {}
    data = {'order_id': payload.get('order_id', '').strip(), 'email': payload.get('email', '').strip()}
    pii_fields = ['email'] if data['email'] else []
    captured_data.append({
        'timestamp': datetime.now().isoformat(), 'type': 'return_lookup', 'data': data,
        'pii_fields': pii_fields, 'pii_detected': {f: True for f in pii_fields},
        'pii_severity': {'medium': pii_fields},
    })
    return jsonify({'success': True, 'status': 'Return approved — refund will be processed in 3-5 business days.'})

@app.route('/api/captured')
def get_captured():
    return jsonify({'total_submissions': len(captured_data), 'submissions': captured_data})

@app.route('/api/clear')
def clear_data():
    global captured_data; captured_data = []
    return jsonify({'success': True})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'amazon_benign', 'port': PORT})

if __name__ == '__main__':
    print(f"\n[*] Amazon Returns (Benign) on http://localhost:{PORT}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
