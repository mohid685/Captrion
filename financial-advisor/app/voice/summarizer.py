"""
Converts a full text answer into a short, natural-sounding spoken
summary suitable for TTS. camb.ai's free tier caps requests at 500
characters, and full advisor answers (markdown tables, citations,
disclaimers) run far longer — so this isn't just truncation, it's a
genuine rewrite: take the question + full answer, and produce what a
human analyst would actually *say out loud* if you asked them the
same thing in conversation.
"""

from __future__ import annotations

from app.core.llm_client import generate_response

MAX_VOICE_SUMMARY_CHARS = 450

VOICE_SUMMARY_SYSTEM_PROMPT = """You convert a detailed written financial analysis into a short, \
natural-sounding spoken reply, as if a knowledgeable friend were answering the question out loud \
in conversation.

Rules:
- Under 400 characters. This is a hard limit — be concise.
- No markdown, no tables, no bullet points, no special symbols (%, $, |, #, *, etc. should be \
spoken naturally instead, e.g. "twenty nine percent" or just keep numbers simple and readable).
- Natural spoken sentence flow — contractions are fine, it should sound like speech, not a report.
- Preserve the key facts and the overall takeaway from the full answer, but drop supporting detail, \
tables, citations, and disclaimers. One core insight and one supporting reason is usually enough.
- Do not introduce any fact that isn't in the full answer provided."""


def summarize_for_speech(question: str, full_answer: str) -> str:
    """Generates a short conversational spoken summary of a full answer."""
    user_prompt = f"""User's question: {question}

Full written answer:
{full_answer}

Give the short spoken version now."""

    summary = generate_response(VOICE_SUMMARY_SYSTEM_PROMPT, user_prompt).strip()

    if len(summary) > MAX_VOICE_SUMMARY_CHARS:
        summary = summary[:MAX_VOICE_SUMMARY_CHARS].rsplit(" ", 1)[0] + "."

    return summary