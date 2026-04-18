"""
LLM factory module for PulseCast.

Provides a unified interface for LLM providers (Ollama, OpenAI, Anthropic).
Provider is selected per-request by the frontend; credentials are read from
environment variables only.
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(provider: Optional[str] = None) -> BaseChatModel:
    """
    Get the LLM client for the given provider.

    Args:
        provider: "ollama", "openai", or "anthropic". Falls back to LLM_PROVIDER env var.

    Environment variables:
        LLM_PROVIDER: default provider if none is supplied
        OLLAMA_MODEL, OLLAMA_BASE_URL: Ollama settings
        OPENAI_API_KEY, OPENAI_MODEL: required when provider=openai
        ANTHROPIC_API_KEY, ANTHROPIC_MODEL: required when provider=anthropic
    """
    resolved = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()

    if resolved == "ollama":
        return _get_ollama_llm()
    elif resolved == "openai":
        return _get_openai_llm()
    elif resolved == "anthropic":
        return _get_anthropic_llm()
    else:
        raise ValueError(
            f"Unknown LLM provider: {resolved!r}. Use 'ollama', 'openai', or 'anthropic'."
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


def _get_openai_llm() -> BaseChatModel:
    """Get OpenAI LLM client."""
    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY env var is required when provider=openai")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def _get_anthropic_llm() -> BaseChatModel:
    """Get Anthropic LLM client."""
    from langchain_anthropic import ChatAnthropic

    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var is required when provider=anthropic")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )
