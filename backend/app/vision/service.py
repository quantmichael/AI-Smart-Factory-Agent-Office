"""Secure file storage and resilient visual analysis orchestration."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.vision.analyzer import VisionAnalyzer
from app.vision.repository import InspectionImageRepository
from app.vision.schemas import ImageQuality, InspectionImageRecord, VisualObservation
from app.vision.validation import validate_image


class InspectionImageService:
    def __init__(self, repository: InspectionImageRepository, analyzer: VisionAnalyzer, upload_root: Path | str, *, max_size_mb: int = 8, max_dimension: int = 4096, enabled: bool = True) -> None:
        self.repository = repository
        self.analyzer = analyzer
        self.upload_root = Path(upload_root)
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_dimension = max_dimension
        self.enabled = enabled

    def store(self, *, equipment_id: str, content: bytes, mime_type: str, filename: str, description: str | None = None, run_id: str | None = None) -> InspectionImageRecord:
        validated = validate_image(content, mime_type, max_size_bytes=self.max_size_bytes, max_dimension=self.max_dimension)
        image_id = f"image_{uuid4().hex}"
        safe_original = Path(
            (filename or f"inspection{validated.extension}").replace("\\", "/")
        ).name[:200]
        file_path = (self.upload_root / f"{image_id}{validated.extension}").resolve()
        if self.upload_root.resolve() not in file_path.parents:
            raise ValueError("invalid upload path")
        file_path.write_bytes(content)
        record = InspectionImageRecord(
            image_id=image_id, run_id=run_id, equipment_id=equipment_id,
            file_ref=str(file_path), original_filename=safe_original,
            mime_type=validated.mime_type, size_bytes=validated.size_bytes,
            width=validated.width, height=validated.height,
            uploaded_at=datetime.now(UTC), description=description,
        )
        return self.repository.save_image(record)

    def attach(self, image_id: str, run_id: str, equipment_id: str) -> InspectionImageRecord:
        return self.repository.attach(image_id, run_id, equipment_id)

    def analyze(self, image_id: str) -> VisualObservation:
        cached = self.repository.get_observation(image_id)
        if cached:
            return cached
        image = self.repository.get_image(image_id)
        if image is None:
            raise KeyError(image_id)
        if not self.enabled:
            result = VisualObservation(
                image_id=image_id, provider="disabled", model="none", quality=ImageQuality.UNUSABLE,
                limitations=["Visual analysis is disabled by configuration."],
                analysis_error="VISION_DISABLED", created_at=datetime.now(UTC),
            )
        else:
            try:
                result = self.analyzer.analyze(image)
            except Exception as exc:
                result = VisualObservation(
                    image_id=image_id, provider=getattr(self.analyzer, "provider_id", "unknown"),
                    model=getattr(self.analyzer, "model_id", "unknown"), quality=ImageQuality.UNUSABLE,
                    limitations=["Visual analysis was unavailable; sensor and technical evidence workflow continued."],
                    analysis_error=type(exc).__name__, created_at=datetime.now(UTC),
                )
        return self.repository.save_observation(result)

    def list_for_run(self, run_id: str) -> list[dict]:
        return [
            {"image": image.model_dump(mode="json"), "observation": (self.repository.get_observation(image.image_id).model_dump(mode="json") if self.repository.get_observation(image.image_id) else None)}
            for image in self.repository.list_for_run(run_id)
        ]
