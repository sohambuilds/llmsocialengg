"""
Gmail-like Mailbox Interface - Flask Backend
Port: 8025 (configured in config.json)

Serves as the entry point for the LLM phishing benchmark.
The agent accesses this mailbox which contains a mix of legitimate
and phishing emails. One phishing email leads to the job application site.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Load configuration
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
    # Also handle cross-env domains that appear in emails (ecommerce links)
    cross_env_rewrites = {
        'shopsmart.com:10010': 'localhost:10010',
        'amazon.com:10060': 'localhost:10060',
        'target.com:10070': 'localhost:10070',
        'walmart.com:10080': 'localhost:10080',
    }
    for domain_port, localhost_port in cross_env_rewrites.items():
        html = html.replace(f'http://{domain_port}', f'http://{localhost_port}')
    return html


# Load emails
emails_path = os.path.join(os.path.dirname(__file__), 'emails.json')
with open(emails_path, 'r', encoding='utf-8') as f:
    emails = json.load(f)

# Rewrite URLs in email bodies based on use_domains setting
for email in emails:
    if 'body_html' in email:
        email['body_html'] = _rewrite_urls(email['body_html'])

# Track agent interactions for benchmark analysis
interaction_log = []


def log_interaction(action, details):
    """Log agent interactions for benchmark scoring."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details,
        'ip': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else None
    }
    interaction_log.append(entry)

    log_path = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
    with open(log_path, 'w') as f:
        json.dump(interaction_log, f, indent=2)

    print(f"[MAILBOX] {action}: {details}")


@app.route('/')
def inbox():
    """Main inbox view - Gmail-like interface."""
    log_interaction('page_view', 'inbox')
    return render_template('inbox.html', emails=emails)


@app.route('/email/<email_id>')
def view_email(email_id):
    """View a single email."""
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

    # Mark as read
    email['read'] = True

    return render_template('email_view.html', email=email, emails=emails)


@app.route('/api/emails')
def get_emails():
    """API endpoint to list all emails."""
    return jsonify(emails)


@app.route('/api/email/<email_id>')
def get_email(email_id):
    """API endpoint to get a single email."""
    email = next((e for e in emails if e['id'] == email_id), None)
    if not email:
        return jsonify({'error': 'Email not found'}), 404
    return jsonify(email)


@app.route('/api/interactions')
def get_interactions():
    """Retrieve all logged interactions for benchmark analysis."""
    return jsonify({
        'total_interactions': len(interaction_log),
        'interactions': interaction_log
    })


@app.route('/api/clear')
def clear_interactions():
    """Clear interaction log for new test runs."""
    global interaction_log
    interaction_log = []

    log_path = os.path.join(os.path.dirname(__file__), 'interaction_log.json')
    if os.path.exists(log_path):
        os.remove(log_path)

    # Reset read status
    for email in emails:
        if email['id'] != 'msg_001':
            email['read'] = email.get('read', True)

    return jsonify({'success': True, 'message': 'Interaction log cleared'})


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'site': 'mailbox',
        'port': PORT,
        'email_count': len(emails),
        'interaction_count': len(interaction_log)
    })


if __name__ == '__main__':
    print(f"\n{'='*50}")
    print("Gmail-like Mailbox Interface")
    print(f"Running on http://localhost:{PORT}")
    print(f"{'='*50}\n")

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=True
    )
