from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from app.vision import (
    ImageQuality,
    InspectionImageRepository,
    InspectionImageService,
    VisualObservation,
    VisualObservationItem,
)


def image_bytes(*, color=(120, 130, 140), size=(320, 240), image_format="PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    return buffer.getvalue()


class ControlledVisionAnalyzer:
    provider_id = "test"
    model_id = "controlled-observer-v1"

    def analyze(self, image):
        return VisualObservation(
            image_id=image.image_id,
            provider=self.provider_id,
            model=self.model_id,
            quality=ImageQuality.USABLE,
            observations=[
                VisualObservationItem(
                    observation_id=f"visual_{image.image_id[-12:]}",
                    category="surface_condition",
                    description="A controlled test-only exterior surface mark is visible.",
                    confidence_level="medium",
                )
            ],
            limitations=["Controlled test observation; not a physical fault diagnosis."],
            created_at=datetime.now(UTC),
        )


class FailingVisionAnalyzer:
    provider_id = "test"
    model_id = "failing-observer-v1"

    def analyze(self, image):
        raise TimeoutError("controlled vision failure")


def build_vision_service(path, analyzer=None):
    return InspectionImageService(
        InspectionImageRepository(path / "vision.sqlite3"),
        analyzer or ControlledVisionAnalyzer(),
        path / "uploads",
    )
