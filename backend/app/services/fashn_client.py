"""
MIRA Stylist — FASHN Virtual Try-On Client

Async client for the FASHN API (https://api.fashn.ai/v1).
Handles prediction creation, status polling, and graceful error handling
with premium user-facing messages.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx

from ..utils.env import get_settings


class FashnClientError(Exception):
    """Raised when a FASHN API operation fails.

    Only premium, user-friendly messages are surfaced — raw API details
    are logged but never exposed to the caller.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class FashnClient:
    """Async client for the FASHN virtual try-on API.

    Usage::

        async with FashnClient(api_key="...") as client:
            result = await client.run_tryon_and_wait(person_url, garment_url)
            print(result["output_image_url"])
    """

    # Valid garment categories accepted by the FASHN API.
    VALID_CATEGORIES = {"tops", "bottoms", "one-pieces", "auto"}
    VALID_MODES = {"performance", "balanced", "quality"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.FASHN_API_KEY
        self.base_url = (base_url or settings.FASHN_API_URL).rstrip("/")
        self.model_name = settings.FASHN_MODEL
        self.mode = self._validate_mode(settings.FASHN_MODE)

        if not self.api_key:
            raise FashnClientError(
                "MIRA cannot connect to the virtual try-on service right now. "
                "Please ensure your FASHN API key is configured."
            )

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    # ── Context-manager support ─────────────────────────────────────────

    async def __aenter__(self) -> "FashnClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    # ── Public API ──────────────────────────────────────────────────────

    async def run_tryon(
        self,
        person_image_url: str,
        garment_image_url: str,
        category: str = "auto",
    ) -> dict:
        """Start a virtual try-on prediction.

        Parameters
        ----------
        person_image_url:
            Publicly accessible URL of the person / model photo.
        garment_image_url:
            Publicly accessible URL of the garment image.
        category:
            Garment category — ``"tops"``, ``"bottoms"``, ``"one-pieces"``,
            or ``"auto"`` (default) to let the API decide.

        Returns
        -------
        dict
            ``{"prediction_id": str, "status": str}`` on success.
        """
        category = self._validate_category(category)
        use_base64_io = person_image_url.startswith("data:image/") or garment_image_url.startswith("data:image/")

        payload = {
            "model_name": self.model_name,
            "inputs": {
                "model_image": person_image_url,
                "garment_image": garment_image_url,
                "category": category,
                "mode": self.mode,
                "return_base64": use_base64_io,
                "output_format": "png" if use_base64_io else None,
            },
        }
        if payload["inputs"]["output_format"] is None:
            payload["inputs"].pop("output_format")

        try:
            response = await self.client.post("/run", json=payload)
            response.raise_for_status()
            data = response.json()

            prediction_id = data.get("id") or data.get("prediction_id")
            if not prediction_id:
                raise FashnClientError(
                    "MIRA could not start your try-on session. "
                    "Please try again in a moment."
                )

            return {
                "prediction_id": prediction_id,
                "status": data.get("status", "starting"),
            }

        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from None
        except httpx.RequestError:
            raise FashnClientError(
                "MIRA is unable to reach the virtual try-on service. "
                "Please check your connection and try again."
            ) from None

    async def get_status(self, prediction_id: str) -> dict:
        """Get the current status of a prediction.

        Parameters
        ----------
        prediction_id:
            The identifier returned by :meth:`run_tryon`.

        Returns
        -------
        dict
            Contains ``status`` (``"starting"`` | ``"processing"`` |
            ``"completed"`` | ``"failed"``) and, when complete,
            ``output_image_url``.
        """
        try:
            response = await self.client.get(f"/status/{prediction_id}")
            response.raise_for_status()
            data = response.json()

            result: dict = {
                "prediction_id": prediction_id,
                "status": data.get("status", "unknown"),
            }
            error = data.get("error")
            if error:
                result["error"] = error
                if isinstance(error, dict):
                    result["error_name"] = error.get("name")
                    result["error_message"] = error.get("message")
                elif isinstance(error, str):
                    result["error_message"] = error

            # The FASHN API returns the output image in an "output" field
            # (may be a list or a direct URL string).
            output = data.get("output")
            if output:
                if isinstance(output, list) and len(output) > 0:
                    result["output_image_url"] = output[0]
                elif isinstance(output, str):
                    result["output_image_url"] = output

            return result

        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from None
        except httpx.RequestError:
            raise FashnClientError(
                "MIRA lost connection while checking your try-on result. "
                "Please try again."
            ) from None

    async def run_tryon_and_wait(
        self,
        person_image_url: str,
        garment_image_url: str,
        category: str = "auto",
        timeout: int = 120,
    ) -> dict:
        """Run a virtual try-on and poll until the result is ready.

        This is the recommended high-level method. It starts a prediction,
        polls every 2 seconds, and returns the final result.

        Parameters
        ----------
        person_image_url:
            Publicly accessible URL of the person / model photo.
        garment_image_url:
            Publicly accessible URL of the garment image.
        category:
            ``"tops"``, ``"bottoms"``, ``"one-pieces"``, or ``"auto"``.
        timeout:
            Maximum seconds to wait before giving up (default 120).

        Returns
        -------
        dict
            ``{"status": str, "output_image_url": str,
            "processing_time_ms": int}``
        """
        start = time.monotonic()

        prediction = await self.run_tryon(
            person_image_url, garment_image_url, category
        )
        prediction_id = prediction["prediction_id"]

        while True:
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                raise FashnClientError(
                    "Your virtual try-on is taking longer than expected. "
                    "Please try again — MIRA apologises for the wait."
                )

            await asyncio.sleep(2)

            result = await self.get_status(prediction_id)
            status = result.get("status", "unknown")

            if status == "completed":
                processing_time_ms = int((time.monotonic() - start) * 1000)
                return {
                    "status": "completed",
                    "output_image_url": result.get("output_image_url", ""),
                    "processing_time_ms": processing_time_ms,
                }

            if status == "failed":
                error_name = result.get("error_name")
                error_message = result.get("error_message") or "The try-on prediction failed."
                if error_name:
                    error_message = f"{error_name}: {error_message}"
                raise FashnClientError(
                    f"FASHN could not complete this try-on. {error_message}"
                )

            # Any other status (starting, processing, …) → keep polling.

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    # ── Internal helpers ────────────────────────────────────────────────

    def _validate_mode(self, mode: str) -> str:
        normalized = mode.strip().lower()
        if normalized not in self.VALID_MODES:
            raise FashnClientError(
                f"MIRA does not recognise the FASHN quality mode '{mode}'. "
                f"Please choose from: {', '.join(sorted(self.VALID_MODES))}."
            )
        return normalized

    def _validate_category(self, category: str) -> str:
        category = category.strip().lower()
        if category not in self.VALID_CATEGORIES:
            raise FashnClientError(
                f"MIRA does not recognise the garment category '{category}'. "
                f"Please choose from: {', '.join(sorted(self.VALID_CATEGORIES))}."
            )
        return category

    @staticmethod
    def _map_http_error(exc: httpx.HTTPStatusError) -> FashnClientError:
        """Translate raw HTTP errors into premium, user-facing messages."""
        code = exc.response.status_code
        body_error = ""
        body_message = ""
        try:
            payload = exc.response.json()
            if isinstance(payload, dict):
                raw_error = payload.get("error")
                if isinstance(raw_error, dict):
                    body_error = str(raw_error.get("name") or raw_error.get("code") or "")
                    body_message = str(raw_error.get("message") or "")
                else:
                    body_error = str(raw_error or "")
                body_message = body_message or str(payload.get("message") or "")
        except ValueError:
            pass

        combined = f"{body_error} {body_message}".strip().lower()

        if code == 401:
            return FashnClientError(
                "MIRA's try-on service credentials are invalid. "
                "Please contact support.",
                status_code=code,
            )
        if code == 400:
            message = body_message or "FASHN rejected the request format."
            return FashnClientError(
                f"FASHN rejected this try-on request. {message}",
                status_code=code,
            )
        if code == 422:
            return FashnClientError(
                body_message
                or "The images provided could not be processed. Please ensure "
                "they are clear, well-lit photos with a visible person or "
                "garment.",
                status_code=code,
            )
        if code == 429:
            if "outofcredits" in combined or "out of credits" in combined:
                return FashnClientError(
                    "FASHN has no API credits remaining on this key. Add credits and try again.",
                    status_code=code,
                )
            if "concurrency" in combined:
                return FashnClientError(
                    "FASHN already has too many try-ons running for this key. Please wait a moment and try again.",
                    status_code=code,
                )
            return FashnClientError(
                body_message
                or "MIRA's try-on service is experiencing high demand. "
                "Please wait a moment and try again.",
                status_code=code,
            )
        if 500 <= code < 600:
            return FashnClientError(
                body_message
                or "The virtual try-on service is temporarily unavailable. "
                "MIRA will be back shortly — please try again soon.",
                status_code=code,
            )

        return FashnClientError(
            body_message
            or "Something unexpected happened during your virtual try-on. "
            "Please try again or contact MIRA support.",
            status_code=code,
        )
