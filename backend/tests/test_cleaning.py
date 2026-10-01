from app.rag.ingestion.cleaning import clean_text


def test_cleaning_preserves_terms_and_repairs_extraction_artifacts() -> None:
    raw = "Rolling bear-\ning\u00a0damage   analysis\n\nISO 15243"

    cleaned = clean_text(raw)

    assert cleaned == "Rolling bearing damage analysis\n\nISO 15243"
