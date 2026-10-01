from pathlib import Path

import pytest

from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.retrieval import (
    RetrievalPurpose,
    RetrieverService,
    build_retrieval_context,
)
from app.rag.vector_store import ChromaVectorStore
from app.services.analysis import build_analysis_service


@pytest.mark.integration
def test_real_analysis_result_to_diagnostic_evidence_without_ground_truth_leakage() -> None:
    root = Path(__file__).resolve().parents[2]
    analysis_service = build_analysis_service(
        root / "data/paderborn",
        root / "artifacts/ml",
        "bearing_rf_binary_v1",
        PaderbornDatasetAdapter,
    )
    summary = next(iter(analysis_service.adapter.list_measurements()))
    analysis = analysis_service.analyze(summary.measurement_id)
    context = build_retrieval_context(
        analysis, analysis_service.adapter.get_metadata(summary.measurement_id)
    )
    retriever = RetrieverService(
        ChromaVectorStore(root / "artifacts/vector_db", "bearing_v1"),
        LocalHashingEmbeddingService(),
    )

    result = retriever.retrieve_by_purpose(
        context, RetrievalPurpose.DIAGNOSTIC_EVIDENCE, top_k=3
    )

    assert result.evidence
    assert result.query.query_id
    assert context.bearing_id not in result.query.query_text
    assert analysis.predicted_class in result.query.query_text
    assert "ground_truth" not in context.model_dump()
    assert "PADERBORN_DAMAGE_FACT_SHEETS" not in result.query.filters["source_id_in"]
    assert "PADERBORN_MEASUREMENT_LOGS" not in result.query.filters["source_id_in"]
    assert all(item.query_id == result.query.query_id for item in result.evidence)
    assert all(item.official_url and item.content for item in result.evidence)
