"""
MIRA Stylist — Image Utilities

Helper functions for validating, downloading, encoding, and inspecting
images used in the virtual try-on pipeline.  All user-facing messages are
written in a warm, premium tone — never raw technical jargon.
"""

from __future__ import annotations

import base64
import binascii
import io
import os
import uuid
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

from ..models.schemas import ImageValidationResult

# ── Constants ────────────────────────────────────────────────────────────

MIN_DIMENSION = 512
MAX_DIMENSION = 8192
SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}
DOWNLOAD_TIMEOUT = 30.0  # seconds

# ── Premium-tone message helpers ─────────────────────────────────────────

_MSG_NOT_FOUND = (
    "We couldn't locate that image. Please double-check the file path or "
    "link and try again."
)
_MSG_UNREACHABLE = (
    "The image link doesn't seem to be reachable right now. "
    "Could you verify the URL or try uploading the photo directly?"
)
_MSG_UNSUPPORTED_FORMAT = (
    "This image format isn't supported just yet. For the best results, "
    "please use a JPEG, PNG, or WebP photo."
)
_MSG_TOO_SMALL = (
    "The image quality isn't quite high enough for a beautiful result. "
    "A clearer, higher-resolution photo will help us capture every detail."
)
_MSG_TOO_LARGE = (
    "This image is extremely large and may slow things down. "
    "For the smoothest experience, try a photo under 8 192 pixels on each side."
)
_MSG_CORRUPT = (
    "Something seems off with this image file — it may be damaged or "
    "incomplete. Please try a different photo."
)
_MSG_PERSON_GUIDANCE = (
    "For the most realistic try-on, use a well-lit photo where the full "
    "upper body (or full body) is clearly visible against a simple background."
)
_MSG_GARMENT_GUIDANCE = (
    "For the best garment result, use a clean product shot on a plain "
    "background — flat-lay or mannequin photos work wonderfully."
)


# ── Internal helpers ─────────────────────────────────────────────────────

def _is_url(value: str) -> bool:
    """Return True if *value* looks like an HTTP(S) URL."""
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def _is_data_url(value: str) -> bool:
    """Return True if *value* looks like a base64-encoded image data URL."""
    return value.startswith("data:image/")


def _build_result(
    *,
    is_valid: bool,
    issues: list[str] | None = None,
    suggestions: list[str] | None = None,
    confidence: float = 0.9,
) -> ImageValidationResult:
    """Create a normalized validation result."""
    return ImageValidationResult(
        is_valid=is_valid,
        issues=issues or [],
        suggestions=suggestions or [],
        confidence=confidence,
    )


