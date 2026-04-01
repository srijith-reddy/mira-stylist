"""
MIRA Stylist — Kling AI Motion / Video Client

Async client for the Kling API that transforms static fashion images into
short animated videos (image-to-video). Includes curated motion presets
tailored for premium fashion presentation.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx
import jwt

from ..utils.env import get_settings


class KlingClientError(Exception):
    """Raised when a Kling API operation fails.

    Only premium, user-friendly messages are surfaced — raw API details
    are logged but never exposed to the caller.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class KlingClient:
    """Async client for the Kling image-to-video API.

    Usage::

        async with KlingClient(api_key="...") as client:
            result = await client.generate_and_wait(
                image_url="https://...",
                prompt=KlingClient.MOTION_PRESETS["editorial_turn"],
            )
            print(result["video_url"])
    """

    # ── Curated motion presets for fashion presentation ──────────────────

    MOTION_PRESETS: dict[str, str] = {
        "editorial_turn": (
            "model makes a slow controlled 45 to 60 degree turn, natural posture, "
            "gentle body movement, fabric responds softly and naturally, refined editorial fashion presentation, "
            "clean luxury campaign feel, preserve identity, preserve garment details, "
            "no warping, no extra limbs, no face distortion, smooth realistic motion"
        ),
        "subtle_idle": (
            "model stands relaxed with a slight weight shift and soft natural breathing, "
            "minimal movement, subtle fabric motion only, calm showroom presentation, "
            "clean studio fashion feel, preserve identity, preserve garment silhouette and texture, "
            "no distortion, no jitter, no unnatural body movement"
        ),
        "runway_step": (
            "model takes one slow confident step forward with poised runway posture, "
            "natural arm and body movement, fabric flows softly and realistically, "
            "modern runway fashion energy, elegant and controlled, preserve identity, preserve garment fit and detail, "
            "no warping, no anatomy errors, no exaggerated motion"
        ),
    }

    # ── Valid generation modes ──────────────────────────────────────────

    VALID_MODES = {"std", "pro"}

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        settings = get_settings()
        self._access_key = access_key or settings.KLING_ACCESS_KEY
        self._secret_key = secret_key or settings.KLING_SECRET_KEY
        self.base_url = (base_url or settings.KLING_API_URL).rstrip("/")
        self.model = model or settings.KLING_MODEL
        self.default_mode = self._validate_mode(mode or settings.KLING_MODE)

        if not self._access_key or not self._secret_key:
            raise KlingClientError(
                "MIRA cannot connect to the motion generation service right now. "
                "Please ensure your Kling access and secret keys are configured."
            )

        if not self.base_url:
            raise KlingClientError(
                "MIRA's motion generation service URL is not configured. "
                "Please set the KLING_API_URL in your environment."
            )

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._auth_headers(),
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    def _generate_jwt(self) -> str:
        """Generate a short-lived JWT using the Kling access + secret key pair."""
        now = int(time.time())
        payload = {
            "iss": self._access_key,
            "exp": now + 1800,
            "nbf": now - 5,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._generate_jwt()}",
            "Content-Type": "application/json",
        }

    # ── Context-manager support ─────────────────────────────────────────

    async def __aenter__(self) -> "KlingClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    # ── Public API ──────────────────────────────────────────────────────

    async def generate_motion(
        self,
        image_url: str,
        prompt: str,
        duration: float = 5.0,
        mode: Optional[str] = None,
    ) -> dict:
        """Start a motion / video generation task.

        Parameters
        ----------
        image_url:
            Publicly accessible URL of the source image.
        prompt:
            Text prompt describing the desired motion. Consider using one of
            the curated :attr:`MOTION_PRESETS` for best results.
        duration:
            Video duration in seconds (default 5.0).
        mode:
            Generation mode — ``"standard"`` or ``"professional"``.

        Returns
        -------
        dict
            ``{"task_id": str, "status": str}``
        """
        mode = self._validate_mode(mode or self.default_mode)
        normalized_image = self._normalize_media_input(image_url)

        payload = {
            "model_name": self.model,
            "image": normalized_image,
            "prompt": prompt,
            "negative_prompt": "",
            "duration": str(int(duration)),
            "mode": mode,
            "sound": "off",
            "callback_url": "",
            "external_task_id": "",
        }

        try:
            response = await self.client.post(
                "/v1/videos/image2video",
                json=payload,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            data = response.json()

            task_id = (
                data.get("task_id")
                or data.get("id")
                or data.get("data", {}).get("task_id")
                or data.get("data", {}).get("id")
            )
            if not task_id:
                raise KlingClientError(
                    "MIRA could not start your motion generation. "
                    "Please try again in a moment."
                )

            return {
                "task_id": task_id,
                "status": data.get("status", "submitted"),
            }

        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from None
        except httpx.RequestError:
            raise KlingClientError(
                "MIRA is unable to reach the motion generation service. "
                "Please check your connection and try again."
            ) from None

    async def get_task_status(self, task_id: str) -> dict:
        """Poll for the current status of a generation task.

        Parameters
        ----------
        task_id:
            The identifier returned by :meth:`generate_motion`.

        Returns
        -------
        dict
            Contains ``status`` and, when complete, ``video_url``.
        """
        try:
            response = await self.client.get(
                f"/v1/videos/image2video/{task_id}",
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            data = response.json()

            # Normalise — the Kling API may nest results under "data".
            import logging as _logging
            _logging.getLogger(__name__).info("Kling status raw response: %s", data)
            task_data = data.get("data", data)

            result: dict = {
                "task_id": task_id,
                "status": task_data.get("status", task_data.get("task_status", "unknown")),
            }
            error = task_data.get("error") or data.get("error")
            if error:
                result["error"] = error
                if isinstance(error, dict):
                    result["error_code"] = error.get("code") or error.get("name")
                    result["error_message"] = error.get("message")
                elif isinstance(error, str):
                    result["error_message"] = error

            # Extract video URL — Kling API has several response shapes.
            # Most common: data.task_result.videos[0].url
            task_result = task_data.get("task_result") or {}
            tr_videos = task_result.get("videos") if isinstance(task_result, dict) else None

            video_url = (
                task_data.get("video_url")
                or task_data.get("output", {}).get("video_url")
            )
            if not video_url and tr_videos and isinstance(tr_videos, list):
                first = tr_videos[0]
                video_url = first.get("url") if isinstance(first, dict) else first
            if not video_url:
                works = task_data.get("works")
                if isinstance(works, list) and works:
                    video_url = works[0].get("resource") if isinstance(works[0], dict) else None
            if not video_url:
                videos = task_data.get("videos") or task_data.get("output", {}).get("videos")
                if isinstance(videos, list) and videos:
                    video_url = videos[0].get("url") if isinstance(videos[0], dict) else videos[0]

            if video_url:
                result["video_url"] = video_url

            return result

        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from None
        except httpx.RequestError:
            raise KlingClientError(
                "MIRA lost connection while checking your motion result. "
                "Please try again."
            ) from None

    async def generate_and_wait(
        self,
        image_url: str,
        prompt: str,
        duration: float = 5.0,
        mode: Optional[str] = None,
        timeout: int = 300,
    ) -> dict:
        """Generate a motion video and poll until the result is ready.

        This is the recommended high-level method. It starts a generation
        task, polls every 5 seconds, and returns the final result.

        Parameters
        ----------
        image_url:
            Publicly accessible URL of the source image.
        prompt:
            Text prompt describing the desired motion.
        duration:
            Video duration in seconds (default 5.0).
        mode:
            ``"standard"`` or ``"professional"``.
        timeout:
            Maximum seconds to wait before giving up (default 300).

        Returns
        -------
        dict
            ``{"status": str, "video_url": str, "processing_time_ms": int}``
        """
        start = time.monotonic()

        task = await self.generate_motion(
            image_url,
            prompt,
            duration,
            mode or self.default_mode,
        )
        task_id = task["task_id"]

        while True:
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                raise KlingClientError(
                    "Your motion generation is taking longer than expected. "
                    "Please try again — MIRA apologises for the wait."
                )

            # Video generation is slower than image processing — poll
            # every 5 seconds to be respectful of the API.
            await asyncio.sleep(5)

            result = await self.get_task_status(task_id)
            status = result.get("status", "unknown")

            if status in ("completed", "succeed"):
                processing_time_ms = int((time.monotonic() - start) * 1000)
                return {
                    "status": "completed",
                    "video_url": result.get("video_url", ""),
                    "processing_time_ms": processing_time_ms,
                }

            if status in ("failed", "error"):
                error_code = result.get("error_code")
                error_message = result.get("error_message") or "The motion generation task failed."
                if error_code:
                    error_message = f"{error_code}: {error_message}"
                raise KlingClientError(
                    f"Kling could not complete this motion request. {error_message}"
                )

            # Any other status (submitted, processing, queued, …) → keep polling.

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _normalize_media_input(value: str) -> str:
        """Convert data URLs into the raw base64 format Kling expects."""
        if value.startswith("data:image/") and "," in value:
            return value.split(",", 1)[1]
        return value

    def _validate_mode(self, mode: str) -> str:
        mode = mode.strip().lower()
        aliases = {
            "standard": "std",
            "professional": "pro",
        }
        mode = aliases.get(mode, mode)
        if mode not in self.VALID_MODES:
            raise KlingClientError(
                f"MIRA does not recognise the generation mode '{mode}'. "
                f"Please choose from: {', '.join(sorted(self.VALID_MODES))}."
            )
        return mode

    @staticmethod
    def _map_http_error(exc: httpx.HTTPStatusError) -> KlingClientError:
        """Translate raw HTTP errors into premium, user-facing messages."""
        code = exc.response.status_code
        body_error = ""
        body_message = ""
        try:
            payload = exc.response.json()
            if isinstance(payload, dict):
                raw_error = payload.get("error")
                if isinstance(raw_error, dict):
                    body_error = str(raw_error.get("code") or raw_error.get("name") or "")
                    body_message = str(raw_error.get("message") or "")
                else:
                    body_error = str(raw_error or "")
                body_message = body_message or str(payload.get("message") or payload.get("msg") or "")
        except ValueError:
            pass

        combined = f"{body_error} {body_message}".strip().lower()

        if code == 401:
            return KlingClientError(
                body_message
                or "MIRA's motion generation credentials are invalid. "
                "Please contact support.",
                status_code=code,
            )
        if code == 400:
            return KlingClientError(
                body_message or "Kling rejected this motion request.",
                status_code=code,
            )
        if code == 403:
            return KlingClientError(
                body_message or "Kling refused this request. The key may not have permission for this model or feature.",
                status_code=code,
            )
        if code == 404:
            return KlingClientError(
                body_message or "Kling could not find the requested motion resource or model.",
                status_code=code,
            )
        if code == 422:
            return KlingClientError(
                body_message
                or "The image or prompt could not be processed. Please ensure "
                "the image is clear and the prompt is descriptive.",
                status_code=code,
            )
        if code == 429:
            if "credit" in combined or "quota" in combined or "balance" in combined:
                return KlingClientError(
                    body_message or "Kling has no credits remaining for this account.",
                    status_code=code,
                )
            return KlingClientError(
                body_message
                or "MIRA's motion generation service is experiencing high demand. "
                "Please wait a moment and try again.",
                status_code=code,
            )
        if 500 <= code < 600:
            return KlingClientError(
                body_message
                or "The motion generation service is temporarily unavailable. "
                "MIRA will be back shortly — please try again soon.",
                status_code=code,
            )

        return KlingClientError(
            body_message
            or "Something unexpected happened during your motion generation. "
            "Please try again or contact MIRA support.",
            status_code=code,
        )
