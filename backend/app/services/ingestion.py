"""
Content ingestion module for PulseCast.

Fetches content from URLs and extracts clean markdown.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Send a real-browser User-Agent; many sites 403 the default httpx UA.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class IngestionResult:
    title: str
    markdown: str


async def ingest_source(source_url: str) -> IngestionResult:
    """
    Ingest content from a source URL and return title + markdown.

    Args:
        source_url: The URL to fetch and extract content from.

    Returns:
        IngestionResult with title and markdown content.

    Raises:
        httpx.HTTPError: If the URL cannot be fetched.
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers=_DEFAULT_HEADERS,
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.exception("Failed to fetch source URL %s", source_url)
        raise RuntimeError(f"Failed to fetch {source_url}: {e}") from e

    soup = _parse_html(html)

    title = _extract_title(soup)
    content = _extract_main_content(soup)
    markdown = _html_to_markdown(content)

    markdown = _clean_markdown(markdown)

    if not markdown:
        raise RuntimeError(
            f"Ingestion produced empty content from {source_url}; "
            "the page may be JS-rendered or blocked by anti-bot protection."
        )

    return IngestionResult(title=title, markdown=markdown)


def _parse_html(html: str) -> BeautifulSoup:
    """Parse HTML, falling back to the stdlib parser if lxml is unavailable."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        logger.warning("lxml parser unavailable; falling back to html.parser")
        return BeautifulSoup(html, "html.parser")


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract the page title."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return "Untitled"


def _extract_main_content(soup: BeautifulSoup) -> str:
    """Extract main content from the page."""
    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"content|article|post", re.I))
    )

    if article:
        return str(article)

    body = soup.find("body")
    if body:
        for tag in body.find_all(
            ["nav", "footer", "header", "aside", "script", "style", "form"]
        ):
            tag.decompose()
        return str(body)

    return str(soup)


def _html_to_markdown(html: str) -> str:
    """Convert HTML to simple markdown."""
    soup = _parse_html(html)

    for tag in soup.find_all(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()

    lines = []
    for element in soup.descendants:
        if element.name == "h1":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n# {text}\n")
        elif element.name == "h2":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n## {text}\n")
        elif element.name == "h3":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n### {text}\n")
        elif element.name == "h4":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n#### {text}\n")
        elif element.name == "p":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif element.name == "li":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif element.name == "blockquote":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n> {text}\n")
        elif element.name == "code":
            if element.parent and element.parent.name != "pre":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"`{text}`")
        elif element.name == "pre":
            text = element.get_text()
            if text:
                lines.append(f"\n```\n{text.strip()}\n```\n")
        elif element.name == "a":
            text = element.get_text(strip=True)
            href = element.get("href", "")
            if text and href:
                lines.append(f"[{text}]({href})")
        elif element.name == "strong" or element.name == "b":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"**{text}**")
        elif element.name == "em" or element.name == "i":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"*{text}*")

    return "\n".join(lines)


def _clean_markdown(markdown: str) -> str:
    """Clean up markdown content."""
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"^\s+|\s+$", "", markdown, flags=re.MULTILINE)
    return markdown.strip()
