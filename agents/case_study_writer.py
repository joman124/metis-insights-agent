# -*- coding: utf-8 -*-
"""
The Case Study Writer agent: drafts an Insights case study in the Metis voice.

A case study is the third Insights content type, next to essays and field
notes (decision c14: "inside Insights, by pillar, named-with-consent"). It
traces one piece of client work as a situation -> intervention -> outcome arc
and reads as teaching material under the same banner as the essays, not as a
named-client showcase.

Confidentiality is built into the drafting, not bolted on after. The writer
ALWAYS drafts anonymized -- role + sector + situation, no company or person
names, figures banded -- so the agent never invents a client identity. Naming
a real client is a deliberate, consent-gated opt-in John applies at promote
time (content_publisher's `consent` field), once a signed release is on file.

Drafting runs through the same guardrails.draft_with_guardrails() loop as the
essay and field-note writers, using the case-study format's length and em-dash
rules. Reuses the essay writer's propose_metadata() for the title/dek, since a
case study needs the same card metadata an essay does.

Run:  python -m agents.case_study_writer
"""

import os

from voice_profile import (VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT,
                           CONTENT_RULES, append_cta)
from guardrails import draft_with_guardrails
import edit_lessons

MODEL = os.getenv("ANTHROPIC_WRITER_MODEL", "claude-opus-5")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT
DRAFTS_DOC = "Insights Drafts.docx"
CASE_RULES = CONTENT_RULES["case_study"]


def _build_case_study_prompt(topic: str, pillar: str, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write an Insights case study for Metis Advisory Group.

PILLAR (the lens this case study works within): {pillar}
STARTING ANGLE: {topic}
{revision_note}{edit_lessons.lessons_prompt()}
A case study traces one piece of real advisory work as an arc: the situation
as it actually presented, the intervention Metis made, and the outcome that
followed. It is teaching material, not a sales page. Draw the general pattern
a leader would recognize out of the specific engagement.

CONFIDENTIALITY (not optional):
- Write it ANONYMIZED. Identify the client only by role and sector -- "a
  mid-market healthcare operator," "a founder scaling past 200 people." Never
  name a company or a person, and never invent a name to stand in for one.
- Band any figures so they cannot be back-solved ("headcount roughly doubled,"
  not "grew from 95 to 210"). Do not report exact client metrics.
- A real name only ever enters later, by hand, when a signed release exists.
  Your job is the anonymized draft.

Requirements:
- {CASE_RULES['min_words']} to {CASE_RULES['max_words']} words
- Structure it as situation, then intervention, then outcome -- in that order,
  but as flowing prose, not as labeled sections or headings
- Open on the situation itself, not a hook, a statistic, or a question
- Name the mechanism underneath what happened, not just the events
- Short declarative sentences; let each land
- No headline or title -- body only
- Separate paragraphs with a blank line
- No hashtags, no emoji, no calls to action
- End on an earned observation about the pattern, not a summary or a bow

Write only the case-study body. No title, no preamble, no explanation."""


def draft_case_study(topic: str, pillar: str, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for a case study. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails,
    with the discovery-call CTA appended to the final text (added after the
    guardrails run, so the voice judge never scores against it)."""
    result = draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_case_study_prompt(topic, pillar, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=CASE_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="case_study_writer",
        temperature=CASE_RULES["temperature"],
    )
    return {**result, "text": append_cta(result["text"])}


def write_case_study(topic: str, pillar: str) -> str:
    """Thin wrapper for callers that only want the final text."""
    return draft_case_study(topic, pillar)["text"]


if __name__ == "__main__":
    from doc_output import append_to_doc

    print(f"Using model: {MODEL}\n")
    test = (
        "An executive team that kept reorganizing the same unresolved conflict, "
        "each new structure a fresh way to avoid naming who decided what."
    )
    pillar = "Team Dynamics & Culture Engineering"

    print("=" * 70)
    print(f"Drafting case study for pillar: {pillar}")
    print(f"Angle: {test}")
    print("=" * 70)
    result = draft_case_study(test, pillar)
    case = result["text"]
    append_to_doc(DRAFTS_DOC, "[Case study] " + test, case)
    print(f"[SAVED] Appended to '{DRAFTS_DOC}' after {result['attempts']} attempt(s)")

    word_count = len(case.split())
    print(f"[LENGTH] {word_count} words "
          f"(target {CASE_RULES['min_words']}-{CASE_RULES['max_words']})")

    e = result["evaluation"]
    if e["passed"]:
        print(f"[GUARDRAILS] Passed. voice_score={e['voice_score']}/10, tone={e['tone']}")
    else:
        print(f"[GUARDRAILS] Did not pass after {result['attempts']} attempts: {e['feedback']}")
