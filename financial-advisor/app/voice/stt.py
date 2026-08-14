"""
Speech-to-text via OpenAI's Whisper (original, Hugging Face transformers
pipeline — not Faster-Whisper). Decodes uploaded audio bytes, resamples
to 16kHz (what Whisper expects), and transcribes.
"""

from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import Any

import librosa

from app.config import get_settings

logger = logging.getLogger(__name__)

WHISPER_SAMPLE_RATE = 16000
MAX_AUDIO_DURATION_SECONDS = 120
MIN_TRANSCRIPTION_LENGTH = 3


class STTError(Exception):
    """Raised when audio can't be decoded or transcribed usefully."""


@lru_cache
def _get_whisper_pipeline() -> Any:
    from transformers import pipeline

    settings = get_settings()
    return pipeline("automatic-speech-recognition", model=settings.whisper_model_name)


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Decodes audio bytes and transcribes with Whisper.

    Raises STTError if the audio can't be decoded, exceeds the duration
    cap, or produces a suspiciously short/empty transcription (likely
    silence or unintelligible audio).
    """
    try:
        audio_array, _ = librosa.load(io.BytesIO(audio_bytes), sr=WHISPER_SAMPLE_RATE, mono=True)
    except Exception as exc:
        raise STTError(f"Could not decode audio file: {exc}") from exc

    duration_seconds = len(audio_array) / WHISPER_SAMPLE_RATE
    if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
        raise STTError(
            f"Audio is {duration_seconds:.0f}s long, exceeding the "
            f"{MAX_AUDIO_DURATION_SECONDS}s limit"
        )
    if duration_seconds < 0.3:
        raise STTError("Audio is too short to transcribe")

    # Reject near-silent clips outright — low-energy audio is where Whisper
    # tends to hallucinate garbage output. Use both RMS and peak so
    # short speech bursts are not incorrectly rejected.
    rms_energy = float((audio_array.astype("float64") ** 2).mean() ** 0.5)
    peak_energy = float(abs(audio_array).max()) if len(audio_array) else 0.0
    if rms_energy < 0.0005 and peak_energy < 0.01:
        raise STTError("Audio appears to be silence or too quiet to transcribe")

    asr = _get_whisper_pipeline()
    result = asr(
        {"array": audio_array, "sampling_rate": WHISPER_SAMPLE_RATE},
        generate_kwargs={"language": "en", "task": "transcribe"},
    )
    text = result.get("text", "").strip()

    if len(text) < MIN_TRANSCRIPTION_LENGTH:
        raise STTError(
            "Transcription produced little or no text — audio may be silent or unintelligible"
        )

    return text