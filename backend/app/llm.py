"""
LLM factory module for PulseCast.

Provides a unified interface for LLM providers (Ollama, OpenAI, Anthropic).
Provider is selected per request; credentials are decrypted from each user's
BYOK store by the caller and passed only server-side.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(provider: str, api_key: str) -> BaseChatModel:
    """
    Get the LLM client for the given provider.

    Args:
        provider: "openai" or "anthropic".
        api_key: User-provided API key from encrypted BYOK storage.
    """
    resolved = provider.lower()

    if resolved == "openai":
        return _get_openai_llm(api_key)
    elif resolved == "anthropic":
        return _get_anthropic_llm(api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {resolved!r}. Use 'openai' or 'anthropic'.")


def _get_openai_llm(api_key: str) -> BaseChatModel:
    """Get OpenAI LLM client."""
    import os

    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def _get_anthropic_llm(api_key: str) -> BaseChatModel:
    """Get Anthropic LLM client."""
    import os

    from langchain_anthropic import ChatAnthropic

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )
