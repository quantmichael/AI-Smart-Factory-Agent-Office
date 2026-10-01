from pathlib import Path

from app.agent.run_manager import AgentRunManager
from agent_helpers import build_fake_agent_service


def build_fake_run_manager(path: Path, **service_kwargs) -> AgentRunManager:
    service, _, _ = build_fake_agent_service(
        path / "checkpoint.sqlite3", **service_kwargs
    )
    return AgentRunManager(service, path / "runs.sqlite3", max_workers=2)
