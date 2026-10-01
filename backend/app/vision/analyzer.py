"""Provider-neutral vision boundary with a conservative local quality observer."""

from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageFilter, ImageStat

from app.vision.schemas import ImageQuality, InspectionImageRecord, VisualObservation, VisualObservationItem


class VisionAnalyzer(Protocol):
    provider_id: str
    model_id: str

    def analyze(self, image: InspectionImageRecord) -> VisualObservation: ...


class LocalQualityVisionAnalyzer:
    """Measures directly visible image quality; it never invents equipment faults."""

    provider_id = "local"
    model_id = "pillow-quality-observer-v1"

    @staticmethod
    def _id(image_id: str, category: str) -> str:
        return "visual_" + hashlib.sha256(f"{image_id}:{category}".encode()).hexdigest()[:20]

    def analyze(self, image: InspectionImageRecord) -> VisualObservation:
        with Image.open(Path(image.file_ref)) as source:
            rgb = source.convert("RGB")
            gray = rgb.convert("L")
            brightness = float(ImageStat.Stat(gray).mean[0])
            contrast = float(ImageStat.Stat(gray).stddev[0])
            edge_variance = float(ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).var[0])
        limitations: list[str] = []
        if brightness < 28:
            limitations.append("dark: important exterior details may not be visible")
        if brightness > 238:
            limitations.append("overexposed: bright regions may hide exterior details")
        if contrast < 7 or edge_variance < 8:
            limitations.append("blur_or_low_contrast: fine exterior details cannot be assessed reliably")
        if min(image.width, image.height) < 160:
            limitations.append("low_resolution: only coarse visual review is possible")
        quality = ImageQuality.USABLE if not limitations else ImageQuality.LOW_QUALITY
        description = (
            f"Image quality is directly measurable at {image.width}×{image.height}; "
            f"mean brightness {brightness:.1f}, contrast {contrast:.1f}."
        )
        observations = [] if quality == ImageQuality.LOW_QUALITY else [
            VisualObservationItem(
                observation_id=self._id(image.image_id, "image_quality"),
                category="image_quality",
                description=description,
                confidence_level="high",
            )
        ]
        limitations.append(
            "The local observer evaluates image quality only; it does not identify internal bearing faults or confirm equipment safety."
        )
        return VisualObservation(
            image_id=image.image_id,
            provider=self.provider_id,
            model=self.model_id,
            observations=observations,
            visible_components=[],
            quality=quality,
            limitations=limitations,
            metrics={"brightness": brightness, "contrast": contrast, "edge_variance": edge_variance},
            created_at=datetime.now(UTC),
        )
