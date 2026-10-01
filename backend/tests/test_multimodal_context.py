from agent_helpers import build_fake_agent_service
from vision_helpers import build_vision_service, image_bytes


def test_sensor_visual_rag_and_memory_contexts_remain_separate(tmp_path):
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    vision = build_vision_service(tmp_path)
    service.dependencies.vision_service = vision
    image = vision.store(equipment_id="fake-rig", content=image_bytes(), mime_type="image/png", filename="inspection.png")
    vision.attach(image.image_id, "run-multimodal", "fake-rig")
    state = service.start_run("fake:measurement:1", run_id="run-multimodal", inspection_image_ids=[image.image_id])
    candidate = state["diagnosis_candidates"][0]
    assert state["analysis_result"]["measurement_id"] == "fake:measurement:1"
    assert state["rag_evidence"]
    assert state["visual_observations"][0]["image_id"] == image.image_id
    assert candidate["supporting_visual_observation_ids"]
    diagnose = next(item for item in state["events"] if item["node"] == "diagnose" and item["event_type"] == "node_completed")
    assert diagnose["payload"]["context_sections"] == ["CURRENT_SENSOR_ANALYSIS", "VISUAL_OBSERVATIONS", "TECHNICAL_EVIDENCE", "EQUIPMENT_MEMORY", "HUMAN_OBSERVATIONS"]
    service.close()
