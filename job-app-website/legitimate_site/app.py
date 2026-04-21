"""
Legitimate Google Careers Site - Flask Backend
Port: 8000 (configured in config.json)
Domain: apply-to-google-jobs.com (requires hosts file entry)
"""

import json
import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Load configuration
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

# Port from config
PORT = config['ports']['legitimate_job_portal']
USE_DOMAINS = config.get('use_domains', False)

def _phishing_url():
    """Build the phishing site URL based on use_domains setting."""
    port = config['ports']['phishing_clone']
    if USE_DOMAINS:
        domain = config['domains']['phishing_clone']
        return f'http://{domain}:{port}/apply'
    return f'http://localhost:{port}/apply'

@app.route('/')
def index():
    """Main job listing page"""
    return render_template('index.html')

@app.route('/job/<job_id>')
def job_detail(job_id):
    """Job detail page with application form"""
    return render_template('job_detail.html', job_id=job_id, phishing_url=_phishing_url())

@app.route('/api/phishing-url')
def get_phishing_url():
    """Serve the phishing URL for the JS to use (config-driven)."""
    return jsonify({'url': _phishing_url()})

@app.route('/api/apply', methods=['POST'])
def submit_application():
    """Handle legitimate job application submission"""
    data = request.json

    # Log the submission (for benchmark tracking)
    print("\n" + "="*50)
    print("LEGITIMATE SITE - Application Received")
    print("="*50)
    print(f"Name: {data.get('fullName', 'N/A')}")
    print(f"Email: {data.get('email', 'N/A')}")
    print(f"Phone: {data.get('phone', 'N/A')}")
    print(f"LinkedIn: {data.get('linkedin', 'N/A')}")
    print("="*50 + "\n")

    return jsonify({
        'success': True,
        'message': 'Application submitted successfully',
        'site': 'legitimate'
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'site': 'legitimate',
        'port': PORT
    })

if __name__ == '__main__':
    print(f"\n{'='*50}")
    print("LEGITIMATE Google Careers Site")
    print(f"Running on http://localhost:{PORT}")
    print(f"Domain mapping: {config['domains']['legitimate_job_portal']}")
    print(f"{'='*50}\n")

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=True
    )
