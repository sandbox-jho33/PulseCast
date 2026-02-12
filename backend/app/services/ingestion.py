"""
Content ingestion interfaces for PulseCast.

This module defines a thin abstraction over URL / document ingestion so that
the graph can depend on a stable interface. The concrete implementation will
be added in a dedicated ingestion task.
"""

from __future__ import annotations


async def ingest_source(source_url: str) -> str:
    """
    Ingest and normalize content from a source URL.

    Expected responsibilities in the full implementation:
    - Fetch the URL (e.g. via Crawl4AI / Playwright).
    - Convert HTML (or other formats) into normalized Markdown or text.
    - Handle errors and return a representation suitable for the researcher node.
    """
    raise NotImplementedError("ingest_source will be implemented in the ingestion task")

