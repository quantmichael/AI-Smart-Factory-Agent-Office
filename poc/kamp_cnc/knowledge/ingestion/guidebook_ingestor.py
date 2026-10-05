"""Extract page-aware chunks from the single authorized KAMP Guidebook."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


SOURCE_ID = "kamp-cnc-guidebook"
DOCUMENT_TITLE = "정밀가공 품질보증 AI 데이터셋 분석실습 가이드북"
PROVIDER = "KAMP"
INCLUDED_PAGES = (*range(5, 18), *range(23, 41))


def section_for_page(page: int) -> str:
    if page == 5:
        return "1 분석요약"
    if page == 6:
        return "1.1 분석 배경 - 공정 개요 및 이슈사항"
    if page == 7:
        return "1.1 분석 배경 - 문제해결 및 분석 목표"
    if page == 8:
        return "1.2 분석 목표 - 데이터 정의 및 기대효과"
    if 9 <= page <= 13:
        return "2.1 제조데이터 소개 및 데이터 품질"
    if 14 <= page <= 17:
        return "2.2 분석 모델 소개"
    if 23 <= page <= 32:
        return "2 분석실습 - 데이터 탐색 및 전처리"
    return "2 분석실습 - 학습 및 평가"


class GuidebookIngestor:
    def __init__(self, pdf_path: str | Path, max_chars: int = 600) -> None:
        self.pdf_path = Path(pdf_path)
        self.max_chars = max_chars

    def extract_pages(self) -> dict[int, str]:
        reader = PdfReader(self.pdf_path)
        pages: dict[int, str] = {}
        for page_number in INCLUDED_PAGES:
            raw = reader.pages[page_number - 1].extract_text() or ""
            pages[page_number] = self._normalize(raw, page_number)
        return pages

    def build_chunks(self) -> tuple[list[dict[str, Any]], dict[int, str]]:
        pages = self.extract_pages()
        chunks: list[dict[str, Any]] = []
        for page_number, page_text in pages.items():
            for ordinal, text in enumerate(self._split(page_text), start=1):
                chunks.append({
                    "source_id": SOURCE_ID,
                    "document_title": DOCUMENT_TITLE,
                    "provider": PROVIDER,
                    "page": page_number,
                    "section": section_for_page(page_number),
                    "chunk_id": f"kamp-cnc-guidebook-p{page_number:02d}-c{ordinal:02d}",
                    "text": text,
                })
        return chunks, pages

    def source_sha256(self) -> str:
        return hashlib.sha256(self.pdf_path.read_bytes()).hexdigest()

    @staticmethod
    def _normalize(text: str, page_number: int) -> str:
        text = text.replace("\u00a0", " ").replace("\t", " ")
        text = re.sub(r"「정밀가공 품질보증 AI 데이터셋」\s*분석실습 가이드북", " ", text)
        text = re.sub(r"정밀가공 품질보증 AI 데이터셋, 분석실습 가이드북", " ", text)
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line and line not in {str(page_number), str(page_number - 1)}]
        return re.sub(r"\s+", " ", " ".join(lines)).strip()

    def _split(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+", text)
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if current and len(current) + len(sentence) + 1 > self.max_chars:
                chunks.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current)
        return chunks
