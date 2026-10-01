import json
from pathlib import Path

from app.rag.evaluation import evaluate_cases
from rag_helpers import build_test_retriever


def test_evaluation_set_has_required_size_and_categories() -> None:
    path = Path(__file__).resolve().parents[1] / "app/rag/evaluation/evaluation_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))

    assert 20 <= len(cases) <= 30
    categories = {case["category"] for case in cases}
    assert {
        "dataset context",
        "damage fact",
        "vibration diagnosis",
        "failure analysis",
        "inspection",
        "maintenance",
        "unanswerable",
        "conflicting evidence",
    } <= categories
    assert any(not case.get("answerable", True) for case in cases)


def test_evaluation_metrics_are_computed_from_retrieved_sources(tmp_path) -> None:
    service = build_test_retriever(tmp_path / "vector")
    cases = [
        {
            "case_id": "answerable",
            "question": "bearing vibration spectrum defect frequency",
            "purpose": "DIAGNOSTIC_EVIDENCE",
            "expected_source_ids": ["SKF_VIBRATION_DIAGNOSTIC_GUIDE"],
            "expected_document_types": ["vibration_diagnostic_guide"],
        },
        {
            "case_id": "unanswerable",
            "question": "PLC ladder address",
            "purpose": "INSPECTION_ACTION",
            "expected_source_ids": [],
            "expected_document_types": [],
            "answerable": False,
        },
    ]

    metrics, results = evaluate_cases(service, cases)

    assert metrics["case_count"] == 2
    assert metrics["hit_at_3"] == 1
    assert metrics["recall_at_5"] == 1
    assert metrics["mrr"] == 1
    assert len(results) == 2
