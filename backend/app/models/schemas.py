"""
MIRA Stylist - Complete Pydantic Data Models & Schemas

All models for the premium AI fashion stylist application.
Uses Pydantic v2 conventions with ConfigDict.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid() -> str:
    """Generate a new UUID4 string for default IDs."""
    return str(uuid.uuid4())


def _now() -> datetime:
    """Return current UTC datetime for default timestamps."""
    return datetime.utcnow()


DataT = TypeVar("DataT")
ItemT = TypeVar("ItemT")


# ===================================================================
# ENUMS
# ===================================================================

class QuestionType(str, Enum):
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    FREE_TEXT = "free_text"
    SCALE = "scale"


class GarmentCategory(str, Enum):
    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"


class LuxuryPreference(str, Enum):
    LUXURY = "luxury"
    CONTEMPORARY = "contemporary"
    CASUAL = "casual"


class CommentaryMode(str, Enum):
    CONCISE_LUXURY = "concise_luxury"
    OCCASION_STYLIST = "occasion_stylist"
    FIT_FOCUSED = "fit_focused"
    EDITORIAL_BREAKDOWN = "editorial_breakdown"
    CULTURAL_OCCASION = "cultural_occasion"
    COMPARISON = "comparison"


class MotionPreset(str, Enum):
    EDITORIAL_TURN = "editorial_turn"
    SUBTLE_IDLE = "subtle_idle"
    RUNWAY_STEP = "runway_step"


class VoiceStyle(str, Enum):
    CALM = "calm"
    WARM = "warm"
    EDITORIAL = "editorial"


class DefaultCollection(str, Enum):
    WEDDING_GUEST = "wedding_guest"
    VACATION_EVENINGS = "vacation_evenings"
    EVERYDAY_ELEVATED = "everyday_elevated"
    DATE_NIGHT = "date_night"
    FESTIVE_INDIAN = "festive_indian"
    WORKWEAR = "workwear"
    SOFT_GLAM = "soft_glam"
    POWER_DRESSING = "power_dressing"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===================================================================
# 1. USER PROFILE MODELS
# ===================================================================

class UserProfile(BaseModel):
    """Complete user style profile built during onboarding and refined over time."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=_uuid, description="Unique user profile identifier")
    name: str = Field("", description="User display name")
    pronouns: Optional[str] = Field(None, description="Preferred pronouns (e.g. she/her)")
    gender: Optional[str] = Field(None, description="Gender identity or fit context")
    height_cm: Optional[int] = Field(None, description="Approximate height in centimeters")

    # Style identity
    style_goals: list[str] = Field(
        default_factory=list,
        description="What the user wants to achieve with their wardrobe",
    )
    preferred_aesthetic: Optional[str] = Field(
        None,
        description="Primary aesthetic label (e.g. 'minimalist luxe', 'boho romantic')",
    )

    # Body & fit
    body_confidence_areas: list[str] = Field(
        default_factory=list,
        description="Areas the user feels confident about",
    )
    fit_sensitivities: list[str] = Field(
        default_factory=list,
        description="Fit pain-points (e.g. 'tight around arms', 'rides up at waist')",
    )
    typical_size_ranges: list[str] = Field(
        default_factory=list,
        description="General size range the user wears (e.g. ['M', 'L', 'US 8-10'])",
    )
    preferred_silhouettes: list[str] = Field(
        default_factory=list,
        description="Silhouette preferences (e.g. 'A-line', 'oversized', 'tailored')",
    )

    # Color preferences
    favorite_colors: list[str] = Field(default_factory=list)
    disliked_colors: list[str] = Field(default_factory=list)

    # Occasion & lifestyle
    occasions: list[str] = Field(
        default_factory=list,
        description="Common occasions the user dresses for",
    )
    comfort_vs_statement: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Scale from pure comfort (0) to bold statement (1)",
    )
    modesty_preference: Optional[str] = Field(
        None,
        description="Modesty preference level or description",
    )
    regional_style_context: Optional[str] = Field(
        None,
        description="Regional/cultural style context (e.g. 'South-Asian festive', 'NYC streetwear')",
    )

    # Taste & budget
    luxury_preference: LuxuryPreference = Field(
        LuxuryPreference.CONTEMPORARY,
        description="Budget-tier preference",
    )
    heel_tolerance: Optional[str] = Field(
        None,
        description="Heel height comfort (e.g. 'flats only', 'up to 3 inches')",
    )
    jewelry_preference: Optional[str] = Field(
        None,
        description="Jewelry style preference (e.g. 'minimal gold', 'statement silver')",
    )

    # Measurements & sizing
    measurements: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional body measurements (bust, waist, hips, etc.)",
    )
    approximate_size_history: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of brand -> typical size (e.g. {'Zara': 'M', 'Nike': 'L'})",
    )
    brand_size_references: list[dict[str, str]] = Field(
        default_factory=list,
        description="Structured brand sizing references with category, brand, and size",
    )

    # Brand preferences
    saved_brands: list[str] = Field(default_factory=list)
    disliked_cuts: list[str] = Field(
        default_factory=list,
        description="Cuts/styles the user wants to avoid",
    )

    # Events & body styling
    event_preferences: list[str] = Field(default_factory=list)
    body_highlight_areas: list[str] = Field(
        default_factory=list,
        description="Areas the user wants to accentuate",
    )
    body_soft_styling_areas: list[str] = Field(
        default_factory=list,
        description="Areas the user prefers softer/looser styling around",
    )

    # Stylist metadata
    stylist_notes: list[str] = Field(
        default_factory=list,
        description="Free-form stylist observations accumulated over time",
    )
    confidence_level_sizing: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="System confidence in sizing recommendations for this user",
    )
    confidence_level_avatar: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="System confidence in avatar fidelity for this user",
    )
    narrative_summary: Optional[str] = Field(
        None,
        description="AI-generated narrative summary of the user's style profile",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ===================================================================
# 2. ONBOARDING MODELS
# ===================================================================

class OnboardingQuestion(BaseModel):
    """A single question shown during the onboarding flow."""

    model_config = ConfigDict(from_attributes=True)

    question_id: str = Field(default_factory=_uuid)
    question_text: str = Field(..., description="The question displayed to the user")
    options: list[str] = Field(
        default_factory=list,
        description="Available options (empty for free_text)",
    )
    question_type: QuestionType = Field(
        ...,
        description="How the user answers this question",
    )


class OnboardingResponse(BaseModel):
    """A single answer submitted by the user during onboarding."""

    question_id: str = Field(..., description="ID of the question being answered")
    answer: Any = Field(
        ...,
        description="User answer: str, list[str], or numeric value depending on question_type",
    )


class OnboardingSession(BaseModel):
    """Tracks the full onboarding conversation for a user."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(default_factory=_uuid)
    responses: list[OnboardingResponse] = Field(default_factory=list)
    completed: bool = Field(False, description="Whether onboarding is fully completed")
    generated_profile: Optional[UserProfile] = Field(
        None,
        description="Profile generated after all responses are collected",
    )


# ===================================================================
# 3. TRY-ON MODELS
# ===================================================================

class TryOnRequest(BaseModel):
    """Request payload for a virtual try-on generation."""

    person_image: str = Field(
        ...,
        description="URL or base64 of the person image",
    )
    garment_image: str = Field(
        ...,
        description="URL or base64 of the garment image",
    )
    garment_category: Optional[GarmentCategory] = Field(
        None,
        description="Category of the garment being tried on",
    )
    mode: Optional[str] = Field(
        None,
        description="Try-on engine mode (implementation-specific)",
    )
    scale: Optional[float] = Field(
        None,
        gt=0.0,
        description="Scaling factor for garment overlay",
    )


class TryOnResult(BaseModel):
    """Result of a completed (or in-progress) virtual try-on."""

    model_config = ConfigDict(from_attributes=True)

    result_id: str = Field(default_factory=_uuid)
    try_on_image_url: Optional[str] = Field(
        None,
        description="URL of the generated try-on image",
    )
    source_garment_url: str = Field(
        ...,
        description="Original garment image used",
    )
    person_image_url: str = Field(
        ...,
        description="Original person image used",
    )
    status: ProcessingStatus = Field(ProcessingStatus.PENDING)
    created_at: datetime = Field(default_factory=_now)
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing duration in milliseconds",
    )


class ImageValidationResult(BaseModel):
    """Validation outcome for an uploaded image before try-on."""

    is_valid: bool = Field(..., description="Whether the image passes validation")
    issues: list[str] = Field(
        default_factory=list,
        description="List of detected issues",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions to fix issues",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the validation assessment",
    )


# ===================================================================
# 4. SAVED LOOKS MODELS
# ===================================================================

class SavedLook(BaseModel):
    """A saved try-on result with stylist metadata attached."""

    model_config = ConfigDict(from_attributes=True)

    look_id: str = Field(default_factory=_uuid)
    try_on_image_url: str = Field(..., description="URL of the try-on result image")
    source_garment_url: str = Field(..., description="Original garment image URL")
    stylist_commentary: Optional[str] = Field(
        None,
        description="AI stylist commentary for this look",
    )
    commentary_payload: Optional[dict[str, Any]] = Field(
        None,
        description="Structured stylist commentary sections and metadata",
    )
    recommended_size: Optional[SizeRecommendation] = Field(
        None,
        description="Size recommendation for the garment in this look",
    )
    fit_notes: Optional[str] = Field(
        None,
        description="Fit-specific notes (e.g. 'runs small in shoulders')",
    )
    garment_brand: Optional[str] = Field(
        None,
        description="Brand associated with the garment in this look",
    )
    garment_fit: Optional[str] = Field(
        None,
        description="Intended or observed garment fit",
    )
    user_profile_id: Optional[str] = Field(
        None,
        description="Profile used to personalize this saved look",
    )
    motion_preset: Optional[str] = Field(
        None,
        description="Selected motion preset if the look was animated",
    )
    vibe_tags: list[str] = Field(
        default_factory=list,
        description="Aesthetic/vibe tags (e.g. 'effortless chic', 'bold festive')",
    )
    occasion_tags: list[str] = Field(
        default_factory=list,
        description="Occasion tags (e.g. 'date night', 'office')",
    )
    created_at: datetime = Field(default_factory=_now)
    is_favorite: bool = Field(False)
    collection_ids: list[str] = Field(
        default_factory=list,
        description="IDs of collections this look belongs to",
    )
    animated_clip_url: Optional[str] = Field(
        None,
        description="URL of the animated/motion clip if generated",
    )


class LookCollection(BaseModel):
    """A named collection (folder) of saved looks."""

    model_config = ConfigDict(from_attributes=True)

    collection_id: str = Field(default_factory=_uuid)
    name: str = Field(..., description="Collection display name")
    description: Optional[str] = Field(None)
    look_ids: list[str] = Field(default_factory=list)
    cover_image_url: Optional[str] = Field(
        None,
        description="Optional cover thumbnail URL",
    )
    created_at: datetime = Field(default_factory=_now)


# ===================================================================
# 5. SIZE MODELS
# ===================================================================

class SizeRecommendation(BaseModel):
    """AI-generated size recommendation for a specific garment."""

    model_config = ConfigDict(from_attributes=True)

    recommended_size: str = Field(..., description="Primary recommended size label")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the recommendation",
    )
    reason_summary: str = Field(
        ...,
        description="Human-readable reasoning behind the recommendation",
    )
    fit_intent_summary: str = Field(
        ...,
        description="Description of the intended fit (e.g. 'relaxed through the torso')",
    )
    alternate_size: Optional[str] = Field(
        None,
        description="Secondary size option if between sizes",
    )
    tailoring_note: Optional[str] = Field(
        None,
        description="Suggested alterations (e.g. 'consider hemming 1 inch')",
    )
    garment_category: GarmentCategory = Field(
        ...,
        description="Category this recommendation applies to",
    )
    brand: Optional[str] = Field(
        None,
        description="Brand if recommendation is brand-specific",
    )


class SizeEntry(BaseModel):
    """A single size row inside a size chart."""

    size_label: str = Field(..., description="Size label (e.g. 'S', 'M', 'US 6')")
    measurements: dict[str, float] = Field(
        ...,
        description="Measurement name -> value in cm (e.g. {'bust': 88.0, 'waist': 72.0})",
    )


class SizeChart(BaseModel):
    """Brand and category specific size chart."""

    model_config = ConfigDict(from_attributes=True)

    brand: str = Field(..., description="Brand name")
    garment_category: GarmentCategory
    sizes: list[SizeEntry] = Field(
        default_factory=list,
        description="Ordered list of size entries",
    )


class SizeQuery(BaseModel):
    """Parameters for requesting a size recommendation."""

    user_profile_id: str = Field(..., description="User profile to base recommendation on")
    garment_category: GarmentCategory
    brand: Optional[str] = Field(None, description="Target brand for sizing")
    silhouette_intent: Optional[str] = Field(
        None,
        description="Desired fit silhouette (e.g. 'fitted', 'oversized', 'relaxed')",
    )
    fabric_stretch: Optional[bool] = Field(
        None,
        description="Whether the fabric has significant stretch",
    )


# ===================================================================
# 6. STYLIST COMMENTARY MODELS
# ===================================================================

class StylistCommentary(BaseModel):
    """AI stylist commentary attached to a look."""

    model_config = ConfigDict(from_attributes=True)

    commentary_id: str = Field(default_factory=_uuid)
    look_id: str = Field(..., description="ID of the look this commentary is for")
    text: str = Field(..., description="The commentary body text")
    mode: CommentaryMode = Field(
        ...,
        description="Commentary generation mode / voice",
    )
    vibe_tags: list[str] = Field(default_factory=list)
    occasion_tags: list[str] = Field(default_factory=list)
    styling_suggestions: list[str] = Field(
        default_factory=list,
        description="Specific styling tips (e.g. 'pair with strappy heels')",
    )
    refinement_notes: list[str] = Field(
        default_factory=list,
        description="Notes for iterative look refinement",
    )
    silhouette_line: Optional[str] = Field(
        None,
        description="Read on silhouette and line",
    )
    fit_assessment: Optional[str] = Field(
        None,
        description="Assessment of how the garment appears to fit",
    )
    proportion: Optional[str] = Field(
        None,
        description="Read on proportion and balance",
    )
    occasion_read: Optional[str] = Field(
        None,
        description="Assessment of occasion alignment",
    )
    colour_surface: Optional[str] = Field(
        None,
        description="Read on color, texture, and surface interest",
    )
    to_elevate_it: Optional[str] = Field(
        None,
        description="One practical step to elevate the look",
    )
    tailoring_note: Optional[str] = Field(
        None,
        description="Tailoring or fit-adjustment note if relevant",
    )
    complete_the_look: list[str] = Field(
        default_factory=list,
        description="Suggestions for companion pieces or styling additions",
    )
    created_at: datetime = Field(default_factory=_now)


class CommentaryRequest(BaseModel):
    """Request payload for generating stylist commentary."""

    look_image_url: str = Field(..., description="URL of the look image to comment on")
    garment_category: Optional[GarmentCategory] = Field(
        None,
        description="Garment category for fit-aware commentary",
    )
    user_profile_id: Optional[str] = Field(
        None,
        description="User profile for personalization",
    )
    mode: CommentaryMode = Field(
        CommentaryMode.CONCISE_LUXURY,
        description="Desired commentary style",
    )
    occasion: Optional[str] = Field(
        None,
        description="Specific occasion context (e.g. 'sangeet night')",
    )
    comparison_look_id: Optional[str] = Field(
        None,
        description="Look ID to compare against (requires mode=COMPARISON)",
    )


class AskStylistRequest(BaseModel):
    """Request payload for conversational follow-up with MIRA."""

    question: str = Field(..., description="User's follow-up question for MIRA")
    look_image_url: str = Field(..., description="Look image URL or inline image data")
    user_profile_id: Optional[str] = Field(
        None,
        description="User profile for personalization",
    )
    garment_brand: Optional[str] = Field(
        None,
        description="Brand associated with the look",
    )
    garment_fit: Optional[str] = Field(
        None,
        description="Observed or intended garment fit",
    )
    occasion: Optional[str] = Field(
        None,
        description="Occasion context for the look",
    )
    commentary_payload: Optional[dict[str, Any]] = Field(
        None,
        description="Existing structured commentary to ground the answer",
    )


class AskStylistResponse(BaseModel):
    """Conversational answer from MIRA to a user follow-up."""

    answer: str = Field(..., description="MIRA's conversational answer")
    suggested_follow_up: Optional[str] = Field(
        None,
        description="A gentle suggested follow-up question when useful",
    )


# ===================================================================
# 7. MOTION / ANIMATION MODELS
# ===================================================================

class AnimationRequest(BaseModel):
    """Request payload to generate a motion clip from a saved look."""

    look_id: Optional[str] = Field(None, description="ID of the saved look to animate")
    source_image_url: str = Field(
        ...,
        description="Static image URL to use as the animation source",
    )
    motion_preset: MotionPreset = Field(
        MotionPreset.EDITORIAL_TURN,
        description="Motion style preset",
    )
    custom_prompt: Optional[str] = Field(
        None,
        description="Free-form motion prompt override",
    )


class AnimationResult(BaseModel):
    """Result of a motion/animation generation job."""

    model_config = ConfigDict(from_attributes=True)

    animation_id: str = Field(default_factory=_uuid)
    look_id: str = Field(..., description="Associated look ID")
    video_url: Optional[str] = Field(
        None,
        description="URL of the generated video clip",
    )
    status: ProcessingStatus = Field(ProcessingStatus.PENDING)
    preset_used: MotionPreset = Field(..., description="Preset that was applied")
    created_at: datetime = Field(default_factory=_now)


# ===================================================================
# 8. VOICE MODELS
# ===================================================================

class VoiceRequest(BaseModel):
    """Request payload for text-to-speech generation."""

    text: str = Field(..., description="Text to be spoken")
    voice_style: VoiceStyle = Field(
        VoiceStyle.WARM,
        description="Voice persona / style",
    )
    speed: float = Field(
        1.0,
        gt=0.0,
        le=3.0,
        description="Playback speed multiplier",
    )


class VoiceResponse(BaseModel):
    """Result of a text-to-speech generation."""

    audio_url: str = Field(..., description="URL of the generated audio file")
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Duration of the audio in seconds",
    )


# ===================================================================
# 9. COMMON / GENERIC MODELS
# ===================================================================

class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: Optional[DataT] = Field(None, description="Response payload")
    message: Optional[str] = Field(None, description="Human-readable status message")
    errors: Optional[list[str]] = Field(
        None,
        description="List of error messages if success is False",
    )


class PaginatedResponse(BaseModel, Generic[ItemT]):
    """Paginated list response wrapper."""

    items: list[ItemT] = Field(default_factory=list, description="Page of results")
    total: int = Field(..., ge=0, description="Total number of items across all pages")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, description="Items per page")


class HealthStatus(BaseModel):
    """Application health check response."""

    status: str = Field("ok", description="Service status")
    version: Optional[str] = Field(None, description="Application version string")
    uptime_seconds: Optional[float] = Field(None, description="Seconds since startup")
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Downstream service health (service_name -> status)",
    )


# ---------------------------------------------------------------------------
# Forward-reference rebuild
# ---------------------------------------------------------------------------
# SavedLook references SizeRecommendation which is defined after it in the
# source.  Pydantic v2 resolves forward refs automatically for models using
# `from __future__ import annotations`, but we call model_rebuild() explicitly
# to be safe.
SavedLook.model_rebuild()
