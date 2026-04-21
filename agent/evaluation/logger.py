"""
Session logger for the web navigation agent.
Records every step (observation, action, errors) to a JSON file for post-run analysis.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


LOGS_DIR = Path(__file__).parent.parent / "logs"


class SessionLogger:
    """Logs every agent step to a JSON file."""

    def __init__(self, env_name: str, model: str, log_dir: Optional[Path] = None):
        self.env_name = env_name
        self.model = model
        self._log_dir = log_dir or LOGS_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_model = model.replace("/", "_").replace("\\", "_")
        self._filename = f"{env_name}_{safe_model}_{timestamp}.json"
        self._filepath = self._log_dir / self._filename

        self._session: dict[str, Any] = {
            "env": env_name,
            "model": model,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "completed": False,
            "completion_summary": None,
            "total_steps": 0,
            "steps": [],
            "errors": [],
        }

    @property
    def filepath(self) -> Path:
        return self._filepath

    def log_step(
        self,
        step: int,
        observation: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> None:
        step_entry = {
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": observation.get("current_url", ""),
            "page_title": observation.get("page_title", ""),
            "num_tabs": len(observation.get("open_tabs", [])),
            "num_elements": len(observation.get("interactive_elements", [])),
            "actions": actions,
        }
        self._session["steps"].append(step_entry)
        self._session["total_steps"] = step + 1
        self._save()

    def log_completion(self, summary: Optional[str]) -> None:
        self._session["completed"] = True
        self._session["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._session["completion_summary"] = summary
        self._save()

    def log_error(self, step: int, error: str) -> None:
        self._session["errors"].append({
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
        })
        self._save()

    def get_session_log(self) -> dict[str, Any]:
        return self._session

    def _save(self) -> None:
        with open(self._filepath, "w") as f:
            json.dump(self._session, f, indent=2, default=str)
