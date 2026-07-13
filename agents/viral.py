# -*- coding: utf-8 -*-
"""
The Metis Viral agent: turns a hot topic into fast-reaction content built to
earn views and engagement for the Metis LinkedIn page, in Metis's measured,
anti-hype voice.

Two formats, both drafted through the shared generate-evaluate-revise loop
(guardrails.draft_with_guardrails), so "viral" still means "sounds like Metis
and passes the voice judge," just short and punchy:

  - a short LinkedIn post (PLATFORM_RULES["linkedin_viral"])
  - a Substack Note (PLATFORM_RULES["substack_note"])

The LinkedIn post is meant to be auto-posted (see linkedin_publisher.py); the
Substack Note is saved for a human to post, since Substack has no API.

Each draft must clear TWO gates before it is accepted (up to 3 attempts):
  1. the voice judge in guardrails.py (sounds like Metis, tone authentic), and
  2. engagement.check() -- a pure-logic reach gate (hook length, no question
     opener, hashtag count, length budget). Its feedback is fed back into the
     next redraft, same as the voice feedback.

TUNING (where to adjust behavior):
  - Length / hashtags / temperature: PLATFORM_RULES in metis_voice_profile.py.
  - Weak-hook rules / the "see more" cutoff: engagement.py.
  - What sounds like Metis / banned hype words: metis_voice_profile.py
    (VOICE_SYSTEM_PROMPT, BANNED_PHRASES, REFERENCE_PASSAGES).
  - logs/agent_trace.jsonl shows which gate rejected each attempt.

Run:  python -m agents.viral ["optional hot topic"]
"""

import os
import sys
import time

from metis_voice_profile import (VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT,
                                  PLATFORM_RULES)
from guardrails import draft_with_guardrails, CALL_PACING_SECONDS
import engagement

MODEL = os.getenv("GEMINI_WRITER_MODEL", "gemini-pro-latest")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT

LINKEDIN_DOC = "Metis LinkedIn Posts.docx"
NOTE_DOC = "Metis Substack Notes.docx"

VIRAL_RULES = PLATFORM_RULES["linkedin_viral"]
NOTE_RULES = PLATFORM_RULES["substack_note"]


def _build_viral_linkedin_prompt(topic: str, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write a short, high-engagement LinkedIn post for the Metis page
reacting to this hot topic:

TOPIC: {topic}
{revision_note}
This is a fast reaction meant to stop a senior leader's scroll and pull
comments. Take a real, specific advisory position on what this means for how
companies lead, decide, or adopt AI. Not a summary of the news. A view.

Requirements:
- {VIRAL_RULES['min_words']} to {VIRAL_RULES['max_words']} words
- Open with one sharp, concrete line (a claim or a real tension), not a question
- Short declarative sentences. White space is fine.
- Measured and confident. Anti-hype. No hustle language.
- End on a line that makes a leader reconsider or invites a reply
- Add {VIRAL_RULES['min_hashtags']} to {VIRAL_RULES['max_hashtags']} relevant
  hashtags on the last line
- No external links in the body
- No emoji

Write only the post. No preamble, no explanation."""


def _build_note_prompt(topic: str, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write a Substack Note for Metis reacting to this hot topic:

TOPIC: {topic}
{revision_note}
A Note is a single quick thought, the length of a good text message. Sharp,
specific, in Metis's measured voice. One idea, stated once, well.

Requirements:
- {NOTE_RULES['min_words']} to {NOTE_RULES['max_words']} words
- Open on the concrete, not an abstraction
- No hashtags
- End on a line that provokes thought, not a summary

Write only the Note. No preamble, no explanation."""


def draft_viral_linkedin(topic: str, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for a viral LinkedIn post. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_viral_linkedin_prompt(topic, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=VIRAL_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="viral",
        temperature=VIRAL_RULES["temperature"],
        # Also require the draft to be built for reach (hook, length, hashtags),
        # not just on-voice.
        extra_checks=lambda t: engagement.check(t, VIRAL_RULES),
    )


def draft_note(topic: str, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for a Substack Note. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_note_prompt(topic, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=NOTE_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="viral",
        temperature=NOTE_RULES["temperature"],
        extra_checks=lambda t: engagement.check(t, NOTE_RULES),
    )


def write_viral_post(topic: str) -> str:
    """Thin wrapper for callers that only want the final LinkedIn text."""
    return draft_viral_linkedin(topic)["text"]


def write_note(topic: str) -> str:
    """Thin wrapper for callers that only want the final Note text."""
    return draft_note(topic)["text"]


if __name__ == "__main__":
    from doc_output import append_to_doc

    hot_topic = " ".join(sys.argv[1:]) or (
        "A survey says most executives cannot name the metric their AI pilot moved"
    )
    print(f"Using model: {MODEL}")
    print(f"Hot topic: {hot_topic}\n")

    print("=" * 70)
    print("VIRAL LINKEDIN POST")
    print("=" * 70)
    li = draft_viral_linkedin(hot_topic)
    print(li["text"])
    append_to_doc(LINKEDIN_DOC, hot_topic, li["text"])
    e = li["evaluation"]
    status = "passed" if e["passed"] else "did not pass"
    print(f"\n[GUARDRAILS] {status} after {li['attempts']} attempt(s). "
          f"voice_score={e['voice_score']}/10, tone={e['tone']}")

    time.sleep(CALL_PACING_SECONDS)

    print("\n" + "=" * 70)
    print("SUBSTACK NOTE")
    print("=" * 70)
    note = draft_note(hot_topic)
    print(note["text"])
    append_to_doc(NOTE_DOC, hot_topic, note["text"])
    e = note["evaluation"]
    status = "passed" if e["passed"] else "did not pass"
    print(f"\n[GUARDRAILS] {status} after {note['attempts']} attempt(s). "
          f"voice_score={e['voice_score']}/10, tone={e['tone']}")
    print(f"\n[SAVED] '{LINKEDIN_DOC}' and '{NOTE_DOC}'.")
