"""
LLM factory module for PulseCast.

Provides a unified interface for LLM providers (Ollama, OpenAI, Anthropic).
Ollama is the primary provider for local, free inference.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from langchain_core.language_models.chat_models import BaseChatModel

LLMProvider = Literal["ollama", "openai", "anthropic"]


def get_llm(provider: Optional[str] = None, api_key: Optional[str] = None) -> BaseChatModel:
    """
    Get the LLM client based on provider and optional api_key.

    Args:
        provider: "ollama", "openai", or "anthropic". Falls back to LLM_PROVIDER env var.
        api_key: User-supplied API key. Falls back to env var for cloud providers.

    Environment variables:
        LLM_PROVIDER: "ollama" (default), "openai", or "anthropic"
        OLLAMA_MODEL: Model name for Ollama (default: llama3.2:3b)
        OLLAMA_BASE_URL: Ollama server URL (default: http://host.docker.internal:11434)
        OPENAI_API_KEY: Used when LLM_PROVIDER=openai and no key passed
        OPENAI_MODEL: Model for OpenAI (default: gpt-4o-mini)
        ANTHROPIC_API_KEY: Used when LLM_PROVIDER=anthropic and no key passed
        ANTHROPIC_MODEL: Model for Anthropic (default: claude-3-5-haiku-20241022)
    """
    resolved_provider: str = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()

    if resolved_provider == "ollama":
        return _get_ollama_llm()
    elif resolved_provider == "openai":
        return _get_openai_llm(api_key)
    elif resolved_provider == "anthropic":
        return _get_anthropic_llm(api_key)
    else:
        raise ValueError(
            f"Unknown LLM provider: {resolved_provider!r}. Use 'ollama', 'openai', or 'anthropic'."
        )


def _get_ollama_llm() -> BaseChatModel:
    """Get Ollama LLM client."""
    from langchain_ollama import ChatOllama

    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    request_timeout = float(os.getenv("LLM_REQUEST_TIMEOUT", "120"))

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        request_timeout=request_timeout,
    )


def _get_openai_llm(api_key: Optional[str] = None) -> BaseChatModel:
    """Get OpenAI LLM client."""
    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=resolved_key,
    )


def _get_anthropic_llm(api_key: Optional[str] = None) -> BaseChatModel:
    """Get Anthropic LLM client."""
    from langchain_anthropic import ChatAnthropic

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=resolved_key,
    )
