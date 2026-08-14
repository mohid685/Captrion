"""
Local dev script: continuous voice conversation with the financial
advisor. Auto-detects when you stop speaking (no more pressing Enter),
sends each turn with running conversation history, and plays back the
spoken reply. Press Ctrl+C to end the session.

Usage:
    python scripts/mic_conversation.py --ticker AAPL --email you@example.com --password yourpassword
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import threading


SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
# SILENCE_RMS_THRESHOLD = 0.02  # was 0.01 — raised to reduce false-positive speech detection on background noise
SILENCE_HANG_SECONDS = 1.2
MAX_RECORD_SECONDS = 25
MIN_SPEECH_SECONDS = 0.4


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))


def record_with_vad(output_path: Path) -> bool:
    """
    Calibrates against ambient noise, then records until silence is
    detected after speech has started, or the max duration cap is hit.
    Returns False if nothing was captured.
    """
    print("Calibrating mic (stay quiet for a moment)...")
    calibration_frames: list[np.ndarray] = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=FRAME_SAMPLES) as stream:
        for _ in range(15):  # ~450ms of ambient noise sample
            chunk, _ = stream.read(FRAME_SAMPLES)
            calibration_frames.append(chunk.copy())

    ambient_level = max(_rms(c) for c in calibration_frames)
    threshold = max(ambient_level * 2.5, 0.003)  # speech must clearly exceed ambient noise
    print(f"Ambient level: {ambient_level:.5f} -> speech threshold: {threshold:.5f}")

    print("Listening... (speak now, I'll stop automatically when you pause)")
    frames: list[np.ndarray] = []
    speech_started = False
    silence_start: float | None = None
    start_time = time.time()
    last_print = 0.0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=FRAME_SAMPLES) as stream:
        while True:
            chunk, _ = stream.read(FRAME_SAMPLES)
            frames.append(chunk.copy())
            level = _rms(chunk)
            elapsed = time.time() - start_time

            if elapsed - last_print > 1.0:
                print(f"  (level: {level:.5f}{' - SPEAKING' if level > threshold else ''})")
                last_print = elapsed

            if level > threshold:
                speech_started = True
                silence_start = None
            elif speech_started:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_HANG_SECONDS:
                    break

            if elapsed > MAX_RECORD_SECONDS:
                break

    if not speech_started or elapsed_speech(frames) < MIN_SPEECH_SECONDS:
        print("Didn't catch that — no speech detected.")
        return False

    audio = np.concatenate(frames, axis=0)
    sf.write(str(output_path), audio, SAMPLE_RATE)
    return True

def elapsed_speech(frames: list[np.ndarray]) -> float:
    total_samples = sum(len(f) for f in frames)
    return total_samples / SAMPLE_RATE


def get_token(api_url: str, email: str, password: str) -> str:
    response = requests.post(f"{api_url}/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        response = requests.post(f"{api_url}/auth/register", json={"email": email, "password": password})
        response.raise_for_status()
    return response.json()["access_token"]


def ask_voice(
    api_url: str, ticker: str, token: str, audio_path: Path, history: list[dict[str, str]]
) -> dict:
    with open(audio_path, "rb") as f:
        response = requests.post(
            f"{api_url}/voice/{ticker}/ask",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": f},
            data={"conversation_history": json.dumps(history)},
        )
    response.raise_for_status()
    return response.json()


def play_audio_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))
    else:
        import subprocess

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, str(path)], check=False)


def _heartbeat(stop_event: threading.Event, label: str) -> None:
    """Prints a dot every 3 seconds so long waits don't look frozen."""
    elapsed = 0
    while not stop_event.is_set():
        time.sleep(3)
        if stop_event.is_set():
            break
        elapsed += 3
        print(f"  ...{label} ({elapsed}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuous voice conversation with the financial advisor")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print("Authenticating...")
    token = get_token(args.api_url, args.email, args.password)
    print("Authenticated.\n")

    history: list[dict[str, str]] = []
    print(f"Conversation started for {args.ticker.upper()}. Press Ctrl+C to end.\n")

    try:
        while True:
            with tempfile.TemporaryDirectory() as tmp_dir:
                question_audio_path = Path(tmp_dir) / "question.wav"

                if not record_with_vad(question_audio_path):
                    continue

                print("Got your message. Sending to the advisor pipeline...")

                stop_event = threading.Event()
                heartbeat_thread = threading.Thread(
                    target=_heartbeat, args=(stop_event, "waiting on pipeline (transcribing, reasoning, and generating voice)"), daemon=True
                )
                heartbeat_thread.start()

                try:
                    result = ask_voice(args.api_url, args.ticker, token, question_audio_path, history)
                finally:
                    stop_event.set()
                    heartbeat_thread.join(timeout=1)

                print(f"\nYou said: {result['transcribed_question']}")
                print(f"Advisor: {result['reply_text']}\n")

                history.append({"question": result["transcribed_question"], "answer": result["reply_text"]})

                if result.get("answer_audio_file"):
                    print("Playing response audio...")
                    play_audio_file(Path(result["answer_audio_file"]))
                elif result.get("tts_error"):
                    print(f"(voice synthesis failed: {result['tts_error']})")

                print("---\n")
    except KeyboardInterrupt:
        print("\nConversation ended.")


if __name__ == "__main__":
    main()