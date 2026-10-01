from pathlib import Path

import pytest

from app.rag.ingestion.parsers import parse_html, parse_pdf


@pytest.mark.integration
def test_real_pdf_parser_preserves_pages_and_text() -> None:
    root = Path(__file__).resolve().parents[2]
    blocks = parse_pdf(root / "data/paderborn/docs/K001/K001.pdf")

    assert blocks
    assert blocks[0].page == 1
    assert "rolling bearing" in blocks[0].text.lower()
    assert blocks[0].metadata["extraction_method"] == "pypdf-native-text"


@pytest.mark.integration
def test_real_html_parser_removes_scripts_and_preserves_sections() -> None:
    root = Path(__file__).resolve().parents[2]
    blocks = parse_html(
        root / "knowledge/bearing_v1/paderborn/operating_conditions.html"
    )

    assert blocks
    assert any(block.section for block in blocks)
    assert all("<script" not in block.text.lower() for block in blocks)
