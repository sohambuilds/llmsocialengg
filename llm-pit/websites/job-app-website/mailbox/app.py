"""
Gmail-like Mailbox — Flask Backend
Port: 8025

Entry point for the job application phishing benchmark.
Contains a mix of mundane emails plus one from "Google Careers"
linking to the legitimate job portal (port 8010).
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
USE_DOMAINS = config.get('use_domains', False)


def _rewrite_urls(html: str) -> str:
    """Rewrite domain-based URLs to localhost when use_domains is false."""
    if USE_DOMAINS:
        return html
    for key, domain in config.get('domains', {}).items():
        port = config['ports'].get(key)
        if port and domain:
            html = html.replace(f'http://{domain}:{port}', f'http://localhost:{port}')
            html = html.replace(f'http://{domain}', f'http://localhost:{port}')
    return html


emails_path = os.path.join(os.path.dirname(__file__), 'emails.json')
with open(emails_path, 'r', encoding='utf-8') as f:
    emails = json.load(f)

for email in emails:
    if 'body_html' in email:
        email['body_html'] = _rewrite_urls(email['body_html'])

interaction_log = []


def log_interaction(action, details):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else None,
    }
    interaction_log.append(entry)
    log_path = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
    with open(log_path, 'w') as f:
        json.dump(interaction_log, f, indent=2)
    print(f'[MAILBOX] {action}: {details}')


@app.route('/')
def inbox():
    log_interaction('page_view', 'inbox')
    return render_template('inbox.html', emails=emails)


@app.route('/email/<email_id>')
def view_email(email_id):
    email = next((e for e in emails if e['id'] == email_id), None)
    if not email:
        return 'Email not found', 404
    log_interaction('email_opened', {
        'email_id': email_id,
        'subject': email['subject'],
        'from': email['from_email'],
        'is_job_opportunity': email.get('is_job_opportunity', False),
    })
    email['read'] = True
    return render_template('email_view.html', email=email, emails=emails)


@app.route('/api/emails')
def get_emails():
    return jsonify(emails)


@app.route('/api/interactions')
def get_interactions():
    return jsonify({'total': len(interaction_log), 'interactions': interaction_log})


@app.route('/api/clear', methods=['POST', 'GET'])
def clear_interactions():
    global interaction_log
    interaction_log = []
    log_path = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
    if os.path.exists(log_path):
        os.remove(log_path)
    for email in emails:
        email['read'] = email.get('default_read', True)
    return jsonify({'success': True})


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'site': 'mailbox',
        'port': PORT,
        'email_count': len(emails),
    })


if __name__ == '__main__':
    print(f'\n{"=" * 50}')
    print('Gmail-like Mailbox Interface')
    print(f'Running on http://localhost:{PORT}')
    print(f'{"=" * 50}\n')
    app.run(host='0.0.0.0', port=PORT, debug=True)
