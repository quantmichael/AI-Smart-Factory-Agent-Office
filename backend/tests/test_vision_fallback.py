from agent_helpers import build_fake_agent_service
from vision_helpers import FailingVisionAnalyzer, build_vision_service, image_bytes


def test_vision_failure_records_unavailable_result_and_continues(tmp_path):
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    vision = build_vision_service(tmp_path, FailingVisionAnalyzer())
    service.dependencies.vision_service = vision
    image = vision.store(equipment_id="fake-rig", content=image_bytes(), mime_type="image/png", filename="inspection.png")
    vision.attach(image.image_id, "run-fallback", "fake-rig")
    state = service.start_run("fake:measurement:1", run_id="run-fallback", inspection_image_ids=[image.image_id])
    assert state["workflow_status"] == "COMPLETED"
    assert state["visual_observations"][0]["quality"] == "UNUSABLE"
    assert state["visual_observations"][0]["analysis_error"] == "TimeoutError"
    assert state["rag_evidence"]
    service.close()
