"""
MIRA Stylist - Saved Looks Service

File-based persistence for saved looks and look collections.
Looks are stored as individual JSON files; collections live in a
``collections/`` subdirectory.
"""

from __future__ import annotations

import json
from pathlib import Path

import aiofiles
import aiofiles.os

from ..models.schemas import LookCollection, SavedLook
from ..utils.env import get_settings


class SavedLooksService:
    """Manages saved looks and look collections on disk.

    Storage layout::

        {DATA_DIR}/looks/{look_id}.json
        {DATA_DIR}/looks/collections/{collection_id}.json
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.looks_dir = Path(settings.DATA_DIR) / "looks"
        self.collections_dir = self.looks_dir / "collections"
        self.looks_dir.mkdir(parents=True, exist_ok=True)
        self.collections_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _look_path(self, look_id: str) -> Path:
        return self.looks_dir / f"{look_id}.json"

    def _collection_path(self, collection_id: str) -> Path:
        return self.collections_dir / f"{collection_id}.json"

    async def _read_look(self, look_id: str) -> SavedLook | None:
        path = self._look_path(look_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            raw = await f.read()
        return SavedLook.model_validate(json.loads(raw))

    async def _write_look(self, look: SavedLook) -> None:
        path = self._look_path(look.look_id)
        payload = json.dumps(
            look.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(payload)

    async def _read_collection(self, collection_id: str) -> LookCollection | None:
        path = self._collection_path(collection_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            raw = await f.read()
        return LookCollection.model_validate(json.loads(raw))

    async def _write_collection(self, collection: LookCollection) -> None:
        path = self._collection_path(collection.collection_id)
        payload = json.dumps(
            collection.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(payload)

    # ------------------------------------------------------------------
    # Look CRUD
    # ------------------------------------------------------------------

    async def save_look(self, look: SavedLook) -> SavedLook:
        """Save a look to disk.  Returns the persisted look."""
        await self._write_look(look)
        return look

    async def get_look(self, look_id: str) -> SavedLook | None:
        """Get a saved look by ID.  Returns *None* if not found."""
        return await self._read_look(look_id)

    async def list_looks(
        self,
        profile_id: str | None = None,
        collection_id: str | None = None,
        favorites_only: bool = False,
    ) -> list[SavedLook]:
        """List saved looks with optional filters.

        Parameters
        ----------
        profile_id:
            Reserved for future per-user filtering (not yet stored on
            ``SavedLook``).  Currently ignored — all looks are returned.
        collection_id:
            When provided, only looks belonging to this collection are
            returned.
        favorites_only:
            When *True*, only looks with ``is_favorite == True`` are returned.
        """
        # Collect the set of look IDs that belong to the requested collection
        # so we can filter efficiently.
        collection_look_ids: set[str] | None = None
        if collection_id is not None:
            collection = await self._read_collection(collection_id)
            if collection is None:
                return []
            collection_look_ids = set(collection.look_ids)

        looks: list[SavedLook] = []
        for file_path in self.looks_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    file_path, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                look = SavedLook.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValueError):
                continue

            # Apply filters
            if favorites_only and not look.is_favorite:
                continue
            if collection_look_ids is not None and look.look_id not in collection_look_ids:
                continue

            looks.append(look)

        # Newest first
        looks.sort(key=lambda lk: lk.created_at, reverse=True)
        return looks

    async def toggle_favorite(self, look_id: str) -> SavedLook | None:
        """Toggle the favorite status of a look.  Returns the updated look."""
        look = await self._read_look(look_id)
        if look is None:
            return None
        look.is_favorite = not look.is_favorite
        await self._write_look(look)
        return look

    async def delete_look(self, look_id: str) -> bool:
        """Delete a saved look.

        Also removes the look ID from any collections that reference it.
        Returns *True* if the file was removed.
        """
        path = self._look_path(look_id)
        if not path.exists():
            return False

        # Remove from all collections that reference this look.
        for coll_path in self.collections_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    coll_path, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                coll = LookCollection.model_validate(json.loads(raw))
                if look_id in coll.look_ids:
                    coll.look_ids.remove(look_id)
                    await self._write_collection(coll)
            except (json.JSONDecodeError, ValueError):
                continue

        await aiofiles.os.remove(path)
        return True

    # ------------------------------------------------------------------
    # Collection membership on looks
    # ------------------------------------------------------------------

    async def add_to_collection(
        self, look_id: str, collection_id: str
    ) -> SavedLook | None:
        """Add a look to a collection.

        Updates both the look's ``collection_ids`` and the collection's
        ``look_ids``.  Returns the updated look or *None* if either entity
        does not exist.
        """
        look = await self._read_look(look_id)
        if look is None:
            return None

        collection = await self._read_collection(collection_id)
        if collection is None:
            return None

        if collection_id not in look.collection_ids:
            look.collection_ids.append(collection_id)
            await self._write_look(look)

        if look_id not in collection.look_ids:
            collection.look_ids.append(look_id)
            await self._write_collection(collection)

        return look

    async def remove_from_collection(
        self, look_id: str, collection_id: str
    ) -> SavedLook | None:
        """Remove a look from a collection.

        Updates both the look and the collection.  Returns the updated look
        or *None* if the look does not exist.
        """
        look = await self._read_look(look_id)
        if look is None:
            return None

        if collection_id in look.collection_ids:
            look.collection_ids.remove(collection_id)
            await self._write_look(look)

        collection = await self._read_collection(collection_id)
        if collection is not None and look_id in collection.look_ids:
            collection.look_ids.remove(look_id)
            await self._write_collection(collection)

        return look

    # ------------------------------------------------------------------
    # Collection CRUD
    # ------------------------------------------------------------------

    async def create_collection(
        self, collection: LookCollection
    ) -> LookCollection:
        """Create and persist a new look collection."""
        await self._write_collection(collection)
        return collection

    async def list_collections(self) -> list[LookCollection]:
        """List all look collections, sorted by creation date (newest first)."""
        collections: list[LookCollection] = []
        for file_path in self.collections_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    file_path, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                collections.append(
                    LookCollection.model_validate(json.loads(raw))
                )
            except (json.JSONDecodeError, ValueError):
                continue
        collections.sort(key=lambda c: c.created_at, reverse=True)
        return collections

    async def get_collection(
        self, collection_id: str
    ) -> LookCollection | None:
        """Get a collection by ID.  Returns *None* if not found."""
        return await self._read_collection(collection_id)

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection.

        Removes the collection ID from all looks that reference it, then
        deletes the collection file.  Returns *True* if the file was removed.
        """
        path = self._collection_path(collection_id)
        if not path.exists():
            return False

        # Remove collection reference from all looks.
        for look_path in self.looks_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    look_path, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                look = SavedLook.model_validate(json.loads(raw))
                if collection_id in look.collection_ids:
                    look.collection_ids.remove(collection_id)
                    await self._write_look(look)
            except (json.JSONDecodeError, ValueError):
                continue

        await aiofiles.os.remove(path)
        return True
