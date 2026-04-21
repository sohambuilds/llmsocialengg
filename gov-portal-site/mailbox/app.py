"""
Gmail-like Mailbox Interface - Flask Backend
Port: 8050 (configured in config.json)

Entry point for ENV 5 (IRS Government Portal Phishing Benchmark).
The agent accesses this mailbox which contains a mix of legitimate
and phishing emails. The IRS phishing email leads to the fake refund site.
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

PORT = config['ports']['mailbox']

emails_path = os.path.join(os.path.dirname(__file__), 'emails.json')
with open(emails_path, 'r', encoding='utf-8') as f:
    original_emails = json.load(f)

emails = json.loads(json.dumps(original_emails))

log_file = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
interaction_log = []
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        try:
            interaction_log = json.load(f)
        except json.JSONDecodeError:
            interaction_log = []


def log_interaction(action, details):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else None
    }
    interaction_log.append(entry)

    with open(log_file, 'w') as f:
        json.dump(interaction_log, f, indent=2)

    print(f"[MAILBOX] {action}: {details}")


@app.route('/')
def inbox():
    log_interaction('page_view', 'inbox')
    return render_template('inbox.html', emails=emails)


@app.route('/email/<email_id>')
def view_email(email_id):
    email = next((e for e in emails if e['id'] == email_id), None)
    if not email:
        return "Email not found", 404

    is_phishing = email.get('is_phishing', False)
    log_interaction('email_opened', {
        'email_id': email_id,
        'subject': email['subject'],
        'from': email['from_email'],
        'is_phishing': is_phishing
    })

    email['read'] = True

    return render_template('email_view.html', email=email, emails=emails)


@app.route('/api/emails')
def get_emails():
    return jsonify(emails)


@app.route('/api/email/<email_id>')
def get_email(email_id):
    email = next((e for e in emails if e['id'] == email_id), None)
    if not email:
        return jsonify({'error': 'Email not found'}), 404
    return jsonify(email)


@app.route('/api/interactions')
def get_interactions():
    return jsonify({
        'total_interactions': len(interaction_log),
        'interactions': interaction_log
    })


@app.route('/api/clear')
def clear_interactions():
    global interaction_log, emails
    interaction_log = []

    if os.path.exists(log_file):
        os.remove(log_file)

    emails = json.loads(json.dumps(original_emails))

    return jsonify({'success': True, 'message': 'Interaction log cleared and emails reset'})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'mailbox',
        'port': PORT,
        'email_count': len(emails),
        'interaction_count': len(interaction_log)
    })


if __name__ == '__main__':
    print(f"\n{'='*50}")
    print("Gmail-like Mailbox Interface (ENV 5)")
    print(f"Running on http://localhost:{PORT}")
    print(f"{'='*50}\n")

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=True
    )
