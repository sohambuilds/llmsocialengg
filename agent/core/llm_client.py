"""
LLM client for the web navigation agent — Gemini backend.
Wraps the Google Generative AI SDK to send multimodal prompts (text + images)
and parse structured JSON actions from the response.
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Any, Optional

from google import genai
from google.genai import types

from .action_space import AgentAction, ActionParseError, parse_action, parse_action_batch, build_retry_feedback
from .base_client import BaseLLMClient


DEFAULT_MODEL = "gemini-3-flash-preview"
MAX_RETRIES = 7


class GeminiClient(BaseLLMClient):
    """Sends multimodal prompts to Gemini and parses structured action responses."""

    supports_vision = True

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model = model
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "No API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY env var, "
                "or pass api_key= to GeminiClient."
            )
        self._client = genai.Client(api_key=key)

    async def get_action_batch(
        self,
        messages: list[dict[str, Any]],
        screenshot_base64: Optional[str] = None,
    ) -> list[AgentAction]:
        """
        Send the conversation to Gemini and parse the response as a batch of AgentActions.

        messages: list of {"role": "user"|"model", "text": str}
        screenshot_base64: optional base64 PNG to attach to the latest user message
        """
        last_error: Optional[str] = None
        last_raw: str = ""
        last_is_api_error: bool = False

        for attempt in range(MAX_RETRIES):
            # Only inject parse-error feedback, not API-error feedback
            parse_error_for_feedback = last_error if not last_is_api_error else None
            contents = self._build_contents(messages, screenshot_base64, parse_error_for_feedback, last_raw)

            retry_tag = f" (retry {attempt})" if attempt > 0 else ""
            print(f"  [llm] Calling Gemini API ({self.model}){retry_tag}...")
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=4096,
                    ),
                )
                print(f"  [llm] Response received")
            except Exception as e:
                last_error = f"API call failed: {e}"
                last_is_api_error = True
                print(f"  [llm] API error: {e}")
                # Exponential backoff for API errors
                wait_secs = min(2 ** attempt, 60)
                print(f"  [llm] Waiting {wait_secs}s before retry...")
                await asyncio.sleep(wait_secs)
                continue

            response_text = response.text
            if not response_text:
                last_error = "Empty response from model"
                last_is_api_error = True
                print(f"  [llm] Empty response from model")
                continue

            print(f"  [llm] Raw response ({len(response_text)} chars): {response_text[:200]}")
            try:
                actions = parse_action_batch(response_text)
                reasoning = self._extract_reasoning(response_text)
                for action in actions:
                    action.reasoning = action.reasoning or reasoning
                return actions
            except ActionParseError as e:
                last_error = str(e)
                last_is_api_error = False
                last_raw = response_text
                print(f"  [llm] Parse error: {e}")
                continue

        raise ActionParseError(
            f"Failed to get valid action batch after {MAX_RETRIES} attempts. Last error: {last_error}"
        )

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
    ) -> str:
        """Simple text generation for context compression."""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text or "No summary generated."
        except Exception:
            return "Summary generation failed. Agent continued browsing."

    def _build_contents(
        self,
        messages: list[dict[str, Any]],
        screenshot_base64: Optional[str],
        retry_error: Optional[str],
        retry_raw_response: str = "",
    ) -> list[types.Content]:
        """Convert our message format to Gemini SDK Content objects."""
        contents: list[types.Content] = []

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            parts = [types.Part.from_text(text=msg["text"])]
            contents.append(types.Content(role=role, parts=parts))

        if screenshot_base64:
            image_bytes = base64.b64decode(screenshot_base64)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            if contents and contents[-1].role == "user":
                contents[-1].parts.append(image_part)
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[image_part],
                ))

        if retry_error:
            # Add the failed response as model message for context
            if retry_raw_response:
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=retry_raw_response)],
                ))
            feedback = build_retry_feedback(retry_error, retry_raw_response)
            if contents and contents[-1].role == "user" and not retry_raw_response:
                contents[-1].parts.append(types.Part.from_text(text=feedback))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=feedback)],
                ))

        return contents

    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Try to extract reasoning from the model response text outside the JSON."""
        json_start = text.find("{")
        if json_start > 0:
            before_json = text[:json_start].strip()
            if len(before_json) > 10:
                return before_json
        return None


# Backward-compatible alias
LLMClient = GeminiClient
