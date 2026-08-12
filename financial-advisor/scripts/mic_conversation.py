"""
Local dev script: record a question from your microphone, send it to
the voice advisor endpoint, and play back the spoken answer.

Not part of the deployed API — this simulates what a future frontend
will do client-side (record in-browser, POST to /voice/{ticker}/ask,
play the returned audio).

Usage:
    python scripts/mic_conversation.py --ticker AAPL --email you@example.com --password yourpassword
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import tempfile
import threading
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000


def record_until_enter(output_path: Path) -> None:
    print("Recording... press Enter to stop.")
    frames: list[np.ndarray] = []
    recording = True

    def callback(indata: np.ndarray, frame_count: int, time_info, status) -> None:
        if recording:
            frames.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback)
    stream.start()
    input()
    recording = False
    stream.stop()
    stream.close()

    if not frames:
        print("No audio captured.")
        sys.exit(1)

    audio = np.concatenate(frames, axis=0)
    sf.write(str(output_path), audio, SAMPLE_RATE)
    print(f"Recorded {len(audio) / SAMPLE_RATE:.1f}s of audio.")


def get_token(api_url: str, email: str, password: str) -> str:
    response = requests.post(f"{api_url}/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        # Try registering if login failed — convenient for first-time use.
        response = requests.post(f"{api_url}/auth/register", json={"email": email, "password": password})
        response.raise_for_status()
    return response.json()["access_token"]


def ask_voice(api_url: str, ticker: str, token: str, audio_path: Path) -> dict:
    with open(audio_path, "rb") as f:
        response = requests.post(
            f"{api_url}/voice/{ticker}/ask",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": f},
        )
    response.raise_for_status()
    return response.json()


def play_audio_file(path: Path) -> None:
    print(f"Playing response: {path}")
    if sys.platform == "win32":
        os.startfile(str(path))  # opens in the default media player
    else:
        import subprocess

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, str(path)], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mic-in voice conversation with the financial advisor")
    parser.add_argument("--ticker", required=True, help="Stock ticker, e.g. AAPL")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        question_audio_path = Path(tmp_dir) / "question.wav"
        record_until_enter(question_audio_path)

        print("Authenticating...")
        token = get_token(args.api_url, args.email, args.password)

        print("Sending to advisor...")
        result = ask_voice(args.api_url, args.ticker, token, question_audio_path)

        print(f"\nYou asked: {result['transcribed_question']}")
        print(f"\nAnswer:\n{result['answer_text']}\n")

        if result.get("answer_audio_file"):
            play_audio_file(Path(result["answer_audio_file"]))
        elif result.get("tts_error"):
            print(f"(Voice synthesis failed: {result['tts_error']} — text answer shown above)")


if __name__ == "__main__":
    main()