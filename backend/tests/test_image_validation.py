import pytest

from app.vision import ImageValidationError, validate_image
from vision_helpers import image_bytes


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_allowed_formats_are_decoded_and_magic_checked(fmt, mime):
    result = validate_image(image_bytes(image_format=fmt), mime, max_size_bytes=1_000_000, max_dimension=1024)
    assert result.mime_type == mime
    assert (result.width, result.height) == (320, 240)


def test_rejects_mime_spoofing_and_non_image_bytes():
    with pytest.raises(ImageValidationError, match="MIME"):
        validate_image(image_bytes(), "image/jpeg", max_size_bytes=1_000_000, max_dimension=1024)
    with pytest.raises(ImageValidationError, match="signature"):
        validate_image(b"not-an-image", "image/png", max_size_bytes=1_000_000, max_dimension=1024)


def test_rejects_size_and_dimension_limits():
    content = image_bytes(size=(500, 500))
    with pytest.raises(ImageValidationError, match="size limit"):
        validate_image(content, "image/png", max_size_bytes=10, max_dimension=1024)
    with pytest.raises(ImageValidationError, match="dimensions"):
        validate_image(content, "image/png", max_size_bytes=1_000_000, max_dimension=256)
