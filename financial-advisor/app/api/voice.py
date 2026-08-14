import base64
import json
import logging
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.advisor import _build_user_context, _log_conversation
from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.llm_client import LLMClientError
from app.core.vector_store import VectorStoreError
from app.reasoning.advisor import ask_advisor_voice
from app.models.user import User
from app.voice.stt import STTError, transcribe_audio
from app.voice.tts import TTSError, synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

AUDIO_RESPONSES_DIR = Path("audio_responses")
AUDIO_RESPONSES_DIR.mkdir(exist_ok=True)
MAX_TTS_CHARS = 480

_COMPANY_TO_TICKER: dict[str, str] = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "meta": "META",
    "netflix": "NFLX",
    "amd": "AMD",
    "broadcom": "AVGO",
    "intel": "INTC",
    "spy": "SPY",
    "s&p": "SPY",
}


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


def _extract_ticker(question: str) -> str | None:
    lowered = question.lower()
    for name, ticker in _COMPANY_TO_TICKER.items():
        if name in lowered:
            return ticker

    symbols = re.findall(r"\b[A-Z]{1,5}\b", question)
    for symbol in symbols:
        if symbol not in {"I", "A", "AN", "THE", "AND", "OR", "TO", "FOR"}:
            return symbol
    return None


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
    extracted_ticker = _extract_ticker(question)
    resolved_ticker = (extracted_ticker or fallback_ticker).upper()

    user_context = _build_user_context(current_user, resolved_ticker, db)
    try:
        result = ask_advisor_voice(resolved_ticker, question, user_context=user_context)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    conversation_id = _log_conversation(
        db,
        current_user.id,
        resolved_ticker,
        question,
        result["answer"],
        "voice",
    )

    audio_base64, audio_file_path, tts_error = _synthesize_reply_audio(conversation_id, result["answer"])

    return {
        "ticker": resolved_ticker,
        "transcribed_question": question,
        "reply_text": result["answer"],
        "answer_audio_base64": audio_base64,
        "answer_audio_file": audio_file_path,
        "tts_error": tts_error,
        "detected_ticker": extracted_ticker,
        "conversation_history_used": len(history),
        "sources_used": result.get("sources_used", []),
        "sentiment_analysis": result.get("sentiment_analysis"),
        "ml_signals": result.get("ml_signals"),
    }


@router.post("/transcribe")
def voice_transcribe(audio: UploadFile = File(...)) -> dict[str, Any]:
    audio_bytes = audio.file.read()
    try:
        question = transcribe_audio(audio_bytes)
    except STTError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "transcribed_question": question,
        "detected_ticker": _extract_ticker(question),
    }


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