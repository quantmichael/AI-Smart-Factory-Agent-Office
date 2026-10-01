from app.ml.inference.service import STATUS_BY_CLASS


def test_analysis_result_mapping_is_explicit() -> None:
    assert STATUS_BY_CLASS == {"healthy": "normal", "damaged": "abnormal"}
