from app.domain.schemas import AnalysisResult
from app.rag.retrieval import (
    QueryBuilder,
    RetrievalMode,
    RetrievalPurpose,
    build_retrieval_context,
)
import pytest


def _analysis() -> AnalysisResult:
    return AnalysisResult(
        analysis_id="analysis-1",
        measurement_id="measurement-1",
        model_id="model-1",
        status="abnormal",
        predicted_class="damaged",
        confidence=0.8,
        signal_features={"rms": 1.2, "kurtosis": 4.5},
        metadata={"bearing_id": "KA01", "operating_condition": "N15_M07_F10"},
    )


def test_query_builder_separates_purposes_and_is_stable() -> None:
    context = build_retrieval_context(_analysis())
    builder = QueryBuilder()
    queries = [builder.build(context, purpose) for purpose in RetrievalPurpose]

    assert len({query.query_id for query in queries}) == 3
    assert builder.build(context, RetrievalPurpose.DIAGNOSTIC_EVIDENCE).query_id == queries[1].query_id
    assert all(query.filters["knowledge_pack_id"] == "bearing_v1" for query in queries)
    assert all(query.filters["source_tier_lte"] == 2 for query in queries)


def test_diagnostic_mode_does_not_put_bearing_identity_or_fact_sheet_in_dataset_query() -> None:
    context = build_retrieval_context(_analysis(), mode=RetrievalMode.DIAGNOSTIC)
    query = QueryBuilder().build(context, RetrievalPurpose.DATASET_EVIDENCE)

    assert "KA01" not in query.query_text
    assert "PADERBORN_DAMAGE_FACT_SHEETS" not in query.filters["source_id_in"]
    assert "ground_truth" not in query.model_dump_json().lower()


def test_evaluation_mode_can_explicitly_target_bearing_fact_sheet() -> None:
    context = build_retrieval_context(_analysis(), mode=RetrievalMode.EVALUATION)
    query = QueryBuilder().build(context, RetrievalPurpose.DATASET_EVIDENCE)

    assert "KA01" in query.query_text
    assert "PADERBORN_DAMAGE_FACT_SHEETS" in query.filters["source_id_in"]


def test_diagnostic_filter_cannot_override_ground_truth_boundary() -> None:
    with pytest.raises(ValueError, match="outside the purpose/mode boundary"):
        QueryBuilder().build_text_query(
            "bearing K001",
            RetrievalPurpose.DATASET_EVIDENCE,
            mode=RetrievalMode.DIAGNOSTIC,
            filters={"source_id": "PADERBORN_DAMAGE_FACT_SHEETS"},
        )
