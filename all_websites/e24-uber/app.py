from pathlib import Path
import sys

from flask import render_template

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.base_server import create_app, get_environment_port

ENV_ID = Path(__file__).resolve().parent.name
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PORT = get_environment_port(ENV_ID, 5000)

app = create_app(ENV_ID, PORT, ENV_ID, template_folder=str(TEMPLATE_DIR))


@app.route("/")
def index():
    return render_template(f"{ENV_ID}.html")


@app.route("/entry")
def entry():
    return render_template(f"entry_{ENV_ID}.html")


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
