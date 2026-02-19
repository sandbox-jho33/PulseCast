"""
Content ingestion module for PulseCast.

Fetches content from URLs and extracts clean markdown.
"""

from __future__ import annotations

import re
import ssl
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

# Use system certificates for SSL
_ssl_context = ssl.create_default_context(cafile="/usr/lib/ssl/cert.pem")


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
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        verify=_ssl_context,
    ) as client:
        response = await client.get(source_url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "lxml")

    title = _extract_title(soup)
    content = _extract_main_content(soup)
    markdown = _html_to_markdown(content)

    markdown = _clean_markdown(markdown)

    return IngestionResult(title=title, markdown=markdown)


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
    soup = BeautifulSoup(html, "lxml")

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
