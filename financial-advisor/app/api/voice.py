import base64
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agentic.agent import ask_agentic_advisor
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


@router.post("/{ticker}/ask")
async def voice_ask(
    ticker: str,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    audio_bytes = await audio.read()

    try:
        question = transcribe_audio(audio_bytes)
    except STTError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    user_context = _build_user_context(current_user, ticker, db)
    try:
        result = ask_agentic_advisor(ticker, question, user_context=user_context)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    conversation_id = _log_conversation(db, current_user.id, ticker, question, result["answer"], "voice")

    audio_base64: str | None = None
    audio_file_path: str | None = None
    tts_error: str | None = None
    try:
        answer_audio = synthesize_speech(result["answer"])
        audio_base64 = base64.b64encode(answer_audio).decode("utf-8")

        file_path = AUDIO_RESPONSES_DIR / f"{conversation_id}.mp3"
        file_path.write_bytes(answer_audio)
        audio_file_path = str(file_path)
    except TTSError as exc:
        logger.warning("TTS synthesis failed, returning text-only response: %s", exc)
        tts_error = str(exc)

    return {
        "ticker": result["ticker"],
        "transcribed_question": question,
        "answer_text": result["answer"],
        "answer_audio_base64": audio_base64,
        "answer_audio_file": audio_file_path,
        "tts_error": tts_error,
        "tool_calls_made": result.get("tool_calls_made", []),
    }