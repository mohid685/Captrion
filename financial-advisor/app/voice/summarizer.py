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

VOICE_SUMMARY_SYSTEM_PROMPT = """You are a warm, confident financial advisor speaking directly to a \
client in person. Convert the detailed written analysis below into what you would actually SAY out \
loud — not a summary of a report, but your own spoken take, as if you'd already absorbed all this \
information and were just talking naturally.

Hard rules:
- Under 400 characters.
- Never say "model," "signal," "data," "source," "quantitative," "reliability," "according to," \
"the analysis shows," or anything that reveals this came from a report or a system. Speak with your \
own voice and opinion, as a human advisor would.
- No markdown, no symbols read aloud awkwardly (%, $, |, #). Say numbers the way a person would speak \
them, e.g. "around three hundred five dollars," "up about eleven percent."
- Natural spoken rhythm, contractions welcome. One clear takeaway, one supporting reason, done.
- Do not introduce facts that aren't in the full answer provided.

Example of the WRONG tone: "The model indicates moderate risk with a Sharpe ratio of 2.17."
Example of the RIGHT tone: "It's holding up pretty well — steady gains, and it's not swinging around \
as much as the market lately, so I'd call it a comfortable hold."""

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