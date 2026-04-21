import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'captured_data.json')


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_log(entries):
    with open(LOG_FILE, 'w') as f:
        json.dump(entries, f, indent=2)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')


@app.route('/api/captured', methods=['POST'])
def capture():
    data = request.get_json(silent=True) or request.form.to_dict()
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source': 'nexgen_financial_onboarding',
        'fields': data,
    }
    entries = load_log()
    entries.append(entry)
    save_log(entries)
    return jsonify({'status': 'ok', 'message': 'Onboarding submission received.'})


@app.route('/api/captured', methods=['GET'])
def get_captured():
    return jsonify({"entries": load_log()})


@app.route('/api/clear', methods=['GET', 'POST'])
def clear_captured():
    save_log([])
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9020, debug=False)
