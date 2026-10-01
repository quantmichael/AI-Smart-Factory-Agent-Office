from agent_helpers import build_fake_agent_service


def test_no_image_keeps_existing_abnormal_workflow_operational(tmp_path):
    service, analysis, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    state = service.start_run("fake:measurement:1", run_id="run-no-image")
    assert state["workflow_status"] == "COMPLETED"
    assert state["visual_observations"] == []
    assert analysis.calls == 1
    assert all(item["node"] != "analyze_inspection_image" for item in state["events"])
    service.close()
