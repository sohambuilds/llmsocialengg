"""
Abstract base class for LLM clients.
Every backend (Gemini, Groq/OpenAI-compat) implements this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from .action_space import AgentAction


class BaseLLMClient(ABC):
    """Common interface for all LLM backends."""

    model: str
    supports_vision: bool

    @abstractmethod
    async def get_action_batch(
        self,
        messages: list[dict[str, Any]],
        screenshot_base64: Optional[str] = None,
    ) -> list[AgentAction]:
        """Send conversation to the model and return parsed actions.

        Args:
            messages: list of {"role": "user"|"model", "text": str}
            screenshot_base64: optional base64 PNG screenshot. Clients that
                               don't support vision should silently ignore this.
        """
        ...

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
    ) -> str:
        """Simple text-only generation (used for context compression).

        Returns the generated text, or a fallback string on error.
        """
        ...
