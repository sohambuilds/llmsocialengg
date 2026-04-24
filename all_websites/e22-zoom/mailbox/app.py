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
PORT = config['ports']['mailbox']

data_path = os.path.join(os.path.dirname(__file__), 'messages.json')
with open(data_path, 'r', encoding='utf-8') as f:
    original_data = json.load(f)
messages = json.loads(json.dumps(original_data))

log_file = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
interaction_log = []
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        try:
            interaction_log = json.load(f)
        except json.JSONDecodeError:
            interaction_log = []


def log_interaction(action, details):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
    }
    interaction_log.append(entry)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(interaction_log, f, indent=2)
    print(f"[ENTRY] {action}: {json.dumps(details, ensure_ascii=True)}")


@app.route('/')
def inbox():
    log_interaction('page_view', 'slack_channel')
    return render_template('inbox.html', messages=messages)


@app.route('/api/messages')
def get_messages():
    return jsonify(messages)


@app.route('/api/entry-click', methods=['POST'])
def entry_click():
    payload = request.json or {}
    log_interaction('entry_click', {
        'message_id': payload.get('message_id'),
        'target_url': payload.get('target_url'),
        'is_phishing': payload.get('is_phishing', False),
    })
    return jsonify({'success': True})


@app.route('/api/interactions')
def get_interactions():
    return jsonify({'total_interactions': len(interaction_log), 'interactions': interaction_log})


@app.route('/api/clear')
def clear():
    global interaction_log, messages
    interaction_log = []
    messages = json.loads(json.dumps(original_data))
    if os.path.exists(log_file):
        os.remove(log_file)
    return jsonify({'success': True, 'message': 'Cleared'})


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'mailbox', 'port': PORT, 'interaction_count': len(interaction_log)})


if __name__ == '__main__':
    print(f"\n{'=' * 50}")
    print(f"Entry Point Server ({config['domains']['mailbox']})")
    print(f"Running on http://localhost:{PORT}")
    print(f"{'=' * 50}\n")
    app.run(host='0.0.0.0', port=PORT, debug=True)
