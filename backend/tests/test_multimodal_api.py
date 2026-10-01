import json
import re

from fastapi.testclient import TestClient

from app.agent.run_manager import AgentRunManager
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from agent_helpers import build_fake_agent_service
from vision_helpers import build_vision_service, image_bytes


def test_stage_upload_attach_and_observation_api(tmp_path):
    workflow, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    workflow.dependencies.vision_service = build_vision_service(tmp_path)
    manager = AgentRunManager(workflow, tmp_path / "runs.sqlite3")
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        upload = client.post(
            "/api/v1/agent/inspection-images?equipment_id=fake-rig",
            content=image_bytes(),
            headers={
                "Content-Type": "image/png",
                "X-Filename": r"C:\Users\operator\inspection.png",
            },
        )
        assert upload.status_code == 201
        upload_body = upload.json()
        image_id = upload_body["image_id"]
        assert "file_ref" not in upload_body
        assert upload_body["original_filename"] == "inspection.png"
        assert upload_body["image_url"] == f"/api/v1/agent/inspection-images/{image_id}"
        created = client.post(
            "/api/v1/agent/runs",
            json={
                "equipment_id": "fake-rig",
                "measurement_id": "fake:measurement:1",
                "inspection_image_ids": [image_id],
            },
        )
        assert created.status_code == 202
        run_id = created.json()["run_id"]
        completed = manager.wait_for_status(run_id, {"COMPLETED"})
        images = client.get(f"/api/v1/agent/runs/{run_id}/inspection-images")
        observation = client.get(f"/api/v1/agent/inspection-images/{image_id}/observations")
        image_response = client.get(f"/api/v1/agent/inspection-images/{image_id}")
    finally:
        app.dependency_overrides.clear()
        manager.close()
    assert completed.visual_observations
    assert images.status_code == 200
    images_body = images.json()
    public_image = images_body["images"][0]["image"]
    serialized = json.dumps(images_body)
    assert public_image["run_id"] == run_id
    assert public_image["image_id"] == image_id
    assert public_image["mime_type"] == "image/png"
    assert public_image["size_bytes"] > 0
    assert public_image["image_url"] == f"/api/v1/agent/inspection-images/{image_id}"
    assert "file_ref" not in serialized
    assert str(tmp_path) not in serialized
    assert "/Users/" not in serialized
    assert re.search(r"[A-Za-z]:[\\/]", serialized) is None
    assert observation.status_code == 200
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/png"


def test_upload_rejects_spoofed_content(tmp_path):
    workflow, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    workflow.dependencies.vision_service = build_vision_service(tmp_path)
    manager = AgentRunManager(workflow, tmp_path / "runs.sqlite3")
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    try:
        response = TestClient(app).post(
            "/api/v1/agent/inspection-images?equipment_id=fake-rig",
            content=b"not-an-image",
            headers={"Content-Type": "image/png", "X-Filename": "fake.png"},
        )
    finally:
        app.dependency_overrides.clear()
        manager.close()
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INSPECTION_IMAGE"
