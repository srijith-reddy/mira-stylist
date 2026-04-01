"""
MIRA Stylist — Validation Service

Wraps image validation with premium, user-friendly feedback.
Enhances raw validation results with warm, actionable guidance so
the user always feels guided rather than blocked.
"""

from __future__ import annotations

from ..models.schemas import ImageValidationResult
from ..utils.image_utils import validate_person_image, validate_garment_image


class ValidationService:
    """Validates images for try-on with premium, user-friendly feedback."""

    PERSON_IMAGE_GUIDANCE: dict[str, str] = {
        "low_resolution": (
            "A slightly sharper photo will help us capture every detail "
            "beautifully. Try a well-lit, higher-resolution image."
        ),
        "bad_format": (
            "We work best with JPEG or PNG images. A quick format change "
            "should do the trick."
        ),
        "too_small": (
            "The photo needs a bit more detail for us to work our magic. "
            "Try one that's at least 512 pixels on each side."
        ),
        "too_large": (
            "This image is quite large — we'll work with it, but a "
            "moderately sized photo often gives the smoothest experience."
        ),
        "generic_error": (
            "We weren't able to read this image clearly. A front-facing "
            "photo on a clean background will give the most beautiful result."
        ),
    }

    GARMENT_IMAGE_GUIDANCE: dict[str, str] = {
        "low_resolution": (
            "A clearer garment photo will help us capture the fabric and "
            "drape more faithfully."
        ),
        "bad_format": (
            "We work best with JPEG or PNG images for garment photos."
        ),
        "too_small": (
            "The garment image needs a bit more detail. A larger, well-lit "
            "product photo will give us more to work with."
        ),
        "cluttered_background": (
            "Try a garment photo against a cleaner background — it helps "
            "us isolate the silhouette beautifully."
        ),
        "generic_error": (
            "We're not getting a clean enough garment read yet. Try a "
            "front-facing photo on a plain background so the drape and "
            "fit come through more beautifully."
        ),
    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _enhance_suggestions(
        result: ImageValidationResult,
        guidance: dict[str, str],
    ) -> ImageValidationResult:
        """Replace or augment raw suggestions with premium guidance.

        For each detected issue key that exists in *guidance*, the
        corresponding warm message is used instead of (or in addition to)
        the original suggestion.
        """
        enhanced: list[str] = []
        matched_keys: set[str] = set()

        for issue in result.issues:
            # Normalise the issue string to a lookup key
            key = issue.strip().lower().replace(" ", "_")
            if key in guidance:
                enhanced.append(guidance[key])
                matched_keys.add(key)
            else:
                # Fall back to the original issue text when no mapping exists
                enhanced.append(issue)

        # If no issues matched but the result is invalid, add generic guidance
        if not result.is_valid and not enhanced:
            enhanced.append(guidance.get("generic_error", ""))

        # Preserve any suggestions that came from the validator as-is,
        # then prepend our premium-language enhancements.
        combined = enhanced + [
            s for s in result.suggestions if s not in enhanced
        ]

        return ImageValidationResult(
            is_valid=result.is_valid,
            issues=result.issues,
            suggestions=combined if combined else result.suggestions,
            confidence=result.confidence,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def validate_person(
        self, image_path_or_url: str
    ) -> ImageValidationResult:
        """Validate a person image with premium feedback.

        The underlying validation is synchronous (Pillow-based); it is
        called directly and the result is enhanced with warm guidance.
        """
        result = validate_person_image(image_path_or_url)
        return self._enhance_suggestions(result, self.PERSON_IMAGE_GUIDANCE)

    async def validate_garment(
        self, image_path_or_url: str
    ) -> ImageValidationResult:
        """Validate a garment image with premium feedback."""
        result = validate_garment_image(image_path_or_url)
        return self._enhance_suggestions(result, self.GARMENT_IMAGE_GUIDANCE)

    async def validate_tryon_inputs(
        self, person_image: str, garment_image: str
    ) -> dict:
        """Validate both images for a try-on request.

        Returns a dict containing:
        - ``person``: :class:`ImageValidationResult` for the person image
        - ``garment``: :class:`ImageValidationResult` for the garment image
        - ``is_valid``: ``True`` only when *both* images pass validation
        - ``combined_suggestions``: merged list of suggestions from both
        """
        person_result = await self.validate_person(person_image)
        garment_result = await self.validate_garment(garment_image)

        return {
            "person": person_result,
            "garment": garment_result,
            "is_valid": person_result.is_valid and garment_result.is_valid,
            "combined_suggestions": (
                person_result.suggestions + garment_result.suggestions
            ),
        }
