"""
MIRA Stylist — Artifact Service

Manages styling sessions, temporary files, and output artifacts (images,
video clips, audio).  Sessions are persisted as JSON files so that the
user's try-on history and stylist notes survive across requests.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import aiofiles
import aiofiles.os

from ..utils.env import get_settings


class ArtifactService:
    """Manages sessions, temporary files, and output artifacts.

    Storage layout::

        {DATA_DIR}/sessions/{session_id}.json
        {DATA_DIR}/artifacts/{artifact_type}/{filename}.{ext}
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = Path(settings.DATA_DIR)
        self.sessions_dir = self.base_dir / "sessions"
        self.artifacts_dir = self.base_dir / "artifacts"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _session_path(self, session_id: str) -> Path:
        """Return the filesystem path for a given session ID."""
        return self.sessions_dir / f"{session_id}.json"

    async def _read_session(self, session_id: str) -> dict | None:
        """Read a session from disk, or return *None* if it does not exist."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            raw = await f.read()
        return json.loads(raw)

    async def _write_session(self, session_id: str, data: dict) -> None:
        """Persist session data to disk."""
        path = self._session_path(session_id)
        payload = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(payload)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def create_session(
        self, profile_id: str | None = None
    ) -> dict:
        """Create a new styling session.

        Parameters
        ----------
        profile_id:
            Optional user profile to associate with this session.

        Returns
        -------
        dict
            Session metadata including ``session_id``, ``started_at``,
            ``profile_id``, and an empty ``tryon_history``.
        """
        session_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        session_data = {
            "session_id": session_id,
            "profile_id": profile_id,
            "started_at": now,
            "updated_at": now,
            "tryon_history": [],
            "notes": [],
        }
        await self._write_session(session_id, session_data)
        return session_data

    async def get_session(self, session_id: str) -> dict | None:
        """Load session data by ID.  Returns *None* if not found."""
        return await self._read_session(session_id)

    async def update_session(
        self, session_id: str, updates: dict
    ) -> dict | None:
        """Merge *updates* into an existing session.

        Only keys present in *updates* are overwritten; all other fields
        remain unchanged.  The ``updated_at`` timestamp is refreshed
        automatically.

        Returns the updated session dict, or *None* if the session does
        not exist.
        """
        session = await self._read_session(session_id)
        if session is None:
            return None

        session.update(updates)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._write_session(session_id, session)
        return session

    async def add_tryon_to_session(
        self, session_id: str, tryon_result: dict
    ) -> dict | None:
        """Append a try-on result to the session's history.

        The result dict is stored as-is inside the session's
        ``tryon_history`` list, with a ``recorded_at`` timestamp added
        automatically.

        Returns the updated session, or *None* if the session does not
        exist.
        """
        session = await self._read_session(session_id)
        if session is None:
            return None

        tryon_result["recorded_at"] = datetime.now(timezone.utc).isoformat()
        session["tryon_history"].append(tryon_result)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._write_session(session_id, session)
        return session

    # ------------------------------------------------------------------
    # Artifact storage
    # ------------------------------------------------------------------

    async def save_artifact(
        self,
        artifact_type: str,
        data: bytes,
        extension: str = "png",
    ) -> str:
        """Save a binary artifact (image, video, audio) to disk.

        Parameters
        ----------
        artifact_type:
            Logical grouping, e.g. ``"tryon"``, ``"garment"``,
            ``"animation"``, ``"voice"``.  Creates a subdirectory if it
            does not already exist.
        data:
            Raw bytes of the artifact.
        extension:
            File extension without the leading dot (default ``"png"``).

        Returns
        -------
        str
            Absolute path to the saved file.
        """
        type_dir = self.artifacts_dir / artifact_type
        type_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.{extension.lstrip('.')}"
        dest = type_dir / filename

        async with aiofiles.open(dest, mode="wb") as f:
            await f.write(data)

        return str(dest.resolve())

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessions older than *days* days.

        Compares each session's ``started_at`` timestamp against the
        current time.  Sessions whose files cannot be parsed are also
        removed to avoid accumulating stale data.

        Returns the number of session files deleted.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed = 0

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                async with aiofiles.open(
                    session_file, mode="r", encoding="utf-8"
                ) as f:
                    raw = await f.read()
                session = json.loads(raw)
                started_at = datetime.fromisoformat(session["started_at"])

                # Ensure timezone-aware comparison
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)

                if started_at < cutoff:
                    await aiofiles.os.remove(session_file)
                    removed += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                # Corrupted or unparseable session — remove it.
                await aiofiles.os.remove(session_file)
                removed += 1

        return removed
