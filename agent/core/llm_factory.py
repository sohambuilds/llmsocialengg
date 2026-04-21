"""
Factory for creating the correct LLM client based on model name.

MODEL_REGISTRY maps known model names to their backend and capabilities.
Unknown model names are assumed to be Gemini models (backward compatible).
"""

from __future__ import annotations

from typing import Optional

from .base_client import BaseLLMClient


# ── Known model registry ──────────────────────────────────────────────
MODEL_REGISTRY: dict[str, dict] = {
    # Google Gemini (native SDK)
    "gemini-3-flash-preview": {
        "backend": "gemini",
        "vision": True,
        "label": "Gemini 3 Flash Preview",
    },
    "gemini-2.0-flash": {
        "backend": "gemini",
        "vision": True,
        "label": "Gemini 2.0 Flash",
    },

    # Groq-hosted models (OpenAI-compatible API)
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "backend": "groq",
        "vision": True,
        "label": "Llama 4 Scout 17B (Groq)",
    },
    "openai/gpt-oss-120b": {
        "backend": "groq",
        "vision": False,
        "label": "GPT OSS 120B (Groq)",
    },
}

# Short aliases for convenience on the CLI
MODEL_ALIASES: dict[str, str] = {
    "gemini":       "gemini-3-flash-preview",
    "llama-scout":  "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama4":       "meta-llama/llama-4-scout-17b-16e-instruct",
    "gpt-oss":      "openai/gpt-oss-120b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
}


def resolve_model_name(name: str) -> str:
    """Resolve aliases and return the canonical model ID."""
    return MODEL_ALIASES.get(name, name)


def get_model_info(model: str) -> dict:
    """Return registry info for a model, with sensible defaults for unknowns."""
    model = resolve_model_name(model)
    if model in MODEL_REGISTRY:
        return MODEL_REGISTRY[model]
    # Default: assume Gemini for backward compatibility
    return {"backend": "gemini", "vision": True, "label": model}


def create_llm_client(
    model: str,
    api_key: Optional[str] = None,
) -> BaseLLMClient:
    """Create the appropriate LLM client for the given model name.

    Args:
        model: model name (canonical or alias)
        api_key: optional API key override (otherwise uses env vars)

    Returns:
        A BaseLLMClient instance ready to use.
    """
    model = resolve_model_name(model)
    info = get_model_info(model)
    backend = info["backend"]

    if backend == "groq":
        from .openai_client import OpenAICompatClient

        return OpenAICompatClient(
            model=model,
            supports_vision=info["vision"],
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    # Default: Gemini
    from .llm_client import GeminiClient

    return GeminiClient(model=model, api_key=api_key)
