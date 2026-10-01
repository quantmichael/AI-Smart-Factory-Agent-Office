"""Read-only model transparency API."""

from fastapi import APIRouter, Depends

from app.api.exceptions import APIError
from app.core.config import get_settings, resolve_runtime_path
from app.ml.catalog import (
    CurrentModelView,
    ModelArtifactInvalidError,
    ModelArtifactMissingError,
    ModelCatalogService,
)


router = APIRouter(prefix="/models", tags=["models"])


def get_model_catalog_service() -> ModelCatalogService:
    settings = get_settings()
    return ModelCatalogService(
        resolve_runtime_path(settings.ml_artifact_root),
        settings.active_ml_model_id,
    )


@router.get("/current", response_model=CurrentModelView)
def get_current_model(
    service: ModelCatalogService = Depends(get_model_catalog_service),
) -> CurrentModelView:
    try:
        return service.current()
    except ModelArtifactMissingError as exc:
        raise APIError(
            404,
            "MODEL_ARTIFACT_NOT_FOUND",
            "현재 AI 모델 정보를 찾을 수 없습니다.",
        ) from exc
    except ModelArtifactInvalidError as exc:
        raise APIError(
            503,
            "MODEL_ARTIFACT_INVALID",
            "저장된 AI 모델 정보를 읽을 수 없습니다.",
        ) from exc
