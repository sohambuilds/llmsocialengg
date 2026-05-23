"""
Factory for creating the correct LLM client based on model name.

MODEL_REGISTRY maps known model names to their backend and capabilities.
Unknown model names are assumed to be Gemini models (backward compatible).
"""

from __future__ import annotations

from typing import Optional

from .base_client import BaseLLMClient


# -- Known model registry ----------------------------------------------
MODEL_REGISTRY: dict[str, dict] = {
    # Google Gemini (native SDK)
    "gemini-3-flash-preview": {
        "backend": "gemini",
        "vision": True,
        "label": "Gemini 3 Flash Preview",
    },

    # Groq-hosted models (OpenAI-compatible API) — legacy pilot only
    "openai/gpt-oss-120b": {
        "backend": "groq",
        "vision": False,
        "label": "GPT OSS 120B (Groq)",
    },

    # OpenRouter-hosted frontier models (OpenAI-compatible API)
    "meta-llama/llama-4-scout": {
        "backend": "openrouter",
        "vision": True,
        "label": "Llama 4 Scout (OpenRouter)",
    },
    "openai/gpt-5-mini": {
        "backend": "openrouter",
        "vision": True,
        "label": "GPT-5 mini (OpenRouter)",
        # GPT-5 family supports a reasoning effort knob. "low" cuts latency
        # ~3-5x vs the medium default with minimal quality loss for our
        # action-selection use case. Bump to "medium" if quality regresses.
        "reasoning_effort": "low",
    },
    "anthropic/claude-haiku-4.5": {
        "backend": "openrouter",
        "vision": True,
        "label": "Claude Haiku 4.5 (OpenRouter)",
    },
    # DR judge primary — OpenRouter avoids same-family grading
    "openai/gpt-4o-mini": {
        "backend": "openrouter",
        "vision": True,
        "label": "GPT-4o-mini (OpenRouter)",
    },
    "google/gemini-3-flash-preview": {
        "backend": "openrouter",
        "vision": True,
        "label": "Gemini 3 Flash Preview (OpenRouter)",
        "reasoning_effort": "low",
    },
}

# Short aliases for convenience on the CLI
MODEL_ALIASES: dict[str, str] = {
    "gemini":       "google/gemini-3-flash-preview",
    "gemini-native": "gemini-3-flash-preview",
    "gemini-3":     "google/gemini-3-flash-preview",
    "gemini3":      "google/gemini-3-flash-preview",
    "gemini-3-or":  "google/gemini-3-flash-preview",
    "llama-scout":  "meta-llama/llama-4-scout",
    "llama4":       "meta-llama/llama-4-scout",
    "llama-4":      "meta-llama/llama-4-scout",
    "gpt-oss":      "openai/gpt-oss-120b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "gpt-5-mini":   "openai/gpt-5-mini",
    "gpt5-mini":    "openai/gpt-5-mini",
    "haiku":        "anthropic/claude-haiku-4.5",
    "haiku-4.5":    "anthropic/claude-haiku-4.5",
    "claude":       "anthropic/claude-haiku-4.5",
    "claude-haiku": "anthropic/claude-haiku-4.5",
    # DR judge aliases
    "gpt-4o-mini":  "openai/gpt-4o-mini",
    "gpt4o-mini":   "openai/gpt-4o-mini",
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
            api_key_env="GROQ_API_KEY",
        )

    if backend == "openrouter":
        from .openai_client import OpenAICompatClient

        return OpenAICompatClient(
            model=model,
            supports_vision=info["vision"],
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            reasoning_effort=info.get("reasoning_effort"),
        )

    # Default: Gemini
    from .llm_client import GeminiClient

    return GeminiClient(model=model, api_key=api_key)
