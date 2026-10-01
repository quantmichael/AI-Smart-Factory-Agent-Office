"""Durable asynchronous Agent Run, SSE, HITL, evidence, and report APIs."""

from __future__ import annotations

import asyncio
import json
import logging
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse

from app.agent import HumanInputSubmission, build_agent_service
from app.agent.run_manager import (
    AgentRunManager,
    HumanRequestAlreadyResolvedError,
    HumanRequestNotFoundError,
    InvalidRunStateError,
    ReportNotReadyError,
    RunNotFoundError,
)
from app.agent.schemas import (
    AgentEventList,
    AgentRunCreate,
    AgentRunCreated,
    AgentRunList,
    AgentRunView,
    FinalReport,
)
from app.api.exceptions import APIError
from app.core.config import get_settings, resolve_runtime_path
from app.core.readiness import evaluate_readiness
from app.domain.schemas import WorkflowStatus
from app.vision import (
    InspectionImageRecord,
    PublicInspectionImage,
    PublicInspectionImageResult,
    RunInspectionImageList,
)


router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)
_manager: AgentRunManager | None = None
_manager_lock = Lock()


def get_agent_run_manager() -> AgentRunManager:
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                settings = get_settings()
                workflow = build_agent_service(
                    dataset_root=resolve_runtime_path(settings.paderborn_data_root),
                    ml_artifact_root=resolve_runtime_path(settings.ml_artifact_root),
                    active_model_id=settings.active_ml_model_id,
                    vector_db_path=resolve_runtime_path(settings.vector_db_path),
                    checkpoint_path=resolve_runtime_path(settings.agent_checkpoint_path),
                    memory_db_path=resolve_runtime_path(settings.equipment_memory_db_path),
                    vision_db_path=resolve_runtime_path(settings.inspection_image_db_path),
                    vision_upload_root=resolve_runtime_path(settings.inspection_upload_root),
                    vision_enabled=settings.vision_enabled,
                    vision_model=settings.vision_model,
                    max_image_size_mb=settings.max_image_size_mb,
                    max_image_dimension=settings.max_image_dimension,
                    application_version=settings.app_version,
                    knowledge_pack_id=settings.knowledge_pack_id,
                    knowledge_manifest_version=evaluate_readiness(settings)["versions"]["knowledge_manifest_version"],
                    workflow_version=settings.workflow_version,
                    max_retrieval_retries=settings.max_retrieval_retries,
                    max_human_information_rounds=settings.max_human_information_rounds,
                    max_action_revision_rounds=settings.max_action_revision_rounds,
                )
                _manager = AgentRunManager(
                    workflow,
                    resolve_runtime_path(settings.agent_run_db_path),
                    max_workers=settings.agent_background_workers,
                )
    return _manager


def _not_found(run_id: str) -> APIError:
    return APIError(404, "RUN_NOT_FOUND", "Agent run was not found.", {"run_id": run_id})


