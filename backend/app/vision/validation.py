"""Content-based inspection image validation."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError


class ImageValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidatedImage:
    mime_type: str
    extension: str
    width: int
    height: int
    size_bytes: int


_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


def _magic_format(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "WEBP"
    return None


def validate_image(
    content: bytes,
    declared_mime: str,
    *,
    max_size_bytes: int,
    max_dimension: int,
) -> ValidatedImage:
    if not content:
        raise ImageValidationError("image file is empty")
    if len(content) > max_size_bytes:
        raise ImageValidationError("image exceeds configured size limit")
    magic_format = _magic_format(content)
    if magic_format not in _FORMATS:
        raise ImageValidationError("unsupported image signature")
    expected_mime, extension = _FORMATS[magic_format]
    normalized_mime = declared_mime.split(";", 1)[0].strip().lower()
    if normalized_mime != expected_mime:
        raise ImageValidationError("declared MIME type does not match image content")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            decoded_format = image.format
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError("image could not be decoded safely") from exc
    if decoded_format != magic_format:
        raise ImageValidationError("decoded format does not match image signature")
    if width < 16 or height < 16:
        raise ImageValidationError("image resolution is too small")
    if width > max_dimension or height > max_dimension:
        raise ImageValidationError("image dimensions exceed configured limit")
    return ValidatedImage(expected_mime, extension, width, height, len(content))
