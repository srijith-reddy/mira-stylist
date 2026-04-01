"""
MIRA Stylist — Environment Configuration

Centralised settings powered by pydantic-settings.
All secrets and tunables are loaded from environment variables or a `.env`
file located in the backend root directory.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Application-wide configuration.

    Values are resolved in the following order (highest precedence first):
    1. Explicit environment variables
    2. Entries in the `.env` file
    3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "MIRA Stylist"
    DEBUG: bool = False
    USER_NAME: str = ""

    # ── FASHN Virtual Try-On ─────────────────────────────────────────────
    FASHN_API_KEY: str = ""
    FASHN_API_URL: str = "https://api.fashn.ai/v1"
    FASHN_MODEL: str = "tryon-v1.6"
    FASHN_MODE: str = "quality"

    # ── Kling AI (video / image generation) ──────────────────────────────
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""
    KLING_API_URL: str = "https://api-singapore.klingai.com"
    KLING_MODEL: str = "kling-v2-5-turbo"
    KLING_MODE: str = "pro"

    # ── OpenAI (commentary, Whisper transcription) ───────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    WHISPER_MODEL: str = "whisper-1"

    # ── Cartesia (voice TTS) ─────────────────────────────────────────────
    CARTESIA_API_KEY: str = ""
    CARTESIA_VOICE: str = ""

    # ── Audio pipeline settings ──────────────────────────────────────────
    RATE: int = 16000
    CHANNELS: int = 1
    BLOCK_SIZE: int = 320
    VAD_AGGRESSIVENESS: int = 2
    STOP_MS: int = 2000
    TAIL_MS: int = 100
    DEVICE: str = ""

    # ── Storage ──────────────────────────────────────────────────────────
    DATA_DIR: str = "output/mira_stylist"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"])

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalise_debug(cls, value):
        """Treat non-boolean DEBUG values like 'release' as False."""
        if isinstance(value, str):
            normalised = value.strip().lower()
            if normalised in {"release", "prod", "production"}:
                return False
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    The result is cached so that the `.env` file is read only once and every
    caller receives the same object.
    """
    return Settings()
