"""
MIRA Stylist — Size Recommendation & Chart Routes
Intelligent, confidence-aware fit guidance.
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import SizeQuery, SizeRecommendation, SizeChart, APIResponse
from ..services.sizing_service import SizingService
from ..services.profile_service import ProfileService

router = APIRouter(prefix="/api/sizing", tags=["Sizing"])
sizing_service = SizingService()
profile_service = ProfileService()


@router.post("/recommend", response_model=APIResponse)
async def recommend_size(query: SizeQuery):
    """Get a personalized size recommendation."""
    profile = await profile_service.get_profile(query.user_profile_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Complete your style profile first so we can offer the most accurate guidance.",
        )

    recommendation = await sizing_service.recommend_size(query, profile)
    return APIResponse(
        success=True,
        data=recommendation.model_dump(mode="json"),
        message="Here's your suggested fit.",
    )


@router.get("/chart", response_model=APIResponse)
async def get_size_chart(brand: str = None, category: str = None):
    """Get a size chart, optionally filtered by brand or category."""
    chart = await sizing_service.get_size_chart(brand=brand, category=category)
    return APIResponse(
        success=True,
        data=chart.model_dump(mode="json"),
        message="Size reference ready.",
    )


@router.post("/explain", response_model=APIResponse)
async def explain_recommendation(query: SizeQuery):
    """
    'Why this size?' — Returns a detailed, elegant explanation
    of how we arrived at the recommendation.
    """
    profile = await profile_service.get_profile(query.user_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    recommendation = await sizing_service.recommend_size(query, profile)

    explanation = {
        "recommended_size": recommendation.recommended_size,
        "confidence": recommendation.confidence,
        "reason": recommendation.reason_summary,
        "fit_intent": recommendation.fit_intent_summary,
        "factors_considered": [],
    }

    # Build list of factors
    if profile.measurements:
        explanation["factors_considered"].append(
            "Your saved body measurements were matched against the size chart."
        )
    if query.brand and profile.approximate_size_history.get(query.brand):
        explanation["factors_considered"].append(
            f"Your previous experience with {query.brand} was taken into account."
        )
    if profile.typical_size_ranges:
        explanation["factors_considered"].append(
            "Your typical size range informed the starting point."
        )
    if query.silhouette_intent:
        explanation["factors_considered"].append(
            f"The intended silhouette ({query.silhouette_intent}) influenced size direction."
        )
    if query.fabric_stretch is not None:
        stretch_note = "stretch in the fabric" if query.fabric_stretch else "structured fabric"
        explanation["factors_considered"].append(
            f"We factored in the {stretch_note}."
        )
    if recommendation.alternate_size:
        explanation["factors_considered"].append(
            f"You may also consider {recommendation.alternate_size} depending on your preference."
        )
    if recommendation.tailoring_note:
        explanation["factors_considered"].append(recommendation.tailoring_note)

    return APIResponse(
        success=True,
        data=explanation,
        message="Here's how we arrived at your suggested fit.",
    )
