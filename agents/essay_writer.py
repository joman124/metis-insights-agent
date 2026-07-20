# -*- coding: utf-8 -*-
"""
The Essay Writer agent: drafts a long-form Insights essay in the Metis voice.
This is the primary deliverable -- the featured / archive essays published
about quarterly. Drafting runs through guardrails.draft_with_guardrails(),
which generates, scores (first-pass rule checks + LLM-as-judge voice/tone),
and re-drafts with the judge's feedback up to 3 times before giving up.

Uses its own model (GEMINI_WRITER_MODEL), separate from GEMINI_MODEL which the
other agents use, since draft quality matters most here. Defaults to a pro
model; override in .env if your key does not have access to one (run
check_setup.py to see what is available).

Run:  python -m agents.essay_writer
"""

import os

from voice_profile import VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT, CONTENT_RULES
from guardrails import draft_with_guardrails

MODEL = os.getenv("GEMINI_WRITER_MODEL", "gemini-2.5-pro")
JUDGE_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT
DRAFTS_DOC = "Insights Drafts.docx"
ESSAY_RULES = CONTENT_RULES["essay"]


def _build_essay_prompt(topic: str, pillar: str, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write a long-form Insights essay for Metis Advisory Group.

PILLAR (the lens this piece works within): {pillar}
STARTING ANGLE: {topic}
{revision_note}
Develop the angle into a real argument. Open on a specific pattern or
observation from executive work, name the mechanism underneath it, and follow
it to an earned conclusion. Use one concrete example a leader would recognize.
Do not summarize business news; read it.

Requirements:
- {ESSAY_RULES['min_words']} to {ESSAY_RULES['max_words']} words
- Open on a precise observation or claim, not a hook, statistic, or question
- Short declarative sentences; let each land
- No headline or title -- body only
- Separate paragraphs with a blank line
- No hashtags, no emoji, no calls to action
- End on an earned observation, not a summary or a bow

Write only the essay body. No title, no preamble, no explanation."""


def draft_essay(topic: str, pillar: str, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for an essay. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_essay_prompt(topic, pillar, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=ESSAY_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="essay_writer",
        temperature=ESSAY_RULES["temperature"],
    )


def write_essay(topic: str, pillar: str) -> str:
    """Thin wrapper for callers that only want the final text."""
    return draft_essay(topic, pillar)["text"]


def propose_metadata(essay_text: str, pillar: str) -> dict:
    """One cheap, ungated Gemini call to derive a title and a one-sentence dek
    from a finished essay, for the site card and article header. Runs on the
    Flash model at promote time (not per draft), so only pieces John actually
    promotes pay for it. Falls back to a truncated first line if parsing
    fails, so publishing never hard-crashes on a metadata hiccup."""
    from gemini_client import generate
    import json

    prompt = f"""This is a finished essay for Metis Advisory Group (pillar:
{pillar}). Write a title and a one-sentence dek (a subhead that says what the
essay argues), both in the same restrained voice as the essay.

ESSAY:
{essay_text}

Return ONLY a JSON object with exactly these keys:
- "title": a short, specific title (no more than 12 words, no trailing period)
- "dek": one sentence, no more than 30 words

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
        dek = str(data.get("dek", "")).strip()
    except Exception:
        title, dek = "", ""

    if not title:
        first = essay_text.strip().split("\n", 1)[0]
        title = (first[:70] + "...") if len(first) > 70 else first
    return {"title": title, "dek": dek}


if __name__ == "__main__":
    from doc_output import append_to_doc

    print(f"Using model: {MODEL}\n")
    test = (
        "When an enterprise buys an AI tool before auditing its own decision "
        "rights, the tool inherits the confusion instead of resolving it."
    )
    pillar = "Strategic Thinking & Decision Architecture"

    print("=" * 70)
    print(f"Drafting essay for pillar: {pillar}")
    print(f"Angle: {test}")
    print("=" * 70)
    result = draft_essay(test, pillar)
    essay = result["text"]
    append_to_doc(DRAFTS_DOC, "[Essay] " + test, essay)
    print(f"[SAVED] Appended to '{DRAFTS_DOC}' after {result['attempts']} attempt(s)")

    word_count = len(essay.split())
    print(f"[LENGTH] {word_count} words "
          f"(target {ESSAY_RULES['min_words']}-{ESSAY_RULES['max_words']})")

    e = result["evaluation"]
    if e["passed"]:
        print(f"[GUARDRAILS] Passed. voice_score={e['voice_score']}/10, tone={e['tone']}")
    else:
        print(f"[GUARDRAILS] Did not pass after {result['attempts']} attempts: {e['feedback']}")
