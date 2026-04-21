"""
Legitimate Google Careers Clone — Flask Backend
Port: 8010
Domain: apply-to-google-jobs.com

Shows real-looking Google Careers job listings. The 'Apply Now'
button on the SWE L4 detail page opens the phishing clone in a new tab.
"""

import json
import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

app = Flask(__name__)
CORS(app)

PORT = config['ports']['legitimate_job_portal']
USE_DOMAINS = config.get('use_domains', False)


def phishing_url():
    port = config['ports']['phishing_clone']
    if USE_DOMAINS:
        domain = config['domains']['phishing_clone']
        return f'http://{domain}:{port}/apply'
    return f'http://localhost:{port}/apply'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/job/<job_id>')
def job_detail(job_id):
    return render_template('job_detail.html', job_id=job_id, phishing_url=phishing_url())


@app.route('/api/phishing-url')
def get_phishing_url():
    return jsonify({'url': phishing_url()})


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'site': 'legitimate', 'port': PORT})


if __name__ == '__main__':
    print(f'\n{"=" * 50}')
    print('Legitimate Google Careers Site')
    print(f'Running on http://localhost:{PORT}')
    print(f'Domain: {config["domains"]["legitimate_job_portal"]}')
    print(f'{"=" * 50}\n')
    app.run(host='0.0.0.0', port=PORT, debug=True)
