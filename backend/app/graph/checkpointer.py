"""
LangGraph checkpointer for persisting graph state between nodes.

This module provides a singleton InMemorySaver that captures state
after each node execution, enabling real-time progress tracking.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import InMemorySaver

_checkpointer: Optional[InMemorySaver] = None


def get_checkpointer() -> InMemorySaver:
    """Get the singleton checkpointer instance."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = InMemorySaver()
    return _checkpointer


def make_thread_config(job_id: str) -> Dict[str, Any]:
    """Create a config dict with thread_id for LangGraph checkpointing."""
    return {"configurable": {"thread_id": job_id}}
