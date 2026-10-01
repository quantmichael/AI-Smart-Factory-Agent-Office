from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.system import ComponentStatus, SystemStatusService


def _component(body: dict, component_id: str) -> dict:
    return next(item for item in body["components"] if item["component_id"] == component_id)


def test_system_status_reports_real_components_and_counts_without_paths():
    response = TestClient(app).get("/api/v1/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "READY"
    assert body["application_version"] == get_settings().app_version

    model = _component(body, "ml_model")
    assert model["status"] == "READY"
    assert model["summary"] == "모델 로드 가능"
    assert {item["label"]: item["value"] for item in model["details"]}["Algorithm"] == "RandomForestClassifier"

    vector = _component(body, "vector_db")
    vector_details = {item["label"]: item["value"] for item in vector["details"]}
    assert vector_details["Collection"] == "bearing_v1"
    assert int(vector_details["Embeddings"]) == 183

    run_database = _component(body, "run_database")
    assert int(run_database["details"][0]["value"]) >= 1
    memory = _component(body, "long_term_memory")
    assert int(memory["details"][0]["value"]) >= 1

    serialized = response.text.lower()
    for forbidden in (
        "/users/",
        "sqlite:///",
        "api_key",
        "password",
        "credential",
        "openai_api_key",
        "traceback",
    ):
        assert forbidden not in serialized


def test_missing_vector_store_degrades_only_that_component(tmp_path: Path):
    settings = get_settings().model_copy(update={"vector_db_path": tmp_path / "missing-vector"})

    result = SystemStatusService(settings).inspect()

    vector = next(item for item in result.components if item.component_id == "vector_db")
    assert vector.status is ComponentStatus.UNAVAILABLE
    assert result.overall_status is ComponentStatus.DEGRADED
    assert next(item for item in result.components if item.component_id == "ml_model").status is ComponentStatus.READY
    assert not (tmp_path / "missing-vector").exists()


def test_status_inspection_does_not_create_missing_directories_or_databases(tmp_path: Path):
    root = tmp_path / "must-not-be-created"
    settings = get_settings().model_copy(
        update={
            "paderborn_data_root": root / "dataset",
            "knowledge_base_root": root / "knowledge",
            "ml_artifact_root": root / "models",
            "vector_db_path": root / "vectors",
            "agent_run_db_path": root / "run" / "agent.sqlite3",
            "agent_checkpoint_path": root / "checkpoint" / "checkpoint.sqlite3",
            "equipment_memory_db_path": root / "memory" / "memory.sqlite3",
            "inspection_image_db_path": root / "vision" / "vision.sqlite3",
        }
    )

    result = SystemStatusService(settings).inspect()

    assert result.overall_status is ComponentStatus.UNAVAILABLE
    assert not root.exists()
    statuses = {item.component_id: item.status for item in result.components}
    assert statuses["backend_api"] is ComponentStatus.READY
    assert statuses["ml_model"] is ComponentStatus.UNAVAILABLE
    assert statuses["run_database"] is ComponentStatus.UNAVAILABLE


def test_zero_vision_records_are_ready_not_an_error():
    result = SystemStatusService(get_settings()).inspect()
    vision = next(item for item in result.components if item.component_id == "multimodal")
    details = {item.label: item.value for item in vision.details}

    assert vision.status is ComponentStatus.READY
    assert int(details["Stored Images"]) >= 0
    assert int(details["Observations"]) >= 0
