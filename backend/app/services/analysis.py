"""Application layer joining measurement lookup, model registry, and inference."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from time import perf_counter
from uuid import uuid4

from app.data.adapters.base import SensorDatasetAdapter
from app.domain.schemas import AnalysisResult
from app.ml.inference import InvalidFeatureError, MLInferenceService
from app.ml.registry import ArtifactModelRegistry, ModelRegistryEntry


logger = logging.getLogger(__name__)


class FeatureExtractionError(RuntimeError):
    pass


class AnalysisApplicationService:
    def __init__(
        self,
        adapter: SensorDatasetAdapter,
        registry: ArtifactModelRegistry,
    ) -> None:
        self.adapter = adapter
        self.registry = registry
        self._model_cache: dict[str, MLInferenceService] = {}
        self._model_cache_lock = Lock()

    @property
    def cached_model_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._model_cache))

    def _entry(self, model_id: str | None) -> ModelRegistryEntry:
        return self.registry.get_model(model_id) if model_id else self.registry.get_active_model()

    def _inference_service(self, entry: ModelRegistryEntry) -> MLInferenceService:
        cached = self._model_cache.get(entry.model_id)
        if cached is not None:
            return cached
        with self._model_cache_lock:
            cached = self._model_cache.get(entry.model_id)
            if cached is None:
                cached = MLInferenceService.from_artifact(
                    self.adapter, entry.artifact_directory
                )
                self._model_cache[entry.model_id] = cached
        return cached

    def analyze(self, measurement_id: str, model_id: str | None = None) -> AnalysisResult:
        analysis_id = f"analysis_{uuid4().hex}"
        started = perf_counter()
        selected_model = model_id or self.registry.active_model_id or "unresolved"
        try:
            self.adapter.get_metadata(measurement_id)
            entry = self._entry(model_id)
            selected_model = entry.model_id
            service = self._inference_service(entry)
            result = service.analyze(measurement_id, analysis_id=analysis_id)
        except InvalidFeatureError:
            logger.exception(
                "analysis failed analysis_id=%s measurement_id=%s model_id=%s error=feature_mismatch",
                analysis_id,
                measurement_id,
                selected_model,
            )
            raise
        except ValueError as exc:
            logger.exception(
                "analysis failed analysis_id=%s measurement_id=%s model_id=%s error=feature_extraction",
                analysis_id,
                measurement_id,
                selected_model,
            )
            raise FeatureExtractionError("feature extraction failed") from exc
        except Exception as exc:
            logger.warning(
                "analysis failed analysis_id=%s measurement_id=%s model_id=%s error=%s",
                analysis_id,
                measurement_id,
                selected_model,
                type(exc).__name__,
            )
            raise
        logger.info(
            "analysis completed analysis_id=%s measurement_id=%s model_id=%s duration_ms=%.3f status=%s",
            analysis_id,
            measurement_id,
            selected_model,
            (perf_counter() - started) * 1000.0,
            result.status.value,
        )
        return result


def build_analysis_service(
    dataset_root: Path,
    artifact_root: Path,
    active_model_id: str,
    adapter_factory,
) -> AnalysisApplicationService:
    return AnalysisApplicationService(
        adapter=adapter_factory(dataset_root),
        registry=ArtifactModelRegistry(artifact_root, active_model_id=active_model_id),
    )