def _validate_image(
    image_path_or_url: str,
    *,
    context: str = "image",
) -> ImageValidationResult:
    """Core validation logic shared by person and garment validators.

    Parameters
    ----------
    image_path_or_url:
        A local file path **or** an HTTP(S) URL pointing to the image.
    context:
        Either ``"person"`` or ``"garment"`` — used to tailor guidance.
    """
    is_url = _is_url(image_path_or_url)
    is_data_url = _is_data_url(image_path_or_url)
    local_path: str | None = None
    img: Image.Image | None = None

    # ── Reachability check ───────────────────────────────────────────
    if is_url:
        try:
            with httpx.Client(timeout=DOWNLOAD_TIMEOUT) as client:
                response = client.head(image_path_or_url, follow_redirects=True)
                if response.status_code >= 400:
                    return _build_result(
                        is_valid=False,
                        issues=["generic_error"],
                        suggestions=[_MSG_UNREACHABLE],
                        confidence=0.98,
                    )
        except httpx.HTTPError:
            return _build_result(
                is_valid=False,
                issues=["generic_error"],
                suggestions=[_MSG_UNREACHABLE],
                confidence=0.98,
            )

        # Download to a temporary location so we can inspect with Pillow.
        try:
            local_path = download_image(
                image_path_or_url,
                save_dir=os.path.join("output", "mira_stylist", ".tmp"),
            )
        except Exception:
            return _build_result(
                is_valid=False,
                issues=["generic_error"],
                suggestions=[_MSG_UNREACHABLE],
                confidence=0.98,
            )
    elif is_data_url:
        try:
            header, encoded = image_path_or_url.split(",", 1)
            if ";base64" not in header:
                raise ValueError("Unsupported data URL encoding")
            decoded = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(decoded))
        except (ValueError, binascii.Error):
            return _build_result(
                is_valid=False,
                issues=["generic_error"],
                suggestions=[_MSG_CORRUPT],
                confidence=0.95,
            )
    else:
        if not os.path.isfile(image_path_or_url):
            return _build_result(
                is_valid=False,
                issues=["generic_error"],
                suggestions=[_MSG_NOT_FOUND],
                confidence=0.98,
            )
        local_path = image_path_or_url

    # ── Open & inspect ───────────────────────────────────────────────
    try:
        if img is None:
            img = Image.open(local_path)
        img.verify()  # lightweight integrity check
        if local_path is not None:
            img = Image.open(local_path)
        else:
            header, encoded = image_path_or_url.split(",", 1)
            decoded = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(decoded))
    except Exception:
        return _build_result(
            is_valid=False,
            issues=["generic_error"],
            suggestions=[_MSG_CORRUPT],
            confidence=0.95,
        )

    # Format check
    fmt = (img.format or "").upper()
    if fmt not in SUPPORTED_FORMATS:
        return _build_result(
            is_valid=False,
            issues=["bad_format"],
            suggestions=[_MSG_UNSUPPORTED_FORMAT],
            confidence=0.97,
        )

    # Dimension checks
    width, height = img.size
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        return _build_result(
            is_valid=False,
            issues=["too_small"],
            suggestions=[_MSG_TOO_SMALL],
            confidence=0.99,
        )
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        return _build_result(
            is_valid=False,
            issues=["too_large"],
            suggestions=[_MSG_TOO_LARGE],
            confidence=0.92,
        )

    # ── All good ─────────────────────────────────────────────────────
    guidance = _MSG_PERSON_GUIDANCE if context == "person" else _MSG_GARMENT_GUIDANCE
    return _build_result(
        is_valid=True,
        suggestions=[guidance],
        confidence=0.95,
    )


# ── Public API ───────────────────────────────────────────────────────────

def validate_person_image(image_path_or_url: str) -> ImageValidationResult:
    """Validate that an image is suitable as the *person* input for virtual
    try-on.

    Checks file existence / URL reachability, image integrity, supported
    format, and minimum resolution.
    """
    return _validate_image(image_path_or_url, context="person")


def validate_garment_image(image_path_or_url: str) -> ImageValidationResult:
    """Validate that an image is suitable as the *garment* input for virtual
    try-on.

    Checks file existence / URL reachability, image integrity, supported
    format, and minimum resolution.
    """
    return _validate_image(image_path_or_url, context="garment")


def download_image(url: str, save_dir: str) -> str:
    """Download an image from *url* and persist it under *save_dir*.

    Returns the absolute path to the saved file.  The file is given a
    unique name to avoid collisions.
    """
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()

    # Derive a sensible extension from the Content-Type or URL.
    content_type = response.headers.get("content-type", "")
    if "png" in content_type:
        ext = ".png"
    elif "webp" in content_type:
        ext = ".webp"
    elif "jpeg" in content_type or "jpg" in content_type:
        ext = ".jpg"
    else:
        # Fall back to the URL's extension.
        url_path = urlparse(url).path
        ext = Path(url_path).suffix or ".jpg"

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = save_path / filename
    dest.write_bytes(response.content)
    return str(dest.resolve())


def encode_image_base64(image_path: str) -> str:
    """Read a local image file and return its contents as a Base64 string."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(
            "We couldn't find that image on disk. "
            "Please check the path and try again."
        )
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Return the ``(width, height)`` of a local image file."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(
            "We couldn't find that image on disk. "
            "Please check the path and try again."
        )
    with Image.open(path) as img:
        return img.size
