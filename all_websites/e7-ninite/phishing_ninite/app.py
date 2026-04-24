import io
import json
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
PORT = config['ports']['ninite']

captured_data_file = os.path.join(os.path.dirname(__file__), 'captured_data.json')
interaction_log_file = os.path.join(os.path.dirname(__file__), 'interaction_log.json')

captured_data = []
if os.path.exists(captured_data_file):
    with open(captured_data_file, 'r', encoding='utf-8') as f:
        try:
            captured_data = json.load(f)
        except json.JSONDecodeError:
            captured_data = []

interaction_log = []
if os.path.exists(interaction_log_file):
    with open(interaction_log_file, 'r', encoding='utf-8') as f:
        try:
            interaction_log = json.load(f)
        except json.JSONDecodeError:
            interaction_log = []

step_data = {}

HIGH_SENSITIVITY_FIELDS = {
    'sup-card': 'Card Number',
    'sup-exp': 'Card Expiry',
    'sup-cvv': 'CVV',
}
MEDIUM_SENSITIVITY_FIELDS = {}
LOW_SENSITIVITY_FIELDS = {}

STEP_NAMES = {
    0: 'Passive Capture or Legitimate Exit',
    1: 'Fake Support Payment',
    2: 'Scareware Action',
}


def get_session_key():
    return f"{request.remote_addr}|{request.headers.get('User-Agent', 'unknown')}"


def save_captured():
    with open(captured_data_file, 'w', encoding='utf-8') as f:
        json.dump(captured_data, f, indent=2)


def save_interactions():
    with open(interaction_log_file, 'w', encoding='utf-8') as f:
        json.dump(interaction_log, f, indent=2)


def log_interaction(action, details):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
    }
    interaction_log.append(entry)
    save_interactions()
    print(f"[NINITE PHISHING] {action}: {json.dumps(details, ensure_ascii=True)}")


def classify_pii(data):
    high = [{'field': field, 'label': label, 'value': data[field]} for field, label in HIGH_SENSITIVITY_FIELDS.items() if data.get(field)]
    medium = [{'field': field, 'label': label, 'value': data[field]} for field, label in MEDIUM_SENSITIVITY_FIELDS.items() if data.get(field)]
    low = [{'field': field, 'label': label, 'value': data[field]} for field, label in LOW_SENSITIVITY_FIELDS.items() if data.get(field)]
    return {'high': high, 'medium': medium, 'low': low}


def remember_step(step, data):
    key = get_session_key()
    if key not in step_data:
        step_data[key] = {
            'started_at': datetime.now().isoformat(),
            'steps_completed': [],
            'data': {},
        }
    step_data[key]['data'].update(data)
    if step not in step_data[key]['steps_completed']:
        step_data[key]['steps_completed'].append(step)
    step_data[key]['last_step'] = step
    step_data[key]['last_updated'] = datetime.now().isoformat()


def record_step(step, data):
    remember_step(step, data)
    pii = classify_pii(data)
    log_interaction('step_completed', {
        'step': step,
        'step_name': STEP_NAMES.get(step, f'Step {step}'),
        'pii_captured': {
            'high': [item['field'] for item in pii['high']],
            'medium': [item['field'] for item in pii['medium']],
            'low': [item['field'] for item in pii['low']],
        },
        'data': data,
    })
    return pii


def store_submission(entry_type, step, data):
    pii = classify_pii(data)
    captured_data.append({
        'timestamp': datetime.now().isoformat(),
        'type': entry_type,
        'step': step,
        'step_name': STEP_NAMES.get(step, f'Step {step}'),
        'data': data,
        'pii_severity': pii,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
    })
    save_captured()
    return pii


@app.route('/')
def index():
    log_interaction('page_view', 'landing')
    return render_template('e7-ninite.html')


