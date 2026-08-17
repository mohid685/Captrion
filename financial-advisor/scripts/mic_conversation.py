"""
Local dev script: continuous conversation with the financial advisor,
either by typing (fast iteration) or speaking (full pipeline test).
Press Ctrl+C or type "exit" to end the session.

Usage:
    python scripts/mic_conversation.py --ticker AAPL --email you@example.com --password yourpassword --input text
    python scripts/mic_conversation.py --ticker AAPL --email you@example.com --password yourpassword --input mic
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
SILENCE_HANG_SECONDS = 1.0
MAX_RECORD_SECONDS = 25
MIN_SPEECH_SECONDS = 0.3


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))


def elapsed_speech(frames: list[np.ndarray]) -> float:
    return sum(len(f) for f in frames) / SAMPLE_RATE


def calibrate_threshold() -> float:
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=FRAME_SAMPLES) as stream:
        for _ in range(16):
            chunk, _ = stream.read(FRAME_SAMPLES)
            frames.append(chunk.copy())
    ambient = max(_rms(c) for c in frames)
    return max(ambient * 3, 0.001)


def record_with_vad(output_path: Path) -> bool:
    threshold = calibrate_threshold()

    print(f"Listening... (threshold: {threshold:.5f})")
    frames: list[np.ndarray] = []
    pre_roll: collections.deque[np.ndarray] = collections.deque(maxlen=8)
    speech_started = False
    silence_start: float | None = None
    start_time = time.time()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=FRAME_SAMPLES) as stream:
        while True:
            chunk, _ = stream.read(FRAME_SAMPLES)
            chunk_copy = chunk.copy()
            level = _rms(chunk)
            elapsed = time.time() - start_time

            if level > threshold:
                if not speech_started:
                    print("Got it — recording...")
                    frames.extend(pre_roll)
                speech_started = True
                silence_start = None
                frames.append(chunk_copy)
            elif speech_started:
                frames.append(chunk_copy)
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_HANG_SECONDS:
                    break
            else:
                pre_roll.append(chunk_copy)

            if elapsed > MAX_RECORD_SECONDS:
                break

    if not speech_started or elapsed_speech(frames) < MIN_SPEECH_SECONDS:
        print("Didn't catch that — try again.")
        return False

    audio = np.concatenate(frames, axis=0)
    sf.write(str(output_path), audio, SAMPLE_RATE)
    print(f"Done — captured {elapsed_speech(frames):.1f}s. Sending...")
    return True


def get_token(api_url: str, email: str, password: str) -> str:
    response = requests.post(f"{api_url}/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        response = requests.post(f"{api_url}/auth/register", json={"email": email, "password": password})
        response.raise_for_status()
    return response.json()["access_token"]


def ask_voice_from_audio(
    api_url: str, ticker: str, token: str, audio_path: Path, history: list[dict[str, str]]
) -> dict | None:
    with open(audio_path, "rb") as f:
        response = requests.post(
            f"{api_url}/voice/transcribe",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": f},
        )
    if response.status_code != 200:
        print(f"STT error ({response.status_code}): {_error_detail(response)}")
        return None

    question = response.json()["transcribed_question"]
    return ask_with_question(api_url, ticker, token, question, history)


def ask_with_question(
    api_url: str, ticker: str, token: str, question: str, history: list[dict[str, str]]
) -> dict | None:
    payload = {
        "fallback_ticker": ticker,
        "question": question,
        "conversation_history": json.dumps(history),
    }
    response = requests.post(f"{api_url}/voice/respond", headers={"Authorization": f"Bearer {token}"}, data=payload)
    if response.status_code != 200:
        print(f"Pipeline error ({response.status_code}): {_error_detail(response)}")
        return None

    result = response.json()
    result.setdefault("transcribed_question", question)
    return result


def _error_detail(response: requests.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except Exception:
        return response.text


def play_audio_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))
    else:
        import subprocess

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, str(path)], check=False)


def _heartbeat(stop_event: threading.Event) -> None:
    elapsed = 0
    while not stop_event.is_set():
        time.sleep(3)
        if stop_event.is_set():
            break
        elapsed += 3
        print(f"  ...working ({elapsed}s)")


def _run_turn(get_result_fn) -> dict | None:
    """Wraps a turn (mic or typed) with the heartbeat + timing display."""
    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(target=_heartbeat, args=(stop_event,), daemon=True)
    heartbeat_thread.start()
    try:
        return get_result_fn()
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Conversation with the financial advisor")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--input",
        choices=["text", "mic"],
        default="text",
        help="'text' (default) to type questions for fast iteration, 'mic' for real voice-in testing",
    )
    args = parser.parse_args()

    print("Authenticating...")
    token = get_token(args.api_url, args.email, args.password)
    print("Authenticated.\n")

    history: list[dict[str, str]] = []
    mode_note = "Type your question and press Enter (type 'exit' to quit)." if args.input == "text" else "Speak when ready."
    print(f"Conversation started for {args.ticker.upper()}. {mode_note}\n")

    try:
        while True:
            if args.input == "text":
                question = input("You: ").strip()
                if not question:
                    continue
                if question.lower() in {"exit", "quit"}:
                    break
                result = _run_turn(lambda: ask_with_question(args.api_url, args.ticker, token, question, history))
            else:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    question_audio_path = Path(tmp_dir) / "question.wav"
                    if not record_with_vad(question_audio_path):
                        continue
                    result = _run_turn(
                        lambda: ask_voice_from_audio(args.api_url, args.ticker, token, question_audio_path, history)
                    )

            if result is None:
                print()
                continue

            if args.input == "mic":
                print(f"\nYou said: {result['transcribed_question']}")

            if result.get("data_gathered"):
                print("Gathering data:")
                for line in result["data_gathered"]:
                    print(f"  - {line}")

            print(f"\nAdvisor ({result['ticker']}): {result['reply_text']}\n")

            history.append({"question": result["transcribed_question"], "answer": result["reply_text"]})

            if result.get("answer_audio_file"):
                play_audio_file(Path(result["answer_audio_file"]))
            elif result.get("tts_error"):
                print(f"(voice synthesis failed: {result['tts_error']})")

            print("---\n")
    except KeyboardInterrupt:
        pass

    print("\nConversation ended.")


if __name__ == "__main__":
    main()