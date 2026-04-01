"""
MIRA Stylist — Try-On Pipeline Routes
The core virtual try-on experience, powered by FASHN API.
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    TryOnRequest, TryOnResult, APIResponse,
    ProcessingStatus, GarmentCategory,
)
from ..services.fashn_client import FashnClient, FashnClientError
from ..services.validation_service import ValidationService
from ..services.artifact_service import ArtifactService
from ..utils.env import get_settings
import time
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/api/tryon", tags=["Try-On"])
validation_service = ValidationService()
artifact_service = ArtifactService()


@router.post("/run", response_model=APIResponse)
async def run_tryon(request: TryOnRequest):
    """
    Run a virtual try-on.
    Validates images first, then sends to FASHN API for generation.
    """
    # 1. Validate inputs
    validation = await validation_service.validate_tryon_inputs(
        request.person_image, request.garment_image
    )
    if not validation["is_valid"]:
        return APIResponse(
            success=False,
            message="Let's refine the inputs for a more beautiful result.",
            errors=validation["combined_suggestions"],
        )

    # 2. Run FASHN try-on
    settings = get_settings()
    try:
        async with FashnClient(api_key=settings.FASHN_API_KEY) as client:
            start = time.time()
            category = (
                request.garment_category.value
                if request.garment_category
                else "auto"
            )
            result = await client.run_tryon_and_wait(
                person_image_url=request.person_image,
                garment_image_url=request.garment_image,
                category=category,
            )
            elapsed = int((time.time() - start) * 1000)
    except FashnClientError as exc:
        return APIResponse(
            success=False,
            message=str(exc),
        )
    except Exception:
        return APIResponse(
            success=False,
            message=(
                "The visualization didn't come together this time. "
                "Please try again with a slightly different pose or angle."
            ),
        )

    if result.get("status") != "completed":
        return APIResponse(
            success=False,
            message=(
                "We weren't able to generate this look cleanly. "
                "A front-facing photo with a clear background often helps."
            ),
        )

    # 3. Build result
    tryon_result = TryOnResult(
        result_id=str(uuid4()),
        try_on_image_url=result["output_image_url"],
        source_garment_url=request.garment_image,
        person_image_url=request.person_image,
        status=ProcessingStatus.COMPLETED,
        processing_time_ms=elapsed,
    )

    return APIResponse(
        success=True,
        data=tryon_result.model_dump(mode="json"),
        message="Your look is ready.",
    )


@router.post("/validate", response_model=APIResponse)
async def validate_images(person_image: str, garment_image: str):
    """Pre-validate images before running try-on."""
    validation = await validation_service.validate_tryon_inputs(
        person_image, garment_image
    )
    return APIResponse(
        success=validation["is_valid"],
        data={
            "person": validation["person"].model_dump(mode="json") if hasattr(validation["person"], "model_dump") else validation["person"],
            "garment": validation["garment"].model_dump(mode="json") if hasattr(validation["garment"], "model_dump") else validation["garment"],
            "is_valid": validation["is_valid"],
        },
        message=(
            "Images look wonderful — ready to visualize."
            if validation["is_valid"]
            else "A few adjustments will help us create something beautiful."
        ),
    )
