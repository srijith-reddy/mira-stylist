from fastapi import APIRouter, HTTPException
from ..models.schemas import UserProfile, APIResponse
from ..services.profile_service import ProfileService

router = APIRouter(prefix="/api/profile", tags=["Profile"])
profile_service = ProfileService()

@router.get("/{profile_id}", response_model=APIResponse)
async def get_profile(profile_id: str):
    profile = await profile_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(success=True, data=profile.model_dump(mode="json"))

@router.put("/{profile_id}", response_model=APIResponse)
async def update_profile(profile_id: str, updates: dict):
    profile = await profile_service.update_profile(profile_id, updates)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(success=True, data=profile.model_dump(mode="json"), message="Profile updated.")

@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    success = await profile_service.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(success=True, message="Profile removed.")

@router.get("/", response_model=APIResponse)
async def list_profiles():
    profiles = await profile_service.list_profiles()
    return APIResponse(success=True, data=[p.model_dump(mode="json") for p in profiles])

@router.post("/{profile_id}/notes", response_model=APIResponse)
async def add_note(profile_id: str, note: str):
    profile = await profile_service.add_stylist_note(profile_id, note)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(success=True, data=profile.model_dump(mode="json"), message="Note added.")

@router.post("/{profile_id}/size-history", response_model=APIResponse)
async def update_size_history(profile_id: str, brand: str, size: str):
    profile = await profile_service.update_size_history(profile_id, brand, size)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(success=True, data=profile.model_dump(mode="json"), message="Size history updated.")
