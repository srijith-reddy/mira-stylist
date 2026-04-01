"""
MIRA Stylist — Saved Looks & Collections Routes
Your personal wardrobe of curated, styled looks.
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import SavedLook, LookCollection, APIResponse
from ..services.saved_looks_service import SavedLooksService

router = APIRouter(prefix="/api/looks", tags=["Saved Looks"])
service = SavedLooksService()


# ── Look Routes ──────────────────────────────────────────────────────────────

@router.post("", response_model=APIResponse, include_in_schema=False)
@router.post("/", response_model=APIResponse)
async def save_look(look: SavedLook):
    """Save a look to your personal collection."""
    saved = await service.save_look(look)
    return APIResponse(
        success=True,
        data=saved.model_dump(mode="json"),
        message="Look saved to your collection.",
    )


@router.get("/list", response_model=APIResponse)
async def list_looks(
    collection_id: str = None,
    favorites_only: bool = False,
):
    """List saved looks with optional filters."""
    looks = await service.list_looks(
        collection_id=collection_id,
        favorites_only=favorites_only,
    )
    return APIResponse(
        success=True,
        data=[look.model_dump(mode="json") for look in looks],
    )


@router.get("/{look_id}", response_model=APIResponse)
async def get_look(look_id: str):
    """Get a saved look by ID."""
    look = await service.get_look(look_id)
    if not look:
        raise HTTPException(status_code=404, detail="Look not found.")
    return APIResponse(success=True, data=look.model_dump(mode="json"))


@router.post("/{look_id}/favorite", response_model=APIResponse)
async def toggle_favorite(look_id: str):
    """Toggle a look's favorite status."""
    look = await service.toggle_favorite(look_id)
    if not look:
        raise HTTPException(status_code=404, detail="Look not found.")
    status = "added to" if look.is_favorite else "removed from"
    return APIResponse(
        success=True,
        data=look.model_dump(mode="json"),
        message=f"Look {status} favorites.",
    )


@router.delete("/{look_id}", response_model=APIResponse)
async def delete_look(look_id: str):
    """Remove a saved look."""
    success = await service.delete_look(look_id)
    if not success:
        raise HTTPException(status_code=404, detail="Look not found.")
    return APIResponse(success=True, message="Look removed.")


@router.post("/{look_id}/collections/{collection_id}", response_model=APIResponse)
async def add_to_collection(look_id: str, collection_id: str):
    """Add a look to a collection."""
    look = await service.add_to_collection(look_id, collection_id)
    if not look:
        raise HTTPException(status_code=404, detail="Look not found.")
    return APIResponse(
        success=True,
        data=look.model_dump(mode="json"),
        message="Added to collection.",
    )


@router.delete("/{look_id}/collections/{collection_id}", response_model=APIResponse)
async def remove_from_collection(look_id: str, collection_id: str):
    """Remove a look from a collection."""
    look = await service.remove_from_collection(look_id, collection_id)
    if not look:
        raise HTTPException(status_code=404, detail="Look not found.")
    return APIResponse(
        success=True,
        data=look.model_dump(mode="json"),
        message="Removed from collection.",
    )


# ── Collection Routes ────────────────────────────────────────────────────────

@router.post("/collections/create", response_model=APIResponse)
async def create_collection(collection: LookCollection):
    """Create a new look collection."""
    saved = await service.create_collection(collection)
    return APIResponse(
        success=True,
        data=saved.model_dump(mode="json"),
        message="Collection created.",
    )


@router.get("/collections/all", response_model=APIResponse)
async def list_collections():
    """List all collections."""
    collections = await service.list_collections()
    return APIResponse(
        success=True,
        data=[c.model_dump(mode="json") for c in collections],
    )


@router.get("/collections/{collection_id}", response_model=APIResponse)
async def get_collection(collection_id: str):
    """Get a collection by ID."""
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found.")
    return APIResponse(success=True, data=collection.model_dump(mode="json"))


@router.delete("/collections/{collection_id}", response_model=APIResponse)
async def delete_collection(collection_id: str):
    """Remove a collection."""
    success = await service.delete_collection(collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found.")
    return APIResponse(success=True, message="Collection removed.")
