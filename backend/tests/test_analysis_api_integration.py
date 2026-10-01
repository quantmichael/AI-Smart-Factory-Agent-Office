from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.v1.analysis import get_analysis_service
from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.main import app
from app.services.analysis import build_analysis_service


@pytest.mark.integration
def test_real_analysis_api_for_healthy_and_damaged_measurements() -> None:
    project_root = Path(__file__).resolve().parents[2]
    dataset_root = project_root / "data/paderborn"
    artifact_root = project_root / "artifacts/ml"
    if not dataset_root.is_dir() or not (artifact_root / "baseline_v1/model.joblib").is_file():
        pytest.skip("local STEP 04 data/model artifacts are unavailable")
    service = build_analysis_service(
        dataset_root,
        artifact_root,
        "bearing_rf_binary_v1",
        PaderbornDatasetAdapter,
    )
    adapter = service.adapter
    healthy = next(x for x in adapter.list_measurements() if x.ground_truth.state == "healthy")
    damaged = next(x for x in adapter.list_measurements() if x.ground_truth.state == "damaged")
    app.dependency_overrides[get_analysis_service] = lambda: service
    try:
        client = TestClient(app)
        responses = [
            client.post("/api/v1/analysis", json={"measurement_id": item.measurement_id})
            for item in (healthy, damaged)
        ]
        preview_response = client.get(
            f"/api/v1/measurements/{healthy.measurement_id}/preview",
            params={"max_points": 80},
        )
    finally:
        app.dependency_overrides.clear()

    for summary, response in zip((healthy, damaged), responses, strict=True):
        assert response.status_code == 200
        body = response.json()
        assert body["measurement_id"] == summary.measurement_id
        assert body["model_id"] == "bearing_rf_binary_v1"
        assert body["status"] in {"normal", "abnormal"}
        assert body["predicted_class"] in {"healthy", "damaged"}
        assert 0 <= body["confidence"] <= 1
        assert body["metadata"]["feature_version"] == "step03_v1"
    assert service.cached_model_ids == ("bearing_rf_binary_v1",)
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["measurement_id"] == healthy.measurement_id
    assert preview["equipment_id"] == healthy.equipment_id
    assert preview["channel"] == "vibration_1"
    assert 32 <= len(preview["points"]) <= 80
    assert preview["original_sample_count"] > len(preview["points"])
    assert set(preview["operating_signals"]) == {"speed", "torque", "force"}
    expected_times = [point["time"] for point in preview["points"]]
    for channel, points in preview["operating_signals"].items():
        assert [point["time"] for point in points] == expected_times
        raw_signal = adapter.load_measurement(healthy.measurement_id).signals[channel]
        expected = np.interp(
            expected_times[0],
            raw_signal.time,
            raw_signal.values,
        )
        assert points[0]["value"] == pytest.approx(expected)
