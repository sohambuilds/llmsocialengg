"""
Manages the agent's conversation context with a sliding window:
  - Full detail for the last N steps
  - A running summary of older steps, compressed via the LLM
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


FULL_WINDOW_SIZE = 5

SUMMARY_INSTRUCTION = (
    "Summarize the following browsing session history in 2-3 concise sentences. "
    "Focus on: what pages were visited, what actions were taken, what forms were "
    "filled, and what the current progress toward the task is. Be factual."
)


@dataclass
class StepRecord:
    step_number: int
    observation_text: str
    actions_taken: list[dict[str, Any]]
    reasoning: Optional[str] = None

    def to_text(self) -> str:
        lines = [
            f"--- Step {self.step_number} ---",
            self.observation_text,
            "",
            f"Actions taken ({len(self.actions_taken)}):",
        ]
        for i, act in enumerate(self.actions_taken):
            lines.append(f"  {i + 1}. {act}")
        if self.reasoning:
            lines.append(f"Reasoning: {self.reasoning}")
        return "\n".join(lines)


class ContextManager:
    """
    Maintains the agent's memory across steps.

    Recent steps (last FULL_WINDOW_SIZE) are kept in full detail.
    Older steps are compressed into a running summary.
    """

    def __init__(self, full_window_size: int = FULL_WINDOW_SIZE):
        self._full_window_size = full_window_size
        self._steps: list[StepRecord] = []
        self._summary: Optional[str] = None
        self._summary_covers_up_to: int = -1

    @property
    def step_count(self) -> int:
        return len(self._steps)

    def add_step(
        self,
        step_number: int,
        observation_text: str,
        actions: list[dict[str, Any]],
        reasoning: Optional[str] = None,
    ) -> None:
        self._steps.append(StepRecord(
            step_number=step_number,
            observation_text=observation_text,
            actions_taken=actions,
            reasoning=reasoning,
        ))

    def needs_summary_update(self) -> bool:
        """Check if we have older steps that need to be summarized."""
        overflow = len(self._steps) - self._full_window_size
        if overflow <= 0:
            return False
        return overflow > (self._summary_covers_up_to + 1)

    def get_steps_to_summarize(self) -> list[StepRecord]:
        """Return older steps that haven't been summarized yet."""
        overflow = len(self._steps) - self._full_window_size
        if overflow <= 0:
            return []
        start = max(0, self._summary_covers_up_to + 1)
        return self._steps[start:overflow]

    def set_summary(self, summary: str, covers_up_to: int) -> None:
        """Update the running summary after LLM compression."""
        if self._summary:
            self._summary = f"{self._summary}\n\n{summary}"
        else:
            self._summary = summary
        self._summary_covers_up_to = covers_up_to

    def get_recent_steps(self) -> list[StepRecord]:
        """Return the last N full-detail steps."""
        return self._steps[-self._full_window_size:]

    def build_messages(
        self,
        system_prompt: str,
        current_observation_text: str,
    ) -> list[dict[str, Any]]:
        """
        Build the message list for the LLM call.
        Format: system prompt (user msg) -> summary (if any) -> recent steps -> current observation
        """
        messages: list[dict[str, Any]] = []

        system_parts = [system_prompt]
        if self._summary:
            system_parts.append(f"\n\n=== Session History Summary ===\n{self._summary}")
        messages.append({"role": "user", "text": "\n".join(system_parts)})
        messages.append({"role": "model", "text": "Understood. I will help complete the task. What is the current page state?"})

        recent = self.get_recent_steps()
        for step in recent:
            messages.append({"role": "user", "text": step.observation_text})
            action_response = str(step.actions_taken)
            if step.reasoning:
                action_response = f"{step.reasoning}\n{action_response}"
            messages.append({"role": "model", "text": action_response})

        messages.append({"role": "user", "text": current_observation_text})

        return messages

    def build_summary_prompt(self, steps: list[StepRecord]) -> str:
        """Build a prompt to ask the LLM to summarize older steps."""
        parts = [SUMMARY_INSTRUCTION, ""]
        if self._summary:
            parts.append(f"Previous summary: {self._summary}")
            parts.append("")
            parts.append("New steps to incorporate:")
        for step in steps:
            parts.append(step.to_text())
            parts.append("")
        return "\n".join(parts)