@router.post(
    "/runs",
    response_model=AgentRunCreated,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create an asynchronous agent run",
)
def create_agent_run(
    body: AgentRunCreate,
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> AgentRunCreated:
    started = monotonic()
    try:
        result = manager.create_run(body)
    except (KeyError, ValueError) as exc:
        raise APIError(
            422,
            "INVALID_RUN_REQUEST",
            "The selected measurement and equipment are not a valid run target.",
            {"reason": str(exc)},
        ) from exc
    except Exception as exc:
        raise APIError(500, "AGENT_START_FAILED", "Agent run could not be started.") from exc
    logger.info(
        "agent API request completed",
        extra={
            "run_id": result.run_id,
            "endpoint": "POST /agent/runs",
            "status": 202,
            "latency_ms": (monotonic() - started) * 1000,
        },
    )
    return result


@router.get("/runs", response_model=AgentRunList, summary="List persisted agent runs")
def list_agent_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    workflow_status: WorkflowStatus | None = Query(default=None),
    measurement_id: str | None = Query(default=None, min_length=1, max_length=256),
    equipment_id: str | None = Query(default=None, min_length=1, max_length=256),
    ml_prediction: str | None = Query(default=None, pattern="^(normal|abnormal)$"),
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> AgentRunList:
    return manager.list_runs(
        page=page,
        page_size=page_size,
        workflow_status=workflow_status,
        measurement_id=measurement_id,
        equipment_id=equipment_id,
        ml_prediction=ml_prediction,
    )


@router.get("/runs/{run_id}", response_model=AgentRunView)
def get_agent_run(
    run_id: str,
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> AgentRunView:
    try:
        return manager.get_run(run_id)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc


@router.get("/runs/{run_id}/events", response_model=AgentEventList)
def get_agent_events(
    run_id: str,
    after_sequence: int = Query(default=0, ge=0),
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> AgentEventList:
    try:
        events = manager.get_events(run_id, after_sequence=after_sequence)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    return AgentEventList(run_id=run_id, events=events)


@router.get("/runs/{run_id}/events/stream")
async def stream_agent_events(
    request: Request,
    run_id: str,
    after_sequence: int = Query(default=0, ge=0),
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> StreamingResponse:
    try:
        manager.get_run(run_id)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    settings = get_settings()

    async def event_source():
        cursor = after_sequence
        last_delivery = monotonic()
        while True:
            if await request.is_disconnected():
                break
            events = manager.get_events(run_id, after_sequence=cursor)
            for event in events:
                cursor = event.sequence
                data = json.dumps(
                    event.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")
                )
                yield f"id: {event.sequence}\nevent: {event.event_type}\ndata: {data}\n\n"
                last_delivery = monotonic()
            run = manager.get_run(run_id)
            if run.workflow_status in {
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.WAITING,
            }:
                break
            if monotonic() - last_delivery >= settings.sse_heartbeat_seconds:
                yield ": heartbeat\n\n"
                last_delivery = monotonic()
            await asyncio.sleep(settings.sse_poll_interval_seconds)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/runs/{run_id}/human-input",
    response_model=AgentRunView,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resume a waiting agent run with validated human input",
)
def submit_human_input(
    run_id: str,
    submission: HumanInputSubmission,
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> AgentRunView:
    try:
        return manager.submit_human_input(run_id, submission)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    except HumanRequestAlreadyResolvedError as exc:
        raise APIError(
            409,
            "HUMAN_REQUEST_ALREADY_RESOLVED",
            "This human request has already been resolved.",
            {"request_id": submission.request_id},
        ) from exc
    except HumanRequestNotFoundError as exc:
        raise APIError(
            404,
            "HUMAN_REQUEST_NOT_FOUND",
            "The pending human request was not found for this run.",
            {"request_id": submission.request_id},
        ) from exc
    except InvalidRunStateError as exc:
        raise APIError(409, "INVALID_RUN_STATE", str(exc), {"run_id": run_id}) from exc


@router.get("/runs/{run_id}/report", response_model=FinalReport)
def get_agent_report(
    run_id: str,
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> FinalReport:
    try:
        return manager.get_report(run_id)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    except ReportNotReadyError as exc:
        raise APIError(
            409, "REPORT_NOT_READY", "The final report is not available yet.", {"run_id": run_id}
        ) from exc


@router.get("/runs/{run_id}/evidence")
def get_agent_evidence(
    run_id: str,
    manager: AgentRunManager = Depends(get_agent_run_manager),
) -> dict:
    try:
        evidence = manager.get_evidence(run_id)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    return {"run_id": run_id, "evidence": evidence}


async def _read_image_body(request: Request) -> bytes:
    content = await request.body()
    if not content:
        raise APIError(422, "EMPTY_IMAGE", "Inspection image body is empty.")
    return content


def _public_inspection_image(record: InspectionImageRecord | dict) -> PublicInspectionImage:
    internal = InspectionImageRecord.model_validate(record)
    return PublicInspectionImage(
        **internal.model_dump(exclude={"file_ref"}),
        image_url=f"/api/v1/agent/inspection-images/{internal.image_id}",
    )


@router.post(
    "/inspection-images",
    response_model=PublicInspectionImage,
    status_code=status.HTTP_201_CREATED,
)
async def stage_inspection_image(
    request: Request,
    equipment_id: str = Query(min_length=1),
    description: str | None = Query(default=None, max_length=500),
    x_filename: str = Header(default="inspection-image"),
    manager: AgentRunManager = Depends(get_agent_run_manager),
):
    try:
        record = manager.store_staged_image(
            equipment_id=equipment_id,
            content=await _read_image_body(request),
            mime_type=request.headers.get("content-type", ""),
            filename=x_filename,
            description=description,
        )
        return _public_inspection_image(record)
    except ValueError as exc:
        raise APIError(422, "INVALID_INSPECTION_IMAGE", str(exc)) from exc


@router.post(
    "/runs/{run_id}/inspection-images",
    response_model=PublicInspectionImage,
    status_code=status.HTTP_201_CREATED,
)
async def upload_run_inspection_image(
    run_id: str,
    request: Request,
    description: str | None = Query(default=None, max_length=500),
    x_filename: str = Header(default="inspection-image"),
    manager: AgentRunManager = Depends(get_agent_run_manager),
):
    try:
        record = manager.upload_run_image(
            run_id,
            content=await _read_image_body(request),
            mime_type=request.headers.get("content-type", ""),
            filename=x_filename,
            description=description,
        )
        return _public_inspection_image(record)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc
    except (ValueError, InvalidRunStateError) as exc:
        raise APIError(409, "INVALID_IMAGE_UPLOAD_STATE", str(exc)) from exc


@router.get(
    "/runs/{run_id}/inspection-images",
    response_model=RunInspectionImageList,
)
def get_run_inspection_images(
    run_id: str, manager: AgentRunManager = Depends(get_agent_run_manager)
):
    try:
        images = [
            PublicInspectionImageResult(
                image=_public_inspection_image(item["image"]),
                observation=item.get("observation"),
            )
            for item in manager.get_images(run_id)
        ]
        return RunInspectionImageList(run_id=run_id, images=images)
    except RunNotFoundError as exc:
        raise _not_found(run_id) from exc


@router.get("/inspection-images/{image_id}/observations")
def get_visual_observation(
    image_id: str, manager: AgentRunManager = Depends(get_agent_run_manager)
):
    try:
        return manager.get_visual_observation(image_id)
    except KeyError as exc:
        raise APIError(404, "VISUAL_OBSERVATION_NOT_FOUND", "Visual observation was not found.") from exc


@router.get("/inspection-images/{image_id}", response_class=FileResponse)
def get_inspection_image_file(
    image_id: str, manager: AgentRunManager = Depends(get_agent_run_manager)
):
    try:
        record = manager.get_image_record(image_id)
    except KeyError as exc:
        raise APIError(404, "INSPECTION_IMAGE_NOT_FOUND", "Inspection image was not found.") from exc
    return FileResponse(
        record.file_ref,
        media_type=record.mime_type,
        filename=record.original_filename,
        content_disposition_type="inline",
    )
