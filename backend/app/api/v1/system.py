"""Read-only, sanitized system status endpoint."""

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.system import SystemStatusService, SystemStatusView


router = APIRouter(prefix="/system", tags=["system"])


def get_system_status_service() -> SystemStatusService:
    return SystemStatusService(get_settings())


@router.get("/status", response_model=SystemStatusView)
def get_system_status(
    service: SystemStatusService = Depends(get_system_status_service),
) -> SystemStatusView:
    return service.inspect()
