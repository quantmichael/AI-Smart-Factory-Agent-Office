"""Page-preserving PDF parser using native text extraction only."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from app.rag.ingestion.cleaning import clean_text
from app.rag.models import ParsedBlock


def _section_candidate(text: str) -> str | None:
    for line in text.splitlines():
        candidate = re.sub(r"\s+", " ", line).strip()
        if 3 <= len(candidate) <= 120 and not candidate.endswith((".", ",", ";")):
            return candidate
    return None


def parse_pdf(path: Path | str) -> list[ParsedBlock]:
    reader = PdfReader(Path(path))
    blocks: list[ParsedBlock] = []
    for page_number, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = clean_text(raw)
        if not text:
            continue
        blocks.append(
            ParsedBlock(
                page=page_number,
                section=_section_candidate(raw),
                text=text,
                metadata={"extraction_method": "pypdf-native-text"},
            )
        )
    if not blocks:
        raise ValueError(f"PDF has no extractable text: {path}")
    return blocks
