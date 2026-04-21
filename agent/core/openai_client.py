"""
LLM client using the OpenAI-compatible Chat Completions API.
Used for Groq-hosted models (Llama 4 Scout, GPT OSS 120B).

Supports both VLM (vision) and text-only modes depending on the model.
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
from typing import Any, Optional

from .action_space import AgentAction, ActionParseError, parse_action_batch, build_retry_feedback
from .base_client import BaseLLMClient

MAX_RETRIES = 7
# Groq enforces 4MB max request size for vision; compress images to stay safe
MAX_IMAGE_BYTES = 2_500_000  # ~2.5MB leaves headroom for text payload


class OpenAICompatClient(BaseLLMClient):
    """Sends prompts via OpenAI-compatible API (Groq) and parses actions."""

    def __init__(
        self,
        model: str,
        supports_vision: bool = False,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        self.model = model
        self.supports_vision = supports_vision

        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "No Groq API key found. Set GROQ_API_KEY env var, "
                "or pass api_key= to OpenAICompatClient."
            )

        # Import lazily so the dep is only required when this client is used
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=key, base_url=base_url)

    async def get_action_batch(
        self,
        messages: list[dict[str, Any]],
        screenshot_base64: Optional[str] = None,
    ) -> list[AgentAction]:
        last_error: Optional[str] = None
        last_raw: str = ""
        last_is_api_error: bool = False

        for attempt in range(MAX_RETRIES):
            # Only inject parse-error feedback, not API-error feedback
            parse_error_for_feedback = last_error if not last_is_api_error else None
            chat_messages = self._build_messages(
                messages, screenshot_base64, parse_error_for_feedback, last_raw
            )

            retry_tag = f" (retry {attempt})" if attempt > 0 else ""
            provider = "Groq" if "groq" in str(self._client.base_url) else "OpenAI-compat"
            print(f"  [llm] Calling {provider} API ({self.model}){retry_tag}...")

            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=chat_messages,
                    temperature=0.2,
                    max_tokens=4096,
                )
                response_text = response.choices[0].message.content
                print(f"  [llm] Response received")
            except Exception as e:
                last_error = f"API call failed: {e}"
                last_is_api_error = True
                print(f"  [llm] API error: {e}")
                # Exponential backoff for connection errors (don't hammer a downed API)
                wait_secs = min(2 ** attempt, 60)
                print(f"  [llm] Waiting {wait_secs}s before retry...")
                await asyncio.sleep(wait_secs)
                continue

            if not response_text:
                last_error = "Empty response from model"
                last_is_api_error = True
                print(f"  [llm] Empty response from model")
                continue

            print(
                f"  [llm] Raw response ({len(response_text)} chars): "
                f"{response_text[:200]}"
            )
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
            f"Failed to get valid action batch after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or "No summary generated."
        except Exception:
            return "Summary generation failed. Agent continued browsing."

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        messages: list[dict[str, Any]],
        screenshot_base64: Optional[str],
        retry_error: Optional[str],
        retry_raw_response: str = "",
    ) -> list[dict[str, Any]]:
        """Convert our internal message format to OpenAI chat format."""
        chat_msgs: list[dict[str, Any]] = []

        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            chat_msgs.append({"role": role, "content": msg["text"]})

        # Attach screenshot to last user message (VLM models only)
        if screenshot_base64 and self.supports_vision:
            compressed = self._maybe_compress_image(screenshot_base64)
            data_url = f"data:image/png;base64,{compressed}"

            # Replace last user msg with multimodal content
            last_msg = chat_msgs[-1]
            if last_msg["role"] == "user":
                chat_msgs[-1] = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": last_msg["content"]},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }

        # Append targeted retry feedback if present
        if retry_error:
            # Add the failed response as assistant message for context
            if retry_raw_response:
                chat_msgs.append({"role": "assistant", "content": retry_raw_response})
            feedback = build_retry_feedback(retry_error, retry_raw_response)
            chat_msgs.append({"role": "user", "content": feedback})

        return chat_msgs

    def _maybe_compress_image(self, b64_str: str) -> str:
        """Compress screenshot if it exceeds Groq's size limits."""
        raw_bytes = base64.b64decode(b64_str)
        if len(raw_bytes) <= MAX_IMAGE_BYTES:
            return b64_str

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw_bytes))
            # Downscale to 60% and convert to JPEG
            new_w = int(img.width * 0.6)
            new_h = int(img.height * 0.6)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            compressed = base64.b64encode(buf.getvalue()).decode("utf-8")
            print(
                f"  [llm] Compressed screenshot: "
                f"{len(raw_bytes)}B -> {len(buf.getvalue())}B"
            )
            return compressed
        except ImportError:
            # Pillow not available — return original and hope for the best
            return b64_str

    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Try to extract reasoning from response text outside the JSON."""
        json_start = text.find("{")
        if json_start > 0:
            before_json = text[:json_start].strip()
            if len(before_json) > 10:
                return before_json
        return None
