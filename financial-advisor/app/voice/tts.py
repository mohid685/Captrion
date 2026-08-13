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
        "speech_model": "mars-pro",
        "output_configuration": {"format": "mp3"},
}

    try:
        response = requests.post(CAMB_TTS_URL, headers=headers, json=payload, timeout=60)
    except requests.exceptions.RequestException as exc:
        logger.exception("camb.ai TTS request failed")
        raise TTSError(f"camb.ai TTS request failed: {exc}") from exc

    if response.status_code != 200:
        logger.error("camb.ai TTS returned status %s: %s", response.status_code, response.text[:300])
        raise TTSError(f"camb.ai TTS returned status {response.status_code}: {response.text[:300]}")

    if not response.content:
        raise TTSError("camb.ai TTS returned an empty audio response")

    return response.content