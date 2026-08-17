"""
Text-to-speech via ElevenLabs, using the fast flash model for low latency.
"""

from __future__ import annotations

import logging

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TTSError(Exception):
    """Raised when speech synthesis fails."""


def synthesize_speech(text: str) -> bytes:
    """Synthesizes speech audio for the given text via ElevenLabs. Returns raw MP3 bytes."""
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise TTSError("ELEVENLABS_API_KEY is not set. Add it to your .env file.")
    if not settings.elevenlabs_voice_id:
        raise TTSError("ELEVENLABS_VOICE_ID is not set. Add it to your .env file.")

    url = ELEVENLABS_TTS_URL.format(voice_id=settings.elevenlabs_voice_id)
    headers = {"xi-api-key": settings.elevenlabs_api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model_id,
        "output_format": "mp3_44100_128",
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=(5, 15))
    except requests.exceptions.RequestException as exc:
        logger.warning("ElevenLabs TTS failed: %s", exc)
        raise TTSError(f"ElevenLabs TTS request failed: {exc}") from exc

    if response.status_code != 200:
        logger.error("ElevenLabs TTS returned status %s: %s", response.status_code, response.text[:300])
        raise TTSError(f"ElevenLabs TTS returned status {response.status_code}: {response.text[:300]}")

    if not response.content:
        raise TTSError("ElevenLabs TTS returned an empty audio response")

    return response.content