from pathlib import Path

from app.rag.ingestion.manifest import load_manifest


def test_real_manifest_validates_and_expands_only_declared_documents() -> None:
    project_root = Path(__file__).resolve().parents[2]
    payload, documents, statuses = load_manifest(
        project_root / "knowledge/bearing_v1/manifests/source_manifest.json",
        project_root,
    )

    assert payload["manifest_version"] == "1.0"
    assert len(statuses) == 12
    assert len(documents) == 15
    assert sum(item["status"] == "READY" for item in statuses) == 11
    assert next(item for item in statuses if item["source_id"] == "PADERBORN_DATASET")[
        "status"
    ] == "UNSUPPORTED"
    assert len({document.document_id for document in documents}) == 15
    assert all(len(document.sha256) == 64 for document in documents)


def test_manifest_fact_sheet_metadata_is_verified() -> None:
    project_root = Path(__file__).resolve().parents[2]
    _, documents, _ = load_manifest(
        project_root / "knowledge/bearing_v1/manifests/source_manifest.json",
        project_root,
    )
    ka01 = next(
        item
        for item in documents
        if item.document_id == "paderborn_damage_fact_sheets_ka01"
    )

    assert ka01.metadata["bearing_id"] == "KA01"
    assert ka01.metadata["bearing_state"] == "damaged"
    assert ka01.metadata["damage_location"] == "outer_ring_raceway"
