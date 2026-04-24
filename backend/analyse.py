# VoiceNote UK - AI structuring via Groq API
# Sends a raw transcript to Groq's llama-3.3-70b-versatile model and
# returns structured notes as a Python dict.

import json
import os

from openai import OpenAI
from templates import get_template_prompt

def _get_client():
    api_key = os.environ.get("OPENROUTER_API_KEY") or "sk-or-your-full-key-here"
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )


_SYSTEM_PROMPT = (
    "You are a professional note-taking assistant. "
    "Given a spoken transcript, extract and structure the content into "
    "clean, actionable notes. Always respond with valid JSON only — "
    "no markdown fences, no extra text, no commentary."
)


def analyse_transcript(transcript: str, template_type: str = "custom") -> dict:
    """
    Send a transcript to Groq and return structured notes.

    Returns a dict with keys:
        summary      — 2-3 sentence overview of the content
        key_points   — list of bullet-point strings
        action_items — list of task/follow-up strings (empty list if none)
        tone         — one of "formal" | "informal" | "emotional"
    """
    # Handle empty or whitespace-only transcripts gracefully
    if not transcript.strip():
        return {
            "summary": "No content to analyse.",
            "key_points": [],
            "action_items": [],
            "tone": "unknown",
        }

    prompt = get_template_prompt(template_type)
    user_prompt = (
        f"{prompt}\n\n"
        "Transcript:\n"
        f"{transcript}"
    )

    client = _get_client()

    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    content = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model accidentally adds them
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    result = json.loads(content)

    return {
        "summary": result.get("summary", ""),
        "key_points": result.get("key_points", []),
        "action_items": result.get("action_items", []),
        "tone": result.get("tone", "unknown"),
    }
