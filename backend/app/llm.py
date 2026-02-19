"""
LLM factory module for PulseCast.

Provides a unified interface for LLM providers (Ollama, OpenAI).
Ollama is the primary provider for local, free inference.
"""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

LLMProvider = Literal["ollama", "openai"]


def get_llm() -> BaseChatModel:
    """
    Get the LLM client based on LLM_PROVIDER environment variable.

    Default: Ollama with llama3.2:3b

    Environment variables:
        LLM_PROVIDER: "ollama" (default) or "openai"
        OLLAMA_MODEL: Model name for Ollama (default: llama3.2:3b)
        OLLAMA_BASE_URL: Ollama server URL (default: http://host.docker.internal:11434)
        OPENAI_API_KEY: Required when LLM_PROVIDER=openai
        OPENAI_MODEL: Model for OpenAI (default: gpt-4o-mini)

    Returns:
        BaseChatModel: Configured LLM client
    """
    provider: LLMProvider = os.getenv("LLM_PROVIDER", "ollama").lower()  # type: ignore

    if provider == "ollama":
        return _get_ollama_llm()
    elif provider == "openai":
        return _get_openai_llm()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'ollama' or 'openai'.")


def _get_ollama_llm() -> BaseChatModel:
    """Get Ollama LLM client."""
    from langchain_ollama import ChatOllama

    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


def _get_openai_llm() -> BaseChatModel:
    """Get OpenAI LLM client (fallback)."""
    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    return ChatOpenAI(
        model=model,
        temperature=temperature,
    )
