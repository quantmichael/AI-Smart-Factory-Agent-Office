"""HTML body parser that removes executable and navigation boilerplate."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from app.rag.ingestion.cleaning import clean_text
from app.rag.models import ParsedBlock


def parse_html(path: Path | str) -> list[ParsedBlock]:
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="replace"), "html.parser")
    root = soup.find("main") or soup.find("article") or soup.body or soup
    for tag in root.find_all(["script", "style", "nav", "footer", "noscript", "form"]):
        tag.decompose()
    blocks: list[ParsedBlock] = []
    section: str | None = None
    for element in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]):
        text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue
        if element.name.startswith("h"):
            section = text
            continue
        if element.name == "p" and element.find_parent("li") is not None:
            continue
        blocks.append(
            ParsedBlock(
                page=None,
                section=section,
                text=text,
                metadata={"html_element": element.name},
            )
        )
    if not blocks:
        text = clean_text(root.get_text("\n", strip=True))
        if text:
            blocks.append(ParsedBlock(text=text, metadata={"html_element": "body"}))
    if not blocks:
        raise ValueError(f"HTML has no extractable body text: {path}")
    return blocks
