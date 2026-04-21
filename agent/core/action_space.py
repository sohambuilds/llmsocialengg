"""
Defines the action space for the web navigation agent.
Each action is a structured dict the VLM outputs as JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


ACTION_SCHEMA: dict[str, dict[str, str]] = {
    "click": {"element_id": "int"},
    "type": {"element_id": "int", "text": "str"},
    "select_option": {"element_id": "int", "value": "str"},
    "check": {"element_id": "int", "checked": "bool"},
    "upload_file": {"element_id": "int", "file_key": "str"},
    "scroll": {"direction": "str", "amount": "int"},
    "navigate": {"url": "str"},
    "go_back": {},
    "switch_tab": {"tab_index": "int"},
    "close_tab": {"tab_index": "int"},
    "screenshot": {},
    "wait": {"seconds": "int"},
    "done": {"summary": "str"},
}

VALID_SCROLL_DIRECTIONS = {"up", "down"}

TYPE_VALIDATORS: dict[str, type] = {
    "int": int,
    "str": str,
    "bool": bool,
}


@dataclass
class AgentAction:
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None

    @property
    def element_id(self) -> Optional[int]:
        return self.params.get("element_id")

    @property
    def text(self) -> Optional[str]:
        return self.params.get("text")

    @property
    def summary(self) -> Optional[str]:
        return self.params.get("summary")

    def to_dict(self) -> dict:
        d = {"action": self.action_type, **self.params}
        if self.reasoning:
            d["reasoning"] = self.reasoning
        return d


class ActionParseError(Exception):
    pass


def parse_action(raw: str | dict) -> AgentAction:
    """Parse raw VLM output into a validated AgentAction."""
    if isinstance(raw, str):
        raw = _extract_json(raw)

    if not isinstance(raw, dict):
        raise ActionParseError(f"Expected a JSON object, got {type(raw).__name__}")

    action_type = raw.get("action")
    if not action_type or action_type not in ACTION_SCHEMA:
        valid = ", ".join(sorted(ACTION_SCHEMA.keys()))
        raise ActionParseError(
            f"Missing or invalid 'action' field. Got: {action_type!r}. "
            f"Valid actions: {valid}"
        )

    reasoning = raw.get("reasoning")
    schema = ACTION_SCHEMA[action_type]
    params: dict[str, Any] = {}

    for param_name, param_type_str in schema.items():
        value = raw.get(param_name)
        if value is None:
            raise ActionParseError(
                f"Action '{action_type}' requires parameter '{param_name}'"
            )
        expected_type = TYPE_VALIDATORS[param_type_str]
        if not isinstance(value, expected_type):
            if expected_type is int and isinstance(value, float) and value == int(value):
                value = int(value)
            elif expected_type is bool and isinstance(value, (int, str)):
                value = bool(value)
            else:
                raise ActionParseError(
                    f"Parameter '{param_name}' for action '{action_type}' "
                    f"must be {param_type_str}, got {type(value).__name__}"
                )
        params[param_name] = value

    if action_type == "scroll" and params.get("direction") not in VALID_SCROLL_DIRECTIONS:
        raise ActionParseError(
            f"scroll direction must be 'up' or 'down', got {params['direction']!r}"
        )

    if action_type == "wait":
        secs = params.get("seconds", 0)
        if secs < 0 or secs > 30:
            raise ActionParseError(f"wait seconds must be 0-30, got {secs}")

    return AgentAction(action_type=action_type, params=params, reasoning=reasoning)


def _extract_json(text: str) -> dict:
    """Extract JSON from VLM text output, handling markdown code fences."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = len(lines)
        for i in range(1, len(lines)):
            if lines[i].strip() == "```":
                end = i
                break
        text = "\n".join(lines[start:end]).strip()

    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start == -1 or brace_end == -1:
        raise ActionParseError(f"No JSON object found in response: {text[:200]}")

    json_str = text[brace_start : brace_end + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ActionParseError(f"Invalid JSON: {e}. Raw: {json_str[:200]}")


def parse_action_batch(raw: str | dict) -> list[AgentAction]:
    """Parse raw VLM output into a list of validated AgentActions.

    Expected format: {"actions": [...], "reasoning": "..."}
    Fallback: if a single action object is returned, wrap it in a list.
    """
    if isinstance(raw, str):
        raw = _extract_json(raw)

    if not isinstance(raw, dict):
        raise ActionParseError(f"Expected a JSON object, got {type(raw).__name__}")

    top_reasoning = raw.get("reasoning")

    # Fallback: single action object (has "action" key but no "actions" key)
    if "action" in raw and "actions" not in raw:
        action = parse_action(raw)
        action.reasoning = action.reasoning or top_reasoning
        return [action]

    actions_raw = raw.get("actions")
    if not isinstance(actions_raw, list) or len(actions_raw) == 0:
        raise ActionParseError(
            "Expected an 'actions' array with at least one action. "
            f"Got: {type(actions_raw).__name__ if actions_raw is not None else 'missing'}"
        )

    actions: list[AgentAction] = []
    for i, item in enumerate(actions_raw):
        if not isinstance(item, dict):
            raise ActionParseError(f"Action at index {i} is not a JSON object")
        try:
            action = parse_action(item)
            action.reasoning = action.reasoning or top_reasoning
            actions.append(action)
        except ActionParseError as e:
            raise ActionParseError(f"Action at index {i}: {e}") from e

    return actions


def build_retry_feedback(error_msg: str, raw_response: str = "") -> str:
    """Build a targeted retry message based on the specific parse error.

    Returns a detailed correction prompt that tells the model exactly
    what went wrong and how to fix the JSON.
    """
    valid_actions = ", ".join(sorted(ACTION_SCHEMA.keys()))

    example = (
        '{"actions": [{"action": "done", "summary": "Task completed."}], '
        '"reasoning": "Explaining why"}'
    )

    # --- Single-quote JSON (Python dict syntax instead of JSON) ---
    if "Expecting property name enclosed in double quotes" in error_msg or \
       "Invalid JSON" in error_msg and raw_response.lstrip().startswith("{"):
        # Check if it looks like single-quoted Python dict
        if "'" in raw_response and '"' not in raw_response[:50]:
            return (
                "ERROR: Your response used single quotes (Python dict syntax) "
                "instead of double quotes (JSON syntax).\n"
                "JSON requires double quotes for all keys and string values.\n"
                f"Correct format example:\n{example}\n"
                "Respond ONLY with a valid JSON object. No explanation text before or after."
            )
        return (
            f"ERROR: Your response contained invalid JSON. Details: {error_msg}\n"
            "Make sure all keys and string values use double quotes, not single quotes.\n"
            "Do not include trailing commas. Ensure all braces and brackets are matched.\n"
            f"Correct format example:\n{example}\n"
            "Respond ONLY with a valid JSON object. No explanation text before or after."
        )

    # --- Empty actions array ---
    if "Expected an 'actions' array with at least one action" in error_msg:
        return (
            "ERROR: You returned an empty 'actions' array. The array MUST contain "
            "at least one action object.\n"
            "If the task is complete, use the 'done' action:\n"
            '{"actions": [{"action": "done", "summary": "Description of what was accomplished."}], '
            '"reasoning": "Why the task is complete"}\n'
            "If the task is NOT complete, include the next action(s) to take.\n"
            f"Valid action types: {valid_actions}\n"
            "Respond ONLY with a valid JSON object."
        )

    # --- No JSON object found at all ---
    if "No JSON object found" in error_msg:
        return (
            "ERROR: Your response did not contain any JSON object.\n"
            "You MUST respond with a JSON object — no plain text responses.\n"
            f"Required format:\n{example}\n"
            f"Valid action types: {valid_actions}\n"
            "Respond ONLY with the JSON object. Do not write any explanation before or after it."
        )

    # --- Missing or invalid 'action' field ---
    if "Missing or invalid 'action' field" in error_msg:
        return (
            f"ERROR: {error_msg}\n"
            "Each action object inside the 'actions' array MUST have an 'action' field "
            f"set to one of: {valid_actions}\n"
            f"Correct format example:\n{example}\n"
            "Respond ONLY with a valid JSON object."
        )

    # --- Missing required parameter ---
    if "requires parameter" in error_msg:
        return (
            f"ERROR: {error_msg}\n"
            "Check the required parameters for the action you are using:\n"
            + _format_action_params_hint(error_msg)
            + "\nRespond ONLY with a valid JSON object."
        )

    # --- Wrong parameter type ---
    if "must be" in error_msg and "got" in error_msg:
        return (
            f"ERROR: {error_msg}\n"
            "Fix the parameter type. For example:\n"
            "  - element_id must be an integer (5, not \"5\")\n"
            "  - text must be a string (\"hello\", not 123)\n"
            "  - checked must be a boolean (true/false)\n"
            "Respond ONLY with a valid JSON object."
        )

    # --- Fallback: generic but still more helpful than before ---
    return (
        f"ERROR: Your previous response was not valid. Details: {error_msg}\n"
        "You MUST respond with a JSON object in this exact format:\n"
        f"{example}\n"
        f"Valid action types: {valid_actions}\n"
        "Rules:\n"
        "- Use double quotes for all keys and strings\n"
        "- The 'actions' array must have at least one action\n"
        "- Each action must have an 'action' field with a valid type\n"
        "- Include required parameters for each action type\n"
        "Respond ONLY with the JSON object."
    )


def _format_action_params_hint(error_msg: str) -> str:
    """Extract the action type from an error and return its parameter schema."""
    for action_type, params in ACTION_SCHEMA.items():
        if f"'{action_type}'" in error_msg:
            if not params:
                return f"  {action_type}: no parameters needed"
            param_strs = [f'"{k}": <{v}>' for k, v in params.items()]
            return f'  {action_type}: {{{", ".join(param_strs)}}}'
    return "  See the action descriptions in the system prompt."


def get_action_prompt_description() -> str:
    """Return a description of available actions for the system prompt."""
    lines = [
        "Available actions (respond with a JSON object containing an \"actions\" array):\n",
    ]
    descriptions = {
        "click": 'Click an element (button, link, checkbox, radio). {"action": "click", "element_id": 3}',
        "type": 'Type text into an input/textarea field. {"action": "type", "element_id": 5, "text": "hello"}',
        "select_option": 'Select an option from a dropdown. Use the option value. {"action": "select_option", "element_id": 7, "value": "masters"}',
        "check": 'Check or uncheck a checkbox. {"action": "check", "element_id": 9, "checked": true}',
        "upload_file": 'Upload a file (e.g. resume). Use a file_key from the user profile. {"action": "upload_file", "element_id": 11, "file_key": "resume"}',
        "scroll": 'Scroll the page. {"action": "scroll", "direction": "down", "amount": 3}',
        "navigate": 'Navigate to a URL. {"action": "navigate", "url": "http://example.com"}',
        "go_back": 'Go back to previous page. {"action": "go_back"}',
        "switch_tab": 'Switch to another browser tab. {"action": "switch_tab", "tab_index": 1}',
        "close_tab": 'Close a browser tab. {"action": "close_tab", "tab_index": 2}',
        "screenshot": 'Take a screenshot to see the page visually. The image will appear in your next observation. {"action": "screenshot"}',
        "wait": 'Wait for the page to update. {"action": "wait", "seconds": 2}',
        "done": 'Declare the task complete. {"action": "done", "summary": "Applied for the job successfully."}',
    }
    for action, desc in descriptions.items():
        lines.append(f"  - {desc}")
    lines.append("")
    lines.append("Respond with a JSON object containing an \"actions\" array and a \"reasoning\" field. Example:")
    lines.append('  {"actions": [{"action": "type", "element_id": 5, "text": "John"}, {"action": "type", "element_id": 7, "text": "john@example.com"}, {"action": "click", "element_id": 13}], "reasoning": "Filling all form fields and submitting"}')
    lines.append("")
    lines.append("Include ALL actions needed for the current page state. Place page-changing actions (click on submit/link, navigate, go_back) at the END of the array.")
    return "\n".join(lines)
