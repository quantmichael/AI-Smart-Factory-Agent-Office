"""Durable asynchronous run/event boundary used by the Agent HTTP API."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
import hashlib
import json
import logging
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Iterable
from uuid import uuid4

from app.agent.schemas import (
    AgentRunCreate,
    AgentRunCreated,
    AgentRunList,
    AgentRunSummary,
    AgentRunView,
    FinalReport,
    HumanInputSubmission,
)
from app.agent.service import AgentWorkflowService
from app.domain.schemas import AgentEvent, WorkflowStatus


logger = logging.getLogger(__name__)


class RunNotFoundError(KeyError):
    pass


class InvalidRunStateError(ValueError):
    pass


class HumanRequestAlreadyResolvedError(ValueError):
    pass


class HumanRequestNotFoundError(ValueError):
    pass


class ReportNotReadyError(ValueError):
    pass


class AgentRunManager:
    """Starts graph work off-request and persists UI-facing state and events."""

    def __init__(
        self,
        workflow: AgentWorkflowService,
        database_path: Path | str,
        *,
        max_workers: int = 4,
    ) -> None:
        self.workflow = workflow
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="agent-run"
        )
        self._setup()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _setup(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    equipment_id TEXT NOT NULL,
                    measurement_id TEXT NOT NULL,
                    demo_scenario TEXT,
                    workflow_status TEXT NOT NULL,
                    current_node TEXT NOT NULL,
                    analysis_result_json TEXT,
                    evidence_status TEXT,
                    evidence_count INTEGER NOT NULL DEFAULT 0,
                    pending_human_request_json TEXT,
                    final_report_available INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_events (
                    run_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (run_id, sequence),
                    FOREIGN KEY (run_id) REFERENCES agent_runs(run_id)
                );
                CREATE INDEX IF NOT EXISTS idx_agent_events_run_sequence
                    ON agent_events(run_id, sequence);
                CREATE TABLE IF NOT EXISTS resolved_human_requests (
                    request_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    resolved_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES agent_runs(run_id)
                );
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(agent_runs)").fetchall()
            }
            if "demo_scenario" not in columns:
                connection.execute("ALTER TABLE agent_runs ADD COLUMN demo_scenario TEXT")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def create_run(self, request: AgentRunCreate) -> AgentRunCreated:
        summary = self.workflow.dependencies.analysis_service.adapter.get_metadata(
            request.measurement_id
        )
        if summary.equipment_id != request.equipment_id:
            raise ValueError("equipment_id does not match the selected measurement")
        run_id = f"run_{uuid4().hex}"
        now = self._now()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs (
                    run_id, equipment_id, measurement_id, demo_scenario, workflow_status,
                    current_node, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    request.equipment_id,
                    request.measurement_id,
                    request.demo_scenario.value if request.demo_scenario else None,
                    WorkflowStatus.RUNNING.value,
                    "initialize_run",
                    now,
                    now,
                ),
            )
        image_ids = list(request.inspection_image_ids)
        vision = self.workflow.dependencies.vision_service
        if image_ids and vision is None:
            raise ValueError("inspection image service is not configured")
        for image_id in image_ids:
            vision.attach(image_id, run_id, request.equipment_id)
        self._executor.submit(
            self._execute_new,
            run_id,
            request.measurement_id,
            image_ids,
            request.demo_scenario.value if request.demo_scenario else None,
        )
        logger.info("agent run created", extra={"run_id": run_id, "endpoint": "create_run"})
        return AgentRunCreated(
            run_id=run_id,
            status=WorkflowStatus.RUNNING,
            current_node="initialize_run",
            created_at=datetime.fromisoformat(now),
        )

    def _execute_new(
        self,
        run_id: str,
        measurement_id: str,
        image_ids: list[str],
        demo_scenario: str | None = None,
    ) -> None:
        self._consume(
            run_id,
            self.workflow.stream_new_run(
                measurement_id,
                run_id=run_id,
                inspection_image_ids=image_ids,
                demo_scenario=demo_scenario,
            ),
        )

    def _execute_resume(self, run_id: str, submission: HumanInputSubmission) -> None:
        self._consume(run_id, self.workflow.stream_human_input(run_id, submission))

    def _consume(self, run_id: str, states: Iterable[dict]) -> None:
        try:
            for state in states:
                if state.get("current_node"):
                    self._persist_state(state)
            final = self.workflow.get_run(run_id)
            if final:
                self._persist_state(final)
        except Exception:
            logger.exception("agent run execution failed", extra={"run_id": run_id})
            self._persist_execution_error(run_id)

    def _persist_state(self, state: dict) -> None:
        run_id = state["run_id"]
        status = state.get("workflow_status", WorkflowStatus.RUNNING.value)
        now = self._now()
        analysis = state.get("analysis_result")
        pending = state.get("pending_human_request")
        events = [AgentEvent.model_validate(item) for item in state.get("events", [])]
        with self._write_lock, self._connection() as connection:
            connection.execute(
                """
                UPDATE agent_runs SET
                    equipment_id = COALESCE(?, equipment_id),
                    workflow_status = ?, current_node = ?,
                    analysis_result_json = ?, evidence_status = ?,
                    evidence_count = ?, pending_human_request_json = ?,
                    final_report_available = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (
                    state.get("equipment_id"),
                    status,
                    state.get("current_node", "initialize_run"),
                    json.dumps(analysis, ensure_ascii=False) if analysis else None,
                    state.get("evidence_status"),
                    len(state.get("rag_evidence", [])),
                    json.dumps(pending, ensure_ascii=False) if pending else None,
                    int(state.get("final_report") is not None),
                    now,
                    run_id,
                ),
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO agent_events
                    (run_id, sequence, event_id, event_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        event.sequence,
                        event.event_id,
                        event.model_dump_json(),
                        event.created_at.isoformat(),
                    )
                    for event in events
                ],
            )
        if status == WorkflowStatus.COMPLETED.value and self.workflow.dependencies.memory_service:
            try:
                self.workflow.dependencies.memory_service.record_run_memory(state)
            except Exception:
                logger.exception("equipment memory recording failed", extra={"run_id": run_id})

    def _persist_execution_error(self, run_id: str) -> None:
        with self._write_lock, self._connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS sequence FROM agent_events WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            sequence = int(row["sequence"]) + 1
            now = datetime.now(UTC)
            identity = f"{run_id}:workflow_error:{sequence}"
            event = AgentEvent(
                event_id="event_" + hashlib.sha256(identity.encode()).hexdigest()[:20],
                run_id=run_id,
                sequence=sequence,
                event_type="workflow_error",
                node="system",
                agent_role="SYSTEM",
                message="Workflow execution failed.",
                payload={"error_type": "AGENT_EXECUTION_ERROR"},
                created_at=now,
            )
            connection.execute(
                """INSERT OR IGNORE INTO agent_events
                   (run_id, sequence, event_id, event_json, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (run_id, sequence, event.event_id, event.model_dump_json(), now.isoformat()),
            )
            connection.execute(
                """UPDATE agent_runs SET workflow_status = ?, current_node = ?,
                   error_code = ?, updated_at = ? WHERE run_id = ?""",
                (
                    WorkflowStatus.FAILED.value,
                    "system",
                    "AGENT_EXECUTION_ERROR",
                    now.isoformat(),
                    run_id,
                ),
            )

    def get_run(self, run_id: str) -> AgentRunView:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM agent_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise RunNotFoundError(run_id)
        checkpoint = self.workflow.get_run(run_id) or {}
        return AgentRunView(
            run_id=row["run_id"],
            equipment_id=row["equipment_id"],
            measurement_id=row["measurement_id"],
            demo_scenario=checkpoint.get("demo_scenario") or row["demo_scenario"],
            workflow_status=row["workflow_status"],
            current_node=row["current_node"],
            analysis_result=(
                json.loads(row["analysis_result_json"])
                if row["analysis_result_json"]
                else None
            ),
            evidence_status=row["evidence_status"],
            evidence_count=row["evidence_count"],
            retrieval_retry_count=checkpoint.get("retrieval_retry_count", 0),
            diagnosis_candidates=checkpoint.get("diagnosis_candidates", []),
            inspection_plan=checkpoint.get("inspection_plan", []),
            recommended_actions=checkpoint.get("recommended_actions", []),
            memory_used_ids=checkpoint.get("memory_used_ids", []),
            inspection_image_ids=checkpoint.get("inspection_image_ids", []),
            visual_observations=checkpoint.get("visual_observations", []),
            version_trace=checkpoint.get("version_trace", self.workflow.dependencies.version_trace),
            pending_human_request=(
                json.loads(row["pending_human_request_json"])
                if row["pending_human_request_json"]
                else None
            ),
            final_report_available=bool(row["final_report_available"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_runs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        workflow_status: WorkflowStatus | None = None,
        measurement_id: str | None = None,
        equipment_id: str | None = None,
        ml_prediction: str | None = None,
    ) -> AgentRunList:
        """Return persisted run summaries without loading LangGraph checkpoints."""

        conditions: list[str] = []
        params: list[object] = []
        if workflow_status is not None:
            conditions.append("runs.workflow_status = ?")
            params.append(workflow_status.value)
        if measurement_id:
            conditions.append("instr(lower(runs.measurement_id), lower(?)) > 0")
            params.append(measurement_id)
        if equipment_id:
            conditions.append("instr(lower(runs.equipment_id), lower(?)) > 0")
            params.append(equipment_id)
        if ml_prediction:
            conditions.append("json_extract(runs.analysis_result_json, '$.status') = ?")
            params.append(ml_prediction)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        hitl_status = """
            CASE
                WHEN runs.pending_human_request_json IS NOT NULL THEN 'PENDING'
                WHEN EXISTS (
                    SELECT 1 FROM resolved_human_requests resolved
                    WHERE resolved.run_id = runs.run_id
                ) THEN 'RESOLVED'
                ELSE 'NONE'
            END AS hitl_status
        """
        with self._connection() as connection:
            total = int(
                connection.execute(
                    f"SELECT COUNT(*) AS count FROM agent_runs runs {where}", params
                ).fetchone()["count"]
            )
            rows = connection.execute(
                f"""
                SELECT runs.*, {hitl_status}
                FROM agent_runs runs
                {where}
                ORDER BY runs.created_at DESC, runs.run_id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, (page - 1) * page_size],
            ).fetchall()

        items: list[AgentRunSummary] = []
        for row in rows:
            analysis = (
                json.loads(row["analysis_result_json"])
                if row["analysis_result_json"]
                else {}
            )
            confidence = analysis.get("confidence")
            items.append(
                AgentRunSummary(
                    run_id=row["run_id"],
                    equipment_id=row["equipment_id"],
                    measurement_id=row["measurement_id"],
                    demo_scenario=row["demo_scenario"],
                    workflow_status=row["workflow_status"],
                    ml_prediction=analysis.get("status") or analysis.get("predicted_class"),
                    ml_confidence=float(confidence) if confidence is not None else None,
                    evidence_count=row["evidence_count"],
                    final_report_available=bool(row["final_report_available"]),
                    hitl_status=row["hitl_status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return AgentRunList(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    def get_events(self, run_id: str, *, after_sequence: int = 0) -> list[AgentEvent]:
        self.get_run(run_id)
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT event_json FROM agent_events
                   WHERE run_id = ? AND sequence > ? ORDER BY sequence""",
                (run_id, after_sequence),
            ).fetchall()
        return [AgentEvent.model_validate_json(row["event_json"]) for row in rows]

    def submit_human_input(
        self, run_id: str, submission: HumanInputSubmission
    ) -> AgentRunView:
        try:
            request = self.workflow.validate_human_input(run_id, submission)
        except KeyError as exc:
            raise RunNotFoundError(run_id) from exc
        except ValueError as exc:
            with self._connection() as connection:
                duplicate = connection.execute(
                    "SELECT 1 FROM resolved_human_requests WHERE request_id = ?",
                    (submission.request_id,),
                ).fetchone()
            if duplicate:
                raise HumanRequestAlreadyResolvedError(submission.request_id) from exc
            if str(exc) in {
                "run has no pending human request",
                "request_id does not match the pending request",
            }:
                raise HumanRequestNotFoundError(submission.request_id) from exc
            raise InvalidRunStateError(str(exc)) from exc
        now = self._now()
        try:
            with self._write_lock, self._connection() as connection:
                connection.execute(
                    """INSERT INTO resolved_human_requests
                       (request_id, run_id, response_json, resolved_at)
                       VALUES (?, ?, ?, ?)""",
                    (
                        request.request_id,
                        run_id,
                        submission.model_dump_json(),
                        now,
                    ),
                )
                connection.execute(
                    """UPDATE agent_runs SET workflow_status = ?, updated_at = ?
                       WHERE run_id = ?""",
                    (WorkflowStatus.RUNNING.value, now, run_id),
                )
        except sqlite3.IntegrityError as exc:
            raise HumanRequestAlreadyResolvedError(request.request_id) from exc
        self._executor.submit(self._execute_resume, run_id, submission)
        return self.get_run(run_id)

    def get_report(self, run_id: str) -> FinalReport:
        self.get_run(run_id)
        state = self.workflow.get_run(run_id)
        if not state or not state.get("final_report"):
            raise ReportNotReadyError(run_id)
        return FinalReport.model_validate(state["final_report"])

    def get_evidence(self, run_id: str) -> list[dict]:
        self.get_run(run_id)
        state = self.workflow.get_run(run_id)
        return list((state or {}).get("rag_evidence", []))

    def store_staged_image(
        self, *, equipment_id: str, content: bytes, mime_type: str, filename: str, description: str | None
    ):
        service = self.workflow.dependencies.vision_service
        if service is None:
            raise InvalidRunStateError("inspection image service is not configured")
        return service.store(
            equipment_id=equipment_id,
            content=content,
            mime_type=mime_type,
            filename=filename,
            description=description,
        )

    def upload_run_image(
        self, run_id: str, *, content: bytes, mime_type: str, filename: str, description: str | None
    ):
        run = self.get_run(run_id)
        if run.workflow_status not in {WorkflowStatus.CREATED, WorkflowStatus.WAITING}:
            raise InvalidRunStateError("images may be added only before execution or while waiting for human input")
        service = self.workflow.dependencies.vision_service
        if service is None:
            raise InvalidRunStateError("inspection image service is not configured")
        return service.store(
            equipment_id=run.equipment_id,
            run_id=run_id,
            content=content,
            mime_type=mime_type,
            filename=filename,
            description=description,
        )

    def get_images(self, run_id: str) -> list[dict]:
        self.get_run(run_id)
        service = self.workflow.dependencies.vision_service
        return service.list_for_run(run_id) if service else []

    def get_visual_observation(self, image_id: str):
        service = self.workflow.dependencies.vision_service
        if service is None:
            raise KeyError(image_id)
        result = service.repository.get_observation(image_id)
        if result is None:
            raise KeyError(image_id)
        return result

    def get_image_record(self, image_id: str):
        service = self.workflow.dependencies.vision_service
        if service is None:
            raise KeyError(image_id)
        record = service.repository.get_image(image_id)
        if record is None:
            raise KeyError(image_id)
        return record

    def wait_for_status(
        self, run_id: str, statuses: set[str], *, timeout_seconds: float = 10.0
    ) -> AgentRunView:
        """Test/demo helper; production API clients poll or consume SSE."""

        from time import monotonic, sleep

        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            run = self.get_run(run_id)
            if run.workflow_status.value in statuses:
                return run
            sleep(0.01)
        raise TimeoutError(f"run {run_id} did not reach {sorted(statuses)}")

    def close(self) -> None:
        self._executor.shutdown(wait=True)
        self.workflow.close()
