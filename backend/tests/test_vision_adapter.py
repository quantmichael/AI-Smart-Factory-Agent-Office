from app.vision import ImageQuality, InspectionImageRepository, InspectionImageService, LocalQualityVisionAnalyzer
from vision_helpers import image_bytes


def test_local_adapter_only_reports_direct_quality_metrics(tmp_path):
    service = InspectionImageService(InspectionImageRepository(tmp_path / "db.sqlite3"), LocalQualityVisionAnalyzer(), tmp_path / "uploads")
    image = service.store(equipment_id="rig-a", content=image_bytes(color=(120, 120, 120)), mime_type="image/png", filename="../safe.png")
    result = service.analyze(image.image_id)
    assert result.provider == "local"
    assert result.visible_components == []
    assert "internal bearing faults" in " ".join(result.limitations)
    assert service.repository.get_image(image.image_id).original_filename == "safe.png"


def test_dark_low_quality_image_has_limitations_without_fabricated_observation(tmp_path):
    service = InspectionImageService(InspectionImageRepository(tmp_path / "db.sqlite3"), LocalQualityVisionAnalyzer(), tmp_path / "uploads")
    image = service.store(equipment_id="rig-a", content=image_bytes(color=(2, 2, 2)), mime_type="image/png", filename="dark.png")
    result = service.analyze(image.image_id)
    assert result.quality == ImageQuality.LOW_QUALITY
    assert result.observations == []
    assert any("dark" in item for item in result.limitations)
