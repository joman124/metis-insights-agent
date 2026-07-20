# -*- coding: utf-8 -*-
"""
The Field Note Writer agent: drafts a short Insights field note in the Metis
voice -- the denser observations published about monthly, shown in the
notes-list on the Insights page. Standalone, not derived from an essay: Scout
can source a field note directly.

Drafting runs through the same guardrails.draft_with_guardrails() loop as the
essay writer, using the field-note format's tighter length and em-dash rules.
Shares the pro-tier writer model since these are still publication-quality.

Run:  python -m agents.field_note_writer
"""

import os

from voice_profile import VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT, CONTENT_RULES
from guardrails import draft_with_guardrails

MODEL = os.getenv("GEMINI_WRITER_MODEL", "gemini-2.5-pro")
JUDGE_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT
DRAFTS_DOC = "Insights Drafts.docx"
NOTE_RULES = CONTENT_RULES["field_note"]


def _build_note_prompt(topic: str, pillar: str, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write a short Insights field note for Metis Advisory Group.

PILLAR (the lens this note works within): {pillar}
STARTING ANGLE: {topic}
{revision_note}
A field note makes one observation well. Name a single pattern from executive
or organizational work, say the mechanism underneath it, and stop. No throat-
clearing, no windup.

Requirements:
- {NOTE_RULES['min_words']} to {NOTE_RULES['max_words']} words
- One idea, stated precisely
- Open on the observation itself, not a hook or a question
- Short declarative sentences
- No headline or title -- body only
- Separate paragraphs with a blank line
- No hashtags, no emoji, no call to action
- End on the concrete, not a summary

Write only the note body. No title, no preamble, no explanation."""


def draft_field_note(topic: str, pillar: str, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for a field note. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_note_prompt(topic, pillar, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=NOTE_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="field_note_writer",
        temperature=NOTE_RULES["temperature"],
    )


def write_field_note(topic: str, pillar: str) -> str:
    """Thin wrapper for callers that only want the final text."""
    return draft_field_note(topic, pillar)["text"]


def propose_title(note_text: str, pillar: str) -> str:
    """One cheap, ungated Gemini call to derive a title for a finished field
    note (the single line shown in the notes-list). Falls back to a truncated
    first line if parsing fails, so publishing never hard-crashes."""
    from gemini_client import generate
    import json

    prompt = f"""This is a finished field note for Metis Advisory Group (pillar:
{pillar}). Write a short title for it in the same restrained voice.

FIELD NOTE:
{note_text}

Return ONLY a JSON object with exactly this key:
- "title": a short, specific title (no more than 12 words, no trailing period)

No markdown code fences, no preamble - just the raw JSON object."""
    try:
        raw = generate(JUDGE_MODEL, prompt, temperature=0.4).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)
        title = str(data.get("title", "")).strip()
    except Exception:
        title = ""

    if not title:
        first = note_text.strip().split("\n", 1)[0]
        title = (first[:70] + "...") if len(first) > 70 else first
    return title


if __name__ == "__main__":
    from doc_output import append_to_doc

    print(f"Using model: {MODEL}\n")
    test = (
        "Boards that add an AI committee before naming who owns a bad model "
        "decision have relabeled the accountability gap, not closed it."
    )
    pillar = "Organizational Systems & Change Psychology"

    print("=" * 70)
    print(f"Drafting field note for pillar: {pillar}")
    print(f"Angle: {test}")
    print("=" * 70)
    result = draft_field_note(test, pillar)
    note = result["text"]
    append_to_doc(DRAFTS_DOC, "[Field note] " + test, note)
    print(f"[SAVED] Appended to '{DRAFTS_DOC}' after {result['attempts']} attempt(s)")

    word_count = len(note.split())
    print(f"[LENGTH] {word_count} words "
          f"(target {NOTE_RULES['min_words']}-{NOTE_RULES['max_words']})")

    e = result["evaluation"]
    if e["passed"]:
        print(f"[GUARDRAILS] Passed. voice_score={e['voice_score']}/10, tone={e['tone']}")
    else:
        print(f"[GUARDRAILS] Did not pass after {result['attempts']} attempts: {e['feedback']}")
