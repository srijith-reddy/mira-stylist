"""
MIRA Stylist -- Sizing Recommendation Service

Generates elegant, confidence-aware size recommendations using user
measurements, brand history, garment metadata, and standard size charts.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ..models.schemas import (
    GarmentCategory,
    SizeChart,
    SizeEntry,
    SizeQuery,
    SizeRecommendation,
    UserProfile,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Size reference data (cm)
# ---------------------------------------------------------------------------

# Ordered list of standard labels for iteration/neighbour lookups.
_SIZE_ORDER: list[str] = ["XS", "S", "M", "L", "XL"]


def _cm(lower: float, upper: float) -> tuple[float, float]:
    """Return a size interval already expressed in centimeters."""
    return (float(lower), float(upper))


def _cm_exact(value: float) -> tuple[float, float]:
    """Return an exact size point in centimeters."""
    value = float(value)
    return (value, value)


def _in(lower: float, upper: float) -> tuple[float, float]:
    """Convert an inch interval from an official chart into centimeters."""
    return (round(lower * 2.54, 1), round(upper * 2.54, 1))


def _in_exact(value: float) -> tuple[float, float]:
    """Convert an exact inch value from an official chart into centimeters."""
    value_cm = round(value * 2.54, 1)
    return (value_cm, value_cm)


def _normalize_brand_name(value: str) -> str:
    """Normalize brand names for tolerant lookups."""
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


class SizingService:
    """Recommends garment sizes based on user profile, measurements,
    brand history, and garment metadata."""

    # Standard unisex/women's size chart (bust, waist, hips in cm).
    # Each range is (inclusive_lower, exclusive_upper).
    STANDARD_SIZES: dict[str, dict[str, tuple[float, float]]] = {
        "XS": {"bust": (78, 82), "waist": (60, 64), "hips": (86, 90)},
        "S":  {"bust": (82, 86), "waist": (64, 68), "hips": (90, 94)},
        "M":  {"bust": (86, 92), "waist": (68, 74), "hips": (94, 100)},
        "L":  {"bust": (92, 98), "waist": (74, 80), "hips": (100, 106)},
        "XL": {"bust": (98, 104), "waist": (80, 86), "hips": (106, 112)},
    }

    # Category-specific key measurements used for sizing decisions.
    _PRIMARY_MEASUREMENT: dict[GarmentCategory, str] = {
        GarmentCategory.TOPS: "bust",
        GarmentCategory.OUTERWEAR: "bust",
        GarmentCategory.DRESSES: "bust",
        GarmentCategory.BOTTOMS: "hips",
    }

    # Known brand-specific charts verified from official brand size guides on
    # 2026-03-31. We only store source-backed values here and leave gaps empty
    # rather than inferring them.
    _BRAND_CHARTS: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
        "Nike": {
            "XS": {"bust": _cm(76, 83), "waist": _cm(60, 67), "hips": _cm(84, 91)},
            "S": {"bust": _cm(83, 90), "waist": _cm(67, 74), "hips": _cm(91, 98)},
            "M": {"bust": _cm(90, 97), "waist": _cm(74, 81), "hips": _cm(98, 105)},
            "L": {"bust": _cm(97, 104), "waist": _cm(81, 88), "hips": _cm(105, 112)},
            "XL": {"bust": _cm(104, 114), "waist": _cm(88, 98), "hips": _cm(112, 120)},
        },
        "adidas": {
            "XS": {"bust": _cm(77, 82), "waist": _cm(61, 66), "hips": _cm(86, 91)},
            "S": {"bust": _cm(83, 88), "waist": _cm(67, 72), "hips": _cm(92, 97)},
            "M": {"bust": _cm(89, 94), "waist": _cm(73, 78), "hips": _cm(98, 103)},
            "L": {"bust": _cm(95, 101), "waist": _cm(79, 85), "hips": _cm(104, 110)},
            "XL": {"bust": _cm(102, 109), "waist": _cm(86, 94), "hips": _cm(111, 117)},
        },
        "Levi's": {
            "XS": {"bust": _in_exact(33), "waist": _in_exact(26.25), "hips": _in_exact(36)},
            "S": {"bust": _in_exact(35), "waist": _in_exact(28.25), "hips": _in_exact(38)},
            "M": {"bust": _in_exact(37), "waist": _in_exact(30.25), "hips": _in_exact(40)},
            "L": {"bust": _in_exact(39.5), "waist": _in_exact(32.75), "hips": _in_exact(42.5)},
            "XL": {"bust": _in_exact(42.5), "waist": _in_exact(35.75), "hips": _in_exact(45.5)},
        },
        "Mango": {
            "XS": {"bust": _cm_exact(82), "waist": _cm_exact(62), "hips": _cm_exact(90)},
            "S": {"bust": _cm_exact(86), "waist": _cm_exact(66), "hips": _cm_exact(94)},
            "M": {"bust": _cm_exact(92), "waist": _cm_exact(72), "hips": _cm_exact(100)},
            "L": {"bust": _cm_exact(98), "waist": _cm_exact(78), "hips": _cm_exact(106)},
            "XL": {"bust": _cm_exact(104), "waist": _cm_exact(85), "hips": _cm_exact(112)},
        },
        "Banana Republic": {
            "XS": {"bust": _in(32.5, 33.5), "waist": _in(26, 27), "hips": _in(35.5, 36.5)},
            "S": {"bust": _in(34.5, 35.5), "waist": _in(28, 29), "hips": _in(37.5, 38.5)},
            "M": {"bust": _in(36.5, 37.5), "waist": _in(30, 31), "hips": _in(39.5, 40.5)},
            "L": {"bust": _in(39, 40.5), "waist": _in(32.5, 34), "hips": _in(42, 43.5)},
            "XL": {"bust": _in(42.5, 44.5), "waist": _in(36, 38), "hips": _in(45.5, 47.5)},
        },
        "Gap": {
            "XS": {"bust": _in(32.25, 33.25), "waist": _in(25.5, 26.5), "hips": _in(35.25, 36.25)},
            "S": {"bust": _in(34.25, 35.25), "waist": _in(27.5, 28.5), "hips": _in(37.25, 38.25)},
            "M": {"bust": _in(36.25, 37.25), "waist": _in(29.5, 30.5), "hips": _in(39.25, 40.25)},
            "L": {"bust": _in(38.75, 40.25), "waist": _in(32, 33.5), "hips": _in(41.75, 43.25)},
            "XL": {"bust": _in(42, 43.75), "waist": _in(35.5, 37.5), "hips": _in(45.25, 47.25)},
        },
        "Athleta": {
            "XS": {"bust": _in(32.5, 33.5), "waist": _in(25.25, 26.25), "hips": _in(35, 36)},
            "S": {"bust": _in(34.5, 35.5), "waist": _in(27.25, 28.25), "hips": _in(37, 38)},
            "M": {"bust": _in(36.5, 37.5), "waist": _in(29.25, 30.25), "hips": _in(39, 40)},
            "L": {"bust": _in(39, 40.5), "waist": _in(31.75, 33.25), "hips": _in(41.5, 43)},
            "XL": {"bust": _in_exact(42), "waist": _in_exact(34.25), "hips": _in_exact(44.5)},
        },
        "Aritzia": {
            "XS": {"bust": _cm(81.5, 84), "waist": _cm(61, 63.5), "hips": _cm(86.5, 89)},
            "S": {"bust": _cm(86.5, 89), "waist": _cm(66, 68.5), "hips": _cm(91.5, 94)},
            "M": {"bust": _cm(91.5, 94), "waist": _cm(71, 73.5), "hips": _cm(96.5, 99)},
            "L": {"bust": _cm(97.5, 101), "waist": _cm(77, 80.5), "hips": _cm(102.5, 106)},
            "XL": {"bust": _cm(103, 106.5), "waist": _cm(85, 89), "hips": _cm(108, 112)},
        },
        "Urban Outfitters": {
            "XS": {"bust": _cm_exact(82), "waist": _cm_exact(63), "hips": _cm_exact(86.5)},
            "S": {"bust": _cm_exact(87), "waist": _cm_exact(68), "hips": _cm_exact(91.5)},
            "M": {"bust": _cm_exact(92), "waist": _cm_exact(73), "hips": _cm_exact(96.5)},
            "L": {"bust": _cm_exact(97), "waist": _cm_exact(78), "hips": _cm_exact(101.5)},
            "XL": {"bust": _cm_exact(102), "waist": _cm_exact(83), "hips": _cm_exact(106.5)},
        },
        "Anthropologie": {
            "XS": {"bust": _in(33, 34), "waist": _in(25, 26), "hips": _in(35, 36)},
            "S": {"bust": _in(35, 36), "waist": _in(27, 28), "hips": _in(37, 38)},
            "M": {"bust": _in(37, 38), "waist": _in(29, 30), "hips": _in(39, 40)},
            "L": {"bust": _in(39, 41), "waist": _in(31, 33), "hips": _in(41, 43)},
            "XL": {"bust": _in(42, 42.5), "waist": _in(34.5, 34.5), "hips": _in(44, 44.5)},
        },
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def recommend_size(
        self,
        query: SizeQuery,
        user_profile: UserProfile,
    ) -> SizeRecommendation:
        """Generate a size recommendation based on profile + query.

        Decision hierarchy:
        1. Brand-specific size history in the user profile  -> high confidence.
        2. Body measurements matched against a size chart    -> moderate-high.
        3. Typical size range from the user profile          -> lower confidence.
        4. Adjustments for silhouette intent and fabric stretch.
        """
        brand = query.brand
        category = query.garment_category
        saved_brand_size = self._lookup_profile_brand_history(user_profile, brand)
        has_brand_history = bool(saved_brand_size)
        has_measurements = bool(
            user_profile.measurements
            and self._PRIMARY_MEASUREMENT.get(category) in (user_profile.measurements or {})
        )
        has_stretch_info = query.fabric_stretch is not None

        # --- 1. Brand-specific history ---------------------------------
        if has_brand_history:
            assert saved_brand_size is not None
            recommended = saved_brand_size
            confidence = self._calculate_confidence(
                has_measurements=has_measurements,
                has_brand_history=True,
                has_stretch_info=has_stretch_info,
            )
            alternate = self._adjacent_size(recommended, direction="up")
            reason = self._generate_reason(recommended, confidence, user_profile, query)
            fit_intent = self._generate_fit_intent(category, query.silhouette_intent, user_profile)
            tailoring = self._tailoring_note(category, query.silhouette_intent)

            return SizeRecommendation(
                recommended_size=recommended,
                confidence=round(confidence, 2),
                reason_summary=reason,
                fit_intent_summary=fit_intent,
                alternate_size=alternate,
                tailoring_note=tailoring,
                garment_category=category,
                brand=brand,
            )

        # --- 2. Measurements ------------------------------------------
        if has_measurements:
            assert user_profile.measurements is not None
            recommended, between = self._match_measurements(
                user_profile.measurements, category, brand
            )
            confidence = self._calculate_confidence(
                has_measurements=True,
                has_brand_history=False,
                has_stretch_info=has_stretch_info,
            )
            # Adjust for silhouette intent
            recommended = self._adjust_for_intent(
                recommended, query.silhouette_intent, query.fabric_stretch
            )
            alternate = self._adjacent_size(recommended, direction="up") if between else None
            reason = self._generate_reason(recommended, confidence, user_profile, query)
            fit_intent = self._generate_fit_intent(category, query.silhouette_intent, user_profile)
            tailoring = self._tailoring_note(category, query.silhouette_intent)

            return SizeRecommendation(
                recommended_size=recommended,
                confidence=round(confidence, 2),
                reason_summary=reason,
                fit_intent_summary=fit_intent,
                alternate_size=alternate,
                tailoring_note=tailoring,
                garment_category=category,
                brand=brand,
            )

        # --- 3. Typical size range fallback ----------------------------
        recommended = self._best_guess_from_ranges(user_profile)
        confidence = self._calculate_confidence(
            has_measurements=False,
            has_brand_history=False,
            has_stretch_info=has_stretch_info,
        )
        recommended = self._adjust_for_intent(
            recommended, query.silhouette_intent, query.fabric_stretch
        )
        alternate = self._adjacent_size(recommended, direction="up")
        reason = self._generate_reason(recommended, confidence, user_profile, query)
        fit_intent = self._generate_fit_intent(category, query.silhouette_intent, user_profile)
        tailoring = self._tailoring_note(category, query.silhouette_intent)

        return SizeRecommendation(
            recommended_size=recommended,
            confidence=round(confidence, 2),
            reason_summary=reason,
            fit_intent_summary=fit_intent,
            alternate_size=alternate,
            tailoring_note=tailoring,
            garment_category=category,
            brand=brand,
        )

    async def get_size_chart(
        self,
        brand: str | None = None,
        category: str | None = None,
    ) -> SizeChart:
        """Return a size chart.  Uses stored brand charts or generic fallback."""
        chart_data = self.STANDARD_SIZES
        resolved_brand = brand or "Generic"

        key = self._resolve_brand_key(brand)
        if key:
            chart_data = self._BRAND_CHARTS[key]
            resolved_brand = key

        # Resolve category enum (default to DRESSES if not provided)
        try:
            cat_enum = GarmentCategory(category) if category else GarmentCategory.DRESSES
        except ValueError:
            cat_enum = GarmentCategory.DRESSES

        entries: list[SizeEntry] = []
        for label in _SIZE_ORDER:
            if label in chart_data:
                measurements = {
                    k: lo if lo == hi else round((lo + hi) / 2, 1)
                    for k, (lo, hi) in chart_data[label].items()
                }
                entries.append(SizeEntry(size_label=label, measurements=measurements))

        return SizeChart(
            brand=resolved_brand,
            garment_category=cat_enum,
            sizes=entries,
        )

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_confidence(
        has_measurements: bool,
        has_brand_history: bool,
        has_stretch_info: bool,
    ) -> float:
        """Calculate confidence score for a recommendation.

        Scoring:
        - Base                 : 0.30
        - Body measurements    : +0.25
        - Brand size history   : +0.25
        - Fabric stretch info  : +0.10
        - Category match (impl): +0.10 (always awarded when we reach here)
        """
        score = 0.30
        if has_measurements:
            score += 0.25
        if has_brand_history:
            score += 0.25
        if has_stretch_info:
            score += 0.10
        # Category match bonus -- we always have category context in practice
        score += 0.10
        return min(score, 1.0)

    # ------------------------------------------------------------------
    # Measurement matching
    # ------------------------------------------------------------------

    def _match_measurements(
        self,
        measurements: dict[str, float | int],
        category: GarmentCategory,
        brand: str | None = None,
    ) -> tuple[str, bool]:
        """Find the best size label for the given measurements.

        Returns (size_label, is_between_sizes).
        """
        chart = self.STANDARD_SIZES
        brand_key = self._resolve_brand_key(brand)
        if brand_key:
            chart = self._BRAND_CHARTS[brand_key]

        primary_key = self._PRIMARY_MEASUREMENT.get(category, "bust")
        value = float(measurements.get(primary_key, measurements.get("bust", 88)))

        best_label = "M"
        best_distance = float("inf")
        between = False

        for label in _SIZE_ORDER:
            if label not in chart or primary_key not in chart[label]:
                continue
            lo, hi = chart[label][primary_key]
            midpoint = lo if lo == hi else (lo + hi) / 2
            distance = abs(value - midpoint)
            if distance < best_distance:
                best_distance = distance
                best_label = label
                if lo == hi:
                    between = False
                else:
                    # If the value is near the boundary of two sizes, flag it.
                    between = not (lo <= value < hi)

        return best_label, between

    def _resolve_brand_key(self, brand: str | None) -> str | None:
        """Resolve a user-provided brand name against stored chart keys."""
        if not brand:
            return None
        target = _normalize_brand_name(brand)
        for key in self._BRAND_CHARTS:
            if _normalize_brand_name(key) == target:
                return key
        return None

    def _lookup_profile_brand_history(
        self,
        profile: UserProfile,
        brand: str | None,
    ) -> str | None:
        """Find a saved brand size even when punctuation/casing differs."""
        if not brand:
            return None
        target = _normalize_brand_name(brand)
        for saved_brand, saved_size in profile.approximate_size_history.items():
            if _normalize_brand_name(saved_brand) == target:
                return saved_size
        return None

    # ------------------------------------------------------------------
    # Size adjustment helpers
    # ------------------------------------------------------------------

    def _adjust_for_intent(
        self,
        size: str,
        silhouette_intent: str | None,
        fabric_stretch: bool | None,
    ) -> str:
        """Shift size up or down based on silhouette intent and stretch."""
        if not silhouette_intent:
            return size

        intent_lower = silhouette_intent.lower()

        # Size-up intents
        if any(kw in intent_lower for kw in ("oversized", "relaxed", "loose", "boxy")):
            shifted = self._adjacent_size(size, direction="up")
            if shifted:
                return shifted

        # Size-down intents (only if fabric has stretch)
        if any(kw in intent_lower for kw in ("fitted", "bodycon", "slim", "tailored")):
            if fabric_stretch:
                shifted = self._adjacent_size(size, direction="down")
                if shifted:
                    return shifted

        return size

    @staticmethod
    def _adjacent_size(size: str, direction: str = "up") -> Optional[str]:
        """Return the next size up or down, or None if at boundary."""
        try:
            idx = _SIZE_ORDER.index(size)
        except ValueError:
            return None

        if direction == "up" and idx < len(_SIZE_ORDER) - 1:
            return _SIZE_ORDER[idx + 1]
        if direction == "down" and idx > 0:
            return _SIZE_ORDER[idx - 1]
        return None

    @staticmethod
    def _best_guess_from_ranges(profile: UserProfile) -> str:
        """Derive a best-guess size from the user's typical_size_ranges."""
        if not profile.typical_size_ranges:
            return "M"  # sensible default

        # Look for known labels in the user's ranges
        for label in _SIZE_ORDER:
            for entry in profile.typical_size_ranges:
                if label.lower() == entry.strip().lower():
                    return label

        # If ranges contain numeric US sizes, map roughly
        _US_MAP: dict[str, str] = {
            "0": "XS", "2": "XS",
            "4": "S", "6": "S",
            "8": "M", "10": "M",
            "12": "L", "14": "L",
            "16": "XL", "18": "XL",
        }
        for entry in profile.typical_size_ranges:
            cleaned = entry.strip().upper().replace("US ", "").replace("US", "")
            if cleaned in _US_MAP:
                return _US_MAP[cleaned]

        # Last resort -- return the first range entry if it looks like a size
        first = profile.typical_size_ranges[0].strip().upper()
        if first in _SIZE_ORDER:
            return first
        return "M"

    # ------------------------------------------------------------------
    # Elegant narrative generation
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_reason(
        recommended: str,
        confidence: float,
        profile: UserProfile,
        query: SizeQuery,
    ) -> str:
        """Generate an elegant reason summary based on confidence tier."""
        brand_clause = f" with {query.brand}" if query.brand else ""
        intent_clause = ""
        if query.silhouette_intent:
            intent_clause = f" for a {query.silhouette_intent} silhouette"

        if confidence >= 0.75:
            # High confidence -- authoritative but warm
            return (
                f"Based on your measurements and experience{brand_clause}, "
                f"{recommended} should give you the clean, defined line you "
                f"prefer{intent_clause}.  This is a high-confidence match."
            )
        if confidence >= 0.55:
            # Moderate confidence -- assured but acknowledging limits
            return (
                f"Based on your usual size profile and the garment's likely "
                f"intended line, {recommended} should preserve the shape "
                f"without pulling too close{intent_clause}.  "
                f"We're fairly confident in this call{brand_clause}."
            )
        # Lower confidence -- transparent and helpful
        without_clause = (
            "the brand's exact cut notes"
            if not query.brand
            else f"more data on your fit{brand_clause}"
        )
        usual_range = (
            ", ".join(profile.typical_size_ranges)
            if profile.typical_size_ranges
            else recommended
        )
        return (
            f"We'd lean {recommended} here{intent_clause}, but confidence is "
            f"still limited without {without_clause}.  "
            f"Consider ordering your usual range ({usual_range}) "
            f"and checking the brand's own chart."
        )

    @staticmethod
    def _generate_fit_intent(
        category: GarmentCategory,
        silhouette_intent: str | None,
        profile: UserProfile,
    ) -> str:
        """Generate a fit-intent summary describing the intended wearing experience."""
        # Category-specific base descriptions
        _CATEGORY_DEFAULTS: dict[GarmentCategory, str] = {
            GarmentCategory.TOPS: "relaxed through the torso with clean shoulder alignment",
            GarmentCategory.BOTTOMS: "smooth through the hip with comfortable ease at the waist",
            GarmentCategory.DRESSES: "balanced proportions from shoulder to hem with natural drape",
            GarmentCategory.OUTERWEAR: "generous enough to layer comfortably without bulk",
        }

        base = _CATEGORY_DEFAULTS.get(category, "a balanced, comfortable fit")

        if silhouette_intent:
            intent = silhouette_intent.lower()
            if "oversized" in intent:
                return (
                    f"An intentionally generous silhouette -- {base}, "
                    f"with extra room for that relaxed, off-duty quality."
                )
            if "fitted" in intent or "tailored" in intent:
                return (
                    f"A more defined line -- {base}, "
                    f"sitting closer to the body for a polished, precise feel."
                )
            if "relaxed" in intent:
                return (
                    f"Easy and unhurried -- {base}, "
                    f"with just enough room that nothing pulls or clings."
                )
            # Generic intent
            return f"Aiming for a {silhouette_intent} feel -- {base}."

        # Incorporate user preferences if available
        if profile.preferred_silhouettes:
            prefs = ", ".join(profile.preferred_silhouettes[:2])
            return (
                f"Aligned with your preference for {prefs} shapes -- {base}."
            )

        return f"The intended fit reads as {base}."

    @staticmethod
    def _tailoring_note(
        category: GarmentCategory,
        silhouette_intent: str | None,
    ) -> Optional[str]:
        """Suggest tailoring for occasion or fitted garments."""
        fitted_intents = {"fitted", "tailored", "bodycon", "slim"}

        if silhouette_intent and silhouette_intent.lower() in fitted_intents:
            if category == GarmentCategory.DRESSES:
                return (
                    "For a truly polished finish, consider having the hem "
                    "adjusted to your preferred length -- even half an inch "
                    "can refine the proportion."
                )
            if category == GarmentCategory.TOPS:
                return (
                    "If the shoulder seam doesn't sit exactly at your "
                    "shoulder point, a quick adjustment by a tailor will "
                    "elevate the entire look."
                )
            if category == GarmentCategory.BOTTOMS:
                return (
                    "Tailoring the waistband for a precise fit is a small "
                    "investment that makes a significant difference in how "
                    "the garment moves with you."
                )

        # Occasion garments generally benefit from tailoring
        if category == GarmentCategory.DRESSES:
            return (
                "For special occasions, a hem check and minor waist "
                "adjustment can take a great fit to a perfect one."
            )

        return None
