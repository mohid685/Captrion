import base64
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agentic.voice_agent import ask_voice_advisor
from app.api.advisor import _build_user_context, _log_conversation
from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.llm_client import LLMClientError
from app.models.user import User
from app.voice.stt import STTError, transcribe_audio
from app.voice.tts import TTSError, synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

AUDIO_RESPONSES_DIR = Path("audio_responses")
AUDIO_RESPONSES_DIR.mkdir(exist_ok=True)
MAX_TTS_CHARS = 480


def _parse_history(raw_history: str | None) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    if not raw_history:
        return history
    try:
        loaded = json.loads(raw_history)
    except json.JSONDecodeError:
        return history

    if isinstance(loaded, list):
        for item in loaded:
            if isinstance(item, dict) and "question" in item and "answer" in item:
                history.append({"question": str(item["question"]), "answer": str(item["answer"])})
    return history


def _synthesize_reply_audio(conversation_id: str, reply_text: str) -> tuple[str | None, str | None, str | None]:
    audio_base64: str | None = None
    audio_file_path: str | None = None
    tts_error: str | None = None

    safe_reply_text = reply_text.strip()
    if len(safe_reply_text) > MAX_TTS_CHARS:
        safe_reply_text = safe_reply_text[:MAX_TTS_CHARS].rsplit(" ", 1)[0].rstrip(".,;: ") + "."

    try:
        answer_audio = synthesize_speech(safe_reply_text)
        audio_base64 = base64.b64encode(answer_audio).decode("utf-8")

        file_path = AUDIO_RESPONSES_DIR / f"{conversation_id}.mp3"
        file_path.write_bytes(answer_audio)
        audio_file_path = str(file_path)
    except TTSError as exc:
        logger.warning("TTS synthesis failed, returning text-only response: %s", exc)
        tts_error = str(exc)

    return audio_base64, audio_file_path, tts_error


def _run_voice_pipeline(
    fallback_ticker: str,
    question: str,
    history: list[dict[str, str]],
    current_user: User,
    db: Session,
) -> dict[str, Any]:
    # No fragile pre-extraction — the agent resolves the actual company/ticker
    # itself via the SYMBOL_SEARCH tool if the question names something other
    # than the fallback ticker. fallback_ticker is only a hint, not a forced
    # substitution.
    user_context = _build_user_context(current_user, fallback_ticker, db)
    try:
        result = ask_voice_advisor(
            fallback_ticker,
            question,
            conversation_history=history,
            user_context=user_context,
        )
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    conversation_id = _log_conversation(
        db,
        current_user.id,
        result["ticker"],
        question,
        result["reply"],
        "voice",
    )

    audio_base64, audio_file_path, tts_error = _synthesize_reply_audio(conversation_id, result["reply"])

    return {
        "ticker": result["ticker"],
        "transcribed_question": question,
        "reply_text": result["reply"],
        "data_gathered": result.get("data_gathered", []),
        "answer_audio_base64": audio_base64,
        "answer_audio_file": audio_file_path,
        "tts_error": tts_error,
        "tool_calls_made": result.get("tool_calls_made", []),
    }


@router.post("/transcribe")
def voice_transcribe(audio: UploadFile = File(...)) -> dict[str, Any]:
    audio_bytes = audio.file.read()
    try:
        question = transcribe_audio(audio_bytes)
    except STTError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"transcribed_question": question}


@router.post("/respond")
def voice_respond(
    fallback_ticker: str = Form(...),
    question: str = Form(...),
    conversation_history: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    history = _parse_history(conversation_history)
    return _run_voice_pipeline(fallback_ticker, question, history, current_user, db)


@router.post("/{ticker}/ask")
def voice_ask(
    ticker: str,
    audio: UploadFile = File(...),
    conversation_history: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    audio_bytes = audio.file.read()

    try:
        question = transcribe_audio(audio_bytes)
    except STTError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    history = _parse_history(conversation_history)
    return _run_voice_pipeline(ticker, question, history, current_user, db)