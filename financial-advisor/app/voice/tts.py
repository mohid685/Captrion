"""
Text-to-speech via camb.ai's /tts-stream endpoint.
"""

from __future__ import annotations

import logging

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

CAMB_TTS_URL = "https://client.camb.ai/apis/tts-stream"


class TTSError(Exception):
    """Raised when speech synthesis fails."""


def synthesize_speech(text: str) -> bytes:
    """Synthesizes speech audio for the given text via camb.ai. Returns raw audio bytes."""
    settings = get_settings()
    if not settings.camb_api_key:
        raise TTSError("CAMB_API_KEY is not set. Add it to your .env file.")

    headers = {"x-api-key": settings.camb_api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "voice_id": settings.camb_voice_id,
        "language": "en-us",
        "speech_model": "mars-flash",  # fast model — priority is getting audio back quickly
        "output_configuration": {"format": "mp3"},
    }

    last_error: Exception | None = None
    response = None
    for attempt in range(2):
        try:
            response = requests.post(url=CAMB_TTS_URL, headers=headers, json=payload, timeout=(5, 25))
            break
        except requests.exceptions.RequestException as exc:
            logger.warning("camb.ai TTS attempt %d failed: %s", attempt + 1, exc)
            last_error = exc
    if response is None:
        raise TTSError(f"camb.ai TTS request failed after retries: {last_error}") from last_error

    if response.status_code != 200:
        logger.error("camb.ai TTS returned status %s: %s", response.status_code, response.text[:300])
        raise TTSError(f"camb.ai TTS returned status {response.status_code}: {response.text[:300]}")

    if not response.content:
        raise TTSError("camb.ai TTS returned an empty audio response")

    return response.content