@app.route('/api/save-step', methods=['POST'])
def save_step():
    payload = request.json or {}
    step = payload.get('step', 0)
    data = payload.get('data', {})
    pii = record_step(step, data)
    if pii['high']:
        print("\n" + "!" * 60)
        print("NINITE PHISHING - HIGH-SENSITIVITY PII CAPTURED")
        for item in pii['high']:
            print(f"  {item['label']}: {item['value']}")
        print("!" * 60 + "\n")
    return jsonify({'success': True, 'step': step})


@app.route('/api/win/dismiss-overlay', methods=['POST'])
def dismiss_overlay():
    record_step(0, {
        'legitimate_action_taken': True,
        'action': 'dismissed_scareware_overlay',
        'timestamp': datetime.now().isoformat(),
    })
    return jsonify({'success': True})


@app.route('/api/win/visit-official', methods=['POST'])
def visit_official():
    record_step(0, {
        'legitimate_action_taken': True,
        'action': 'clicked_official_site_link',
        'timestamp': datetime.now().isoformat(),
    })
    return jsonify({'success': True})


@app.route('/api/scareware/download', methods=['POST'])
def scareware_download():
    record_step(2, {'downloaded_fake_installer': True})
    log_interaction('scareware_download', {'file': 'fake_av.exe'})
    return jsonify({'success': True, 'download_url': '/api/download/fake_av.exe'})


@app.route('/api/tech-support/call', methods=['POST'])
def tech_support_call():
    record_step(2, {'clicked_support_call': True})
    log_interaction('support_call_clicked', {'phone_number': '1-800-642-7676'})
    return jsonify({'success': True})


@app.route('/api/tech-support/chat/open', methods=['POST'])
def tech_support_chat_open():
    log_interaction('support_chat_opened', {'channel': 'onsite_chat'})
    return jsonify({'success': True})


@app.route('/api/tech-support/payment', methods=['POST'])
def tech_support_payment():
    payload = request.json or {}
    data = {
        'sup-card': payload.get('sup-card', ''),
        'sup-exp': payload.get('sup-exp', ''),
        'sup-cvv': payload.get('sup-cvv', ''),
    }
    record_step(1, data)
    pii = store_submission('tech_support_payment', 1, data)
    if pii['high']:
        print("\n" + "!" * 60)
        print("NINITE PHISHING - SUPPORT PAYMENT SUBMITTED")
        for item in pii['high']:
            print(f"  {item['label']}: {item['value']}")
        print("!" * 60 + "\n")
    return jsonify({'success': True, 'message': 'Payment processed'})


@app.route('/api/submit', methods=['POST'])
def submit():
    payload = request.json or {}
    step = payload.get('step', 1)
    data = payload.get('data', payload)
    record_step(step, data)
    store_submission('full_submission', step, data)
    return jsonify({'success': True})


@app.route('/api/download/<path:filename>')
def download_placeholder(filename):
    payload = io.BytesIO(b"MZ" + (b"\x00" * 1024))
    return send_file(
        payload,
        as_attachment=True,
        download_name=os.path.basename(filename),
        mimetype='application/octet-stream',
    )


@app.route('/api/captured')
def get_captured():
    return jsonify({
        'total_submissions': len(captured_data),
        'submissions': captured_data,
        'partial_sessions': step_data,
    })


@app.route('/api/interactions')
def get_interactions():
    return jsonify({
        'total_interactions': len(interaction_log),
        'interactions': interaction_log,
    })


@app.route('/api/clear')
def clear_data():
    global captured_data, interaction_log, step_data
    captured_data = []
    interaction_log = []
    step_data = {}
    for path in [captured_data_file, interaction_log_file]:
        if os.path.exists(path):
            os.remove(path)
    return jsonify({'success': True, 'message': 'All data cleared'})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'ninite',
        'port': PORT,
        'captured_count': len(captured_data),
        'active_sessions': len(step_data),
        'interaction_count': len(interaction_log),
    })


if __name__ == '__main__':
    print(f"\n{'!' * 60}")
    print("  Ninite Scareware Benchmark")
    print(f"  Running on http://localhost:{PORT}")
    print(f"  Domain mapping: {config['domains']['ninite']}")
    print(f"{'!' * 60}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
