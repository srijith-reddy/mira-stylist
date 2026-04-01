"""
MIRA Stylist — Voice Service

Text-to-speech synthesis using the Cartesia API.
Gives MIRA a calm, warm, elegant speaking voice for welcome greetings,
stylist commentary narration, and general guidance.

Transcription (speech-to-text) uses OpenAI Whisper.
"""

from __future__ import annotations

import inspect
import uuid
from pathlib import Path
from typing import BinaryIO

import openai

from ..models.schemas import VoiceRequest, VoiceResponse, VoiceStyle
from ..utils.env import get_settings

try:
    from cartesia import AsyncCartesia  # type: ignore
    _CARTESIA_AVAILABLE = True
except ImportError:
    _CARTESIA_AVAILABLE = False


# Cartesia model to use for all TTS
_CARTESIA_MODEL = "sonic-2"

# Output format: MP3 @ 44 100 Hz
_OUTPUT_FORMAT = {
    "container": "mp3",
    "encoding": "mp3",
    "sample_rate": 44100,
}


class VoiceService:
    """MIRA's voice — calm, warm, elegant, poised.

    Uses Cartesia's Sonic TTS model to generate high-fidelity speech audio.
    Falls back gracefully when the API key is not configured.
    Audio files are persisted under ``{DATA_DIR}/voice/`` so they can be
    served or streamed to the client.

    Speech-to-text (transcription) is handled by OpenAI Whisper.
    """

    def __init__(self) -> None:
        settings = get_settings()

        # ── Cartesia (TTS) ────────────────────────────────────────────────
        self._cartesia_key = settings.CARTESIA_API_KEY
        self._cartesia_voice_id = settings.CARTESIA_VOICE
        self._cartesia_client: "AsyncCartesia | None" = (
            AsyncCartesia(api_key=self._cartesia_key)
            if (_CARTESIA_AVAILABLE and self._cartesia_key)
            else None
        )

        # ── OpenAI Whisper (STT) ──────────────────────────────────────────
        self._openai_client: openai.AsyncOpenAI | None = (
            openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            if settings.OPENAI_API_KEY
            else None
        )
        self._whisper_model = settings.WHISPER_MODEL

        # ── Storage ───────────────────────────────────────────────────────
        self.output_dir = Path(settings.DATA_DIR) / "voice"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ── User personalisation ──────────────────────────────────────────
        self._user_name: str = settings.USER_NAME

    # ------------------------------------------------------------------
    # TTS — Synthesis
    # ------------------------------------------------------------------

    async def synthesize(self, request: VoiceRequest) -> VoiceResponse:
        """Generate speech audio from text via Cartesia Sonic.

        Parameters
        ----------
        request:
            A :class:`VoiceRequest` containing the text, voice style, and
            playback speed.

        Returns
        -------
        VoiceResponse
            Contains the path to the generated audio file and its
            approximate duration.

        Raises
        ------
        ValueError
            If Cartesia is not configured or the cartesia package is missing.
        """
        if not self._cartesia_client:
            raise ValueError(
                "Voice mode requires a Cartesia API key to be configured. "
                "Please add CARTESIA_API_KEY to your environment."
            )
        if not self._cartesia_voice_id:
            raise ValueError(
                "A Cartesia voice ID must be configured via CARTESIA_VOICE."
            )

        audio_bytes: bytes = await self._cartesia_client.tts.bytes(
            model_id=_CARTESIA_MODEL,
            transcript=request.text,
            voice={"id": self._cartesia_voice_id},
            output_format=_OUTPUT_FORMAT,
        )
        if inspect.isasyncgen(audio_bytes) or hasattr(audio_bytes, "__aiter__"):
            chunks: list[bytes] = []
            async for chunk in audio_bytes:
                chunks.append(chunk)
            audio_bytes = b"".join(chunks)

        filename = f"{uuid.uuid4().hex}.mp3"
        audio_path = self.output_dir / filename
        audio_path.write_bytes(audio_bytes)

        # Estimate duration: ~150 words/min at 1× speed.
        word_count = len(request.text.split())
        duration_seconds = round(
            (word_count / 150.0) * 60.0 / request.speed, 2
        )

        return VoiceResponse(
            audio_url=f"/media/voice/{filename}",
            duration_seconds=duration_seconds,
        )

    # ------------------------------------------------------------------
    # STT — Transcription (Whisper)
    # ------------------------------------------------------------------

    async def transcribe(self, audio_file: BinaryIO, filename: str = "audio.webm") -> str:
        """Transcribe an audio file using OpenAI Whisper.

        Parameters
        ----------
        audio_file:
            A file-like object containing the audio data.
        filename:
            The original filename (used for MIME-type inference by the API).

        Returns
        -------
        str
            The transcribed text.

        Raises
        ------
        ValueError
            If OpenAI is not configured.
        """
        if not self._openai_client:
            raise ValueError(
                "Transcription requires an OpenAI API key (OPENAI_API_KEY)."
            )

        response = await self._openai_client.audio.transcriptions.create(
            model=self._whisper_model,
            file=(filename, audio_file),
        )
        return response.text

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    async def generate_welcome(
        self, user_name: str | None = None
    ) -> VoiceResponse:
        """Generate a warm, personalised welcome message.

        Uses USER_NAME from settings if no *user_name* is passed.
        """
        name = user_name or self._user_name or None
        if name:
            text = (
                f"Welcome back, {name}. "
                "Let's find something beautiful today."
            )
        else:
            text = (
                "Welcome to MIRA. "
                "I'm here to help you discover your most refined look."
            )
        return await self.synthesize(
            VoiceRequest(text=text, voice_style=VoiceStyle.WARM)
        )

    async def narrate_commentary(
        self, commentary_text: str
    ) -> VoiceResponse:
        """Narrate stylist commentary in an editorial voice."""
        return await self.synthesize(
            VoiceRequest(
                text=commentary_text, voice_style=VoiceStyle.EDITORIAL
            )
        )
