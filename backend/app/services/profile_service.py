"""
MIRA Stylist - Profile Service

File-based profile persistence using async JSON I/O.
Designed to be easily swapped for a database-backed implementation later.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import aiofiles
import aiofiles.os

from ..models.schemas import UserProfile
from ..utils.env import get_settings


class ProfileService:
    """Manages user style profiles stored as individual JSON files.

    Storage layout::

        {DATA_DIR}/profiles/{profile_id}.json
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.profiles_dir = Path(settings.DATA_DIR) / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _profile_path(self, profile_id: str) -> Path:
        """Return the filesystem path for a given profile ID."""
        return self.profiles_dir / f"{profile_id}.json"

    @staticmethod
    def _normalize_profile_payload(data: dict) -> dict:
        """Keep derived sizing fields in sync before validation."""
        normalized = dict(data)

        references = normalized.get("brand_size_references") or []
        cleaned_refs: list[dict[str, str]] = []
        derived_history: dict[str, str] = {}
        for ref in references:
            if not isinstance(ref, dict):
                continue
            category = str(ref.get("category", "")).strip()
            brand = str(ref.get("brand", "")).strip()
            size = str(ref.get("size", "")).strip()
            if not brand or not size:
                continue
            cleaned_ref = {
                "category": category or "tops",
                "brand": brand,
                "size": size,
            }
            cleaned_refs.append(cleaned_ref)
            derived_history[brand] = size

        normalized["brand_size_references"] = cleaned_refs

        history = normalized.get("approximate_size_history") or {}
        if isinstance(history, dict):
            normalized["approximate_size_history"] = {
                **history,
                **derived_history,
            }
        else:
            normalized["approximate_size_history"] = derived_history

        if normalized.get("measurements") is None:
            normalized["measurements"] = {}

        return normalized

    async def _read_profile(self, profile_id: str) -> UserProfile | None:
        """Read and deserialise a profile from disk, or return *None*."""
        path = self._profile_path(profile_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            raw = await f.read()
        data = json.loads(raw)
        return UserProfile.model_validate(data)

    async def _write_profile(self, profile: UserProfile) -> None:
        """Serialise and persist a profile to disk."""
        path = self._profile_path(profile.id)
        payload = json.dumps(
            profile.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(payload)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_profile(self, profile: UserProfile) -> UserProfile:
        """Save a new user profile to disk.

        The profile's ``updated_at`` timestamp is refreshed before writing.
        """
        profile.updated_at = datetime.utcnow()
        normalized_profile = UserProfile.model_validate(
            self._normalize_profile_payload(profile.model_dump(mode="json"))
        )
        await self._write_profile(normalized_profile)
        return normalized_profile

    async def get_profile(self, profile_id: str) -> UserProfile | None:
        """Load a user profile by ID.  Returns *None* if not found."""
        return await self._read_profile(profile_id)

    async def update_profile(
        self, profile_id: str, updates: dict
    ) -> UserProfile | None:
        """Partial update of a profile.

        Merges *updates* into the existing profile data.  Only keys that are
        present in the ``updates`` dict are overwritten; all other fields remain
        unchanged.  Returns the updated profile or *None* if the profile does
        not exist.
        """
        profile = await self._read_profile(profile_id)
        if profile is None:
            return None

        # Merge: dump existing data, overlay updates, re-validate.
        existing_data = profile.model_dump(mode="json")
        existing_data.update(updates)
        existing_data["updated_at"] = datetime.utcnow().isoformat()
        existing_data = self._normalize_profile_payload(existing_data)

        updated_profile = UserProfile.model_validate(existing_data)
        await self._write_profile(updated_profile)
        return updated_profile

    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile.  Returns *True* if the file was removed."""
        path = self._profile_path(profile_id)
        if not path.exists():
            return False
        await aiofiles.os.remove(path)
        return True

    async def list_profiles(self) -> list[UserProfile]:
        """List all profiles stored on disk (for multi-user support).

        Profiles are returned sorted by ``created_at`` descending (newest
        first).
        """
        profiles: list[UserProfile] = []
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    file_path, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                data = json.loads(raw)
                profiles.append(UserProfile.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                # Skip corrupted files silently — a production service would
                # log this.
                continue
        profiles.sort(key=lambda p: p.created_at, reverse=True)
        return profiles

    async def add_stylist_note(
        self, profile_id: str, note: str
    ) -> UserProfile | None:
        """Append a stylist note to the profile.

        Returns the updated profile, or *None* if the profile does not exist.
        """
        profile = await self._read_profile(profile_id)
        if profile is None:
            return None

        profile.stylist_notes.append(note)
        profile.updated_at = datetime.utcnow()
        await self._write_profile(profile)
        return profile

    async def update_size_history(
        self, profile_id: str, brand: str, size: str
    ) -> UserProfile | None:
        """Update the user's size history for a specific brand.

        Adds or overwrites the *brand* -> *size* entry in
        ``approximate_size_history``.  Returns the updated profile, or *None*
        if the profile does not exist.
        """
        profile = await self._read_profile(profile_id)
        if profile is None:
            return None

        profile.approximate_size_history[brand] = size
        profile.updated_at = datetime.utcnow()
        await self._write_profile(profile)
        return profile
