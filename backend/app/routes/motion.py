"""
MIRA Stylist — Motion / Animation Routes
Editorial motion generation powered by Kling.
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    AnimationRequest, AnimationResult, APIResponse,
    MotionPreset, ProcessingStatus,
)
from ..services.kling_client import KlingClient, KlingClientError
from ..services.saved_looks_service import SavedLooksService
from ..utils.env import get_settings
from uuid import uuid4

router = APIRouter(prefix="/api/motion", tags=["Motion"])
looks_service = SavedLooksService()


@router.post("/generate", response_model=APIResponse)
async def generate_motion(request: AnimationRequest):
    """Bring a look to life with editorial motion."""
    # Resolve prompt from preset or custom
    preset_key = (
        request.motion_preset.value
        if request.motion_preset
        else "editorial_turn"
    )
    prompt = request.custom_prompt or KlingClient.MOTION_PRESETS.get(
        preset_key, KlingClient.MOTION_PRESETS["editorial_turn"]
    )

    try:
        async with KlingClient() as client:
            result = await client.generate_and_wait(
                image_url=request.source_image_url,
                prompt=prompt,
            )
    except KlingClientError as exc:
        return APIResponse(
            success=False,
            message=str(exc),
        )
    except Exception:
        return APIResponse(
            success=False,
            message=(
                "The motion didn't come together this time. "
                "Try a different look or preset for a smoother result."
            ),
        )

    if result.get("status") != "completed":
        return APIResponse(
            success=False,
            message="We couldn't generate motion for this look. A cleaner source image may help.",
        )

    animation_result = AnimationResult(
        animation_id=str(uuid4()),
        look_id=request.look_id or str(uuid4()),
        video_url=result["video_url"],
        status=ProcessingStatus.COMPLETED,
        preset_used=preset_key,
    )

    # Update the saved look with the animated clip URL
    if request.look_id:
        look = await looks_service.get_look(request.look_id)
        if look:
            look.animated_clip_url = result["video_url"]
            await looks_service.save_look(look)

    return APIResponse(
        success=True,
        data=animation_result.model_dump(mode="json"),
        message="Your look has come to life.",
    )


@router.get("/presets", response_model=APIResponse)
async def list_presets():
    """List available motion presets with descriptions."""
    presets = []
    preset_labels = {
        "editorial_turn": "Editorial Turn",
        "subtle_idle": "Subtle Idle",
        "runway_step": "Runway Step",
    }
    for key, prompt in KlingClient.MOTION_PRESETS.items():
        presets.append({
            "key": key,
            "label": preset_labels.get(key, key.replace("_", " ").title()),
            "description": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        })
    return APIResponse(
        success=True,
        data=presets,
        message="Available motion styles.",
    )
