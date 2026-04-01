"""
MIRA Stylist — Stylist Commentary Routes
Premium, intelligent, editorially-aware fashion commentary.
"""

import logging

from fastapi import APIRouter, HTTPException
from ..models.schemas import AskStylistRequest, CommentaryRequest, StylistCommentary, APIResponse
from ..services.stylist_service import StylistService
from ..services.profile_service import ProfileService
from ..services.saved_looks_service import SavedLooksService

router = APIRouter(prefix="/api/stylist", tags=["Stylist"])
stylist_service = StylistService()
profile_service = ProfileService()
looks_service = SavedLooksService()
logger = logging.getLogger(__name__)


@router.post("/commentary", response_model=APIResponse)
async def generate_commentary(request: CommentaryRequest):
    """Generate premium stylist commentary for a look."""
    profile = None
    if request.user_profile_id:
        profile = await profile_service.get_profile(request.user_profile_id)

    try:
        commentary = await stylist_service.generate_commentary(
            request, user_profile=profile
        )
        return APIResponse(
            success=True,
            data=commentary.model_dump(mode="json"),
            message="MIRA's perspective on this look.",
        )
    except Exception as exc:
        logger.exception("Stylist commentary generation failed: %s", exc)
        return APIResponse(
            success=False,
            message="MIRA is composing her thoughts — please try again in a moment.",
        )


@router.post("/ask", response_model=APIResponse)
async def ask_stylist(request: AskStylistRequest):
    """Answer a user's follow-up question about a look."""
    profile = None
    if request.user_profile_id:
        profile = await profile_service.get_profile(request.user_profile_id)

    try:
        answer = await stylist_service.answer_question(request, user_profile=profile)
        return APIResponse(
            success=True,
            data=answer.model_dump(mode="json"),
            message="MIRA answered your question.",
        )
    except Exception as exc:
        logger.exception("Stylist Q&A failed: %s", exc)
        return APIResponse(
            success=False,
            message="MIRA couldn't answer that just yet. Please try again in a moment.",
        )


@router.post("/compare", response_model=APIResponse)
async def compare_looks(look_id_a: str, look_id_b: str, profile_id: str = None):
    """Compare two saved looks with editorial commentary."""
    look_a = await looks_service.get_look(look_id_a)
    look_b = await looks_service.get_look(look_id_b)

    if not look_a or not look_b:
        raise HTTPException(
            status_code=404, detail="One or both looks were not found."
        )

    profile = None
    if profile_id:
        profile = await profile_service.get_profile(profile_id)

    try:
        comparison = await stylist_service.generate_comparison(
            look_a, look_b, user_profile=profile
        )
        return APIResponse(
            success=True,
            data={
                "comparison": comparison,
                "look_a_id": look_id_a,
                "look_b_id": look_id_b,
            },
            message="A thoughtful comparison of your two looks.",
        )
    except Exception as exc:
        logger.exception("Stylist comparison generation failed: %s", exc)
        return APIResponse(
            success=False,
            message="MIRA couldn't compare these looks right now. Please try again.",
        )
