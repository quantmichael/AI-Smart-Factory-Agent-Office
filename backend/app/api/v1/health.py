"""Service health endpoint."""

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.readiness import evaluate_readiness
from app.domain.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return liveness information without checking future dependencies."""

    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/ready")
def get_readiness(response: Response) -> dict:
    """Report whether required runtime dependencies are operational."""

    result = evaluate_readiness(get_settings())
    if result["status"] != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
