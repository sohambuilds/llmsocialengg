import importlib.util
import json
import os
import sys
import threading


def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def run_flask_app(app_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    mod.app.run(host='0.0.0.0', port=mod.PORT, debug=False, use_reloader=False, threaded=True)


def main():
    config = load_config()
    base = os.path.dirname(os.path.abspath(__file__))

    apps = [
        (os.path.join(base, 'mailbox', 'app.py'), 'e13_irs_mailbox_app'),
        (os.path.join(base, 'phishing_irs', 'app.py'), 'e13_irs_phishing_app'),
    ]

    threads = []
    for app_path, module_name in apps:
        t = threading.Thread(target=run_flask_app, args=(app_path, module_name), daemon=True)
        t.start()
        threads.append(t)
        print(f'  Started: {module_name}')

    print('All servers running. Press Ctrl+C to stop.')

    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        print('Shutting down...')


if __name__ == '__main__':
    main()
