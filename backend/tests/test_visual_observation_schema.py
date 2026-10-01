from datetime import UTC, datetime

import pytest

from app.vision import ImageQuality, VisualObservation, VisualObservationItem


def test_visual_observation_is_structured_and_timezone_aware():
    result = VisualObservation(
        image_id="image-1", provider="test", model="test-v1", quality=ImageQuality.USABLE,
        observations=[VisualObservationItem(observation_id="visual-1", category="surface_condition", description="Visible exterior mark.", confidence_level="medium")],
        limitations=["No internal condition claim."], created_at=datetime.now(UTC),
    )
    assert result.quality == ImageQuality.USABLE
    invalid = result.model_dump()
    invalid["created_at"] = datetime.now()
    with pytest.raises(ValueError, match="timezone-aware"):
        VisualObservation.model_validate(invalid)
