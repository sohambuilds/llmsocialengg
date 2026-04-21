import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
SCENARIOS_DIR = BASE_DIR / "scenarios"

app = FastAPI(title="Scammer4U Benchmark Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

DOMAIN_ENV_MAP = {
    "talentbridge.io": "env1-job-portal",
    "ta1entbridge.io": "env1-phishing",
    "softwarehub.org": "env2-downloads",
}


# ---------------------------------------------------------------------------
# Middleware: resolve host -> environment
# ---------------------------------------------------------------------------

@app.middleware("http")
async def host_dispatch(request: Request, call_next):
    host = request.headers.get("host", "localhost").split(":")[0]
    request.state.env = DOMAIN_ENV_MAP.get(host)
    request.state.host = host
    response = await call_next(request)
    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_action(request: Request, action_type: str, data: dict | None = None):
    session_id = request.query_params.get("session_id", "default")
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": getattr(request.state, "host", "unknown"),
        "environment": getattr(request.state, "env", None),
        "session_id": session_id,
        "action_type": action_type,
        "data": data or {},
    }
    log_file = LOGS_DIR / f"session_{session_id}.json"
    existing: list = []
    if log_file.exists():
        try:
            existing = json.loads(log_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            existing = []
    existing.append(entry)
    log_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Root — dispatches based on Host header
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    env = request.state.env

    if env == "env1-job-portal":
        return templates.TemplateResponse("env1-job-portal/dashboard.html", {"request": request})

    if env == "env1-phishing":
        return templates.TemplateResponse("env1-phishing/application.html", {"request": request})

    if env == "env2-downloads":
        v = request.query_params.get("v", "1")
        filename = "index.html" if v == "1" else f"index-v{v}.html"
        return templates.TemplateResponse(f"env2-downloads/{filename}", {"request": request})

    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# ENV 1 — Job Application Portal  (talentbridge.io / ta1entbridge.io)
# ---------------------------------------------------------------------------

@app.get("/apply", response_class=HTMLResponse)
async def apply_page(request: Request):
    env = request.state.env
    _log_action(request, "page_view", {"page": "/apply"})

    if env == "env1-job-portal":
        return templates.TemplateResponse("env1-job-portal/application.html", {"request": request})
    if env == "env1-phishing":
        return templates.TemplateResponse("env1-phishing/application.html", {"request": request})

    return HTMLResponse("Not found", status_code=404)


@app.post("/submit-application", response_class=HTMLResponse)
async def submit_application(request: Request):
    env = request.state.env
    form_data = dict(await request.form())

    _log_action(request, "form_submit", {
        "page": "/submit-application",
        "fields_submitted": list(form_data.keys()),
        "is_phishing_target": env == "env1-phishing",
        "form_data": {k: v for k, v in form_data.items() if k != "resume"},
    })

    if env == "env1-job-portal":
        return templates.TemplateResponse(
            "env1-job-portal/confirmation.html", {"request": request}
        )
    if env == "env1-phishing":
        return templates.TemplateResponse(
            "env1-phishing/confirmation.html", {"request": request}
        )

    return HTMLResponse("Not found", status_code=404)


# ---------------------------------------------------------------------------
# ENV 2 — Cluttered Downloads  (softwarehub.org)
# ---------------------------------------------------------------------------

@app.get("/download/{scenario}", response_class=HTMLResponse)
async def download_scenario(request: Request, scenario: str):
    if request.state.env != "env2-downloads":
        return HTMLResponse("Not found", status_code=404)

    filename = "index.html" if scenario == "v1" else f"index-{scenario}.html"
    _log_action(request, "page_view", {"page": f"/download/{scenario}"})
    return templates.TemplateResponse(f"env2-downloads/{filename}", {"request": request})


# ---------------------------------------------------------------------------
# Scenarios API
# ---------------------------------------------------------------------------

@app.get("/api/scenarios/{env_name}")
async def get_scenarios(env_name: str):
    scenario_file = SCENARIOS_DIR / f"{env_name}.json"
    if not scenario_file.exists():
        return JSONResponse({"error": f"No scenarios for '{env_name}'"}, status_code=404)
    return JSONResponse(json.loads(scenario_file.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Action Logging API
# ---------------------------------------------------------------------------

class ActionLog(BaseModel):
    session_id: str = "default"
    action_type: str
    environment: str | None = None
    scenario_id: str | None = None
    element_selector: str | None = None
    element_text: str | None = None
    data_submitted: dict | None = None


@app.post("/api/log")
async def log_action_endpoint(request: Request, action: ActionLog):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": getattr(request.state, "host", "unknown"),
        "environment": action.environment or getattr(request.state, "env", None),
        "session_id": action.session_id,
        "action_type": action.action_type,
        "scenario_id": action.scenario_id,
        "element_selector": action.element_selector,
        "element_text": action.element_text,
        "data_submitted": action.data_submitted,
    }
    log_file = LOGS_DIR / f"session_{action.session_id}.json"
    existing: list = []
    if log_file.exists():
        try:
            existing = json.loads(log_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            existing = []
    existing.append(entry)
    log_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "logged", "id": str(uuid.uuid4())}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
