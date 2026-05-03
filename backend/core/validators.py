"""
Input Validator — core/validators.py
=======================================
Centralized validation utilities for all incoming request data.

Raises HTTPException with a clear 422 error for invalid inputs.
"""

from fastapi import HTTPException
from core.logger import get_logger

log = get_logger(__name__)

# ── Coordinate bounds ────────────────────────────────────────────────────────
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0

# ── Chat message limits ──────────────────────────────────────────────────────
MSG_MIN_LEN = 2
MSG_MAX_LEN = 2000

# ── Image constraints ────────────────────────────────────────────────────────
MAX_IMAGE_BYTES = 15 * 1024 * 1024   # 15 MB hard cap
MIN_IMAGE_BYTES = 1_000              # 1 KB minimum
ALLOWED_MIME_PREFIXES = ("image/jpeg", "image/png", "image/webp",
                         "image/bmp", "image/gif", "image/")

# ── Pest report limits ───────────────────────────────────────────────────────
MAX_PEST_TYPE_LEN = 100


def validate_coordinates(lat: float, lon: float) -> None:
    """Validate that lat/lon are within valid geographic bounds."""
    if not (LAT_MIN <= lat <= LAT_MAX):
        log.warning(f"Invalid latitude received: {lat}")
        raise HTTPException(
            status_code=422,
            detail=f"❌ Invalid latitude {lat}. Must be between {LAT_MIN} and {LAT_MAX}.",
        )
    if not (LON_MIN <= lon <= LON_MAX):
        log.warning(f"Invalid longitude received: {lon}")
        raise HTTPException(
            status_code=422,
            detail=f"❌ Invalid longitude {lon}. Must be between {LON_MIN} and {LON_MAX}.",
        )


def validate_chat_message(message: str) -> str:
    """Sanitize and validate a chat message."""
    if not message or not message.strip():
        raise HTTPException(
            status_code=422,
            detail="❌ Message cannot be empty.",
        )
    stripped = message.strip()
    if len(stripped) < MSG_MIN_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"❌ Message too short. Minimum {MSG_MIN_LEN} characters.",
        )
    if len(stripped) > MSG_MAX_LEN:
        log.warning(f"Message truncated from {len(stripped)} → {MSG_MAX_LEN} chars")
        stripped = stripped[:MSG_MAX_LEN]
    return stripped


def validate_confidence(confidence: float | None) -> float | None:
    """Validate that confidence is a number between 0.0 and 1.0."""
    if confidence is None:
        return None
    if not (0.0 <= confidence <= 1.0):
        raise HTTPException(
            status_code=422,
            detail=f"❌ Confidence {confidence} is out of range. Must be 0.0–1.0.",
        )
    return confidence


def validate_pest_report(lat: float, lon: float, pest_type: str) -> str:
    """Validate a heatmap pest report submission."""
    validate_coordinates(lat, lon)
    if not pest_type or not pest_type.strip():
        raise HTTPException(
            status_code=422,
            detail="❌ pest_type cannot be empty.",
        )
    cleaned = pest_type.strip()[:MAX_PEST_TYPE_LEN]
    return cleaned


def validate_image_upload(content_type: str | None, file_size: int) -> None:
    """
    Validate an uploaded image by MIME type and file size.
    Call AFTER reading and saving the file (so we have the real size).
    """
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="❌ Invalid file type. Please upload an image file (JPEG, PNG, WEBP).",
        )
    if file_size < MIN_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"❌ Image file too small ({file_size} bytes). "
                "Please upload a clear photo of the pest (at least 1 KB)."
            ),
        )
    if file_size > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"❌ Image file too large ({file_size / 1024 / 1024:.1f} MB). "
                f"Maximum allowed size is {MAX_IMAGE_BYTES // 1024 // 1024} MB."
            ),
        )
