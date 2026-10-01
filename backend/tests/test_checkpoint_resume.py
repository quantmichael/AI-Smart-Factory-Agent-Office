from pathlib import Path

import pytest

from agent_helpers import build_fake_agent_service


def test_sqlite_checkpoint_can_be_loaded_by_a_new_service_without_rerun(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.sqlite3"
    first, analysis1, _ = build_fake_agent_service(checkpoint, status="normal")
    state = first.start_run("fake:measurement:1", run_id="checkpoint-run")
    first.close()

    second, analysis2, _ = build_fake_agent_service(checkpoint, status="normal")
    try:
        loaded = second.get_run("checkpoint-run")
        resumed = second.resume_run("checkpoint-run")
    finally:
        second.close()

    assert analysis1.calls == 1
    assert analysis2.calls == 0
    assert loaded == resumed
    assert resumed["workflow_status"] == "COMPLETED"
    assert resumed["events"] == state["events"]


def test_duplicate_run_id_is_rejected_without_reexecuting_nodes(tmp_path: Path) -> None:
    service, analysis, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", status="normal"
    )
    try:
        service.start_run("fake:measurement:1", run_id="idempotent-run")
        with pytest.raises(ValueError, match="already exists"):
            service.start_run("fake:measurement:1", run_id="idempotent-run")
    finally:
        service.close()

    assert analysis.calls == 1
