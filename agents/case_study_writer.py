# -*- coding: utf-8 -*-
"""
The Case Study Writer agent: drafts a close analysis of one named company or
leader in the Metis voice, mirroring the structure of the Newman's Own
reference sample (voice_reference/01-newmans-own-culture-case-study.docx) --
not just its tone. A case study is Metis's third content line, alongside
essays and field notes: same pillar taxonomy, its own format and cadence.

Drafting runs through the same guardrails.draft_with_guardrails() loop as the
other writers. Shares the pro-tier writer model since these are still
publication-quality.

IMPORTANT -- accuracy: this agent has no search grounding of its own (Scout
does the research, separately). A case study makes specific claims about a
real subject, so hallucinated facts here are a real reputational risk in a
way an essay's abstract argument is not. Pass research_notes (a grounded
headline from Scout, or anything John supplies) whenever you have it; the
prompt leans on it. Without it, the prompt instructs the model to stay with
the general, well-established pattern rather than inventing specifics.

Run:  python -m agents.case_study_writer "Company or leader name"
"""

import os

from voice_profile import VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT, CONTENT_RULES
from guardrails import draft_with_guardrails

MODEL = os.getenv("GEMINI_WRITER_MODEL", "gemini-pro-latest")
JUDGE_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT
DRAFTS_DOC = "Insights Drafts.docx"
CASE_STUDY_RULES = CONTENT_RULES["case_study"]


def _build_case_study_prompt(subject: str, pillar: str, angle: str = None,
                             research_notes: str = None, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    angle_line = f"\nANGLE (the reading Metis wants to take): {angle}\n" if angle else ""
    if research_notes:
        research_block = (
            f"\nVERIFIED CONTEXT ON THE SUBJECT (work from this, do not "
            f"contradict it):\n{research_notes}\n"
        )
        accuracy_note = (
            "Stay inside the verified context above for specific facts. You "
            "may draw on well-established public knowledge about the subject "
            "to fill in the picture, but do not invent dates, figures, or "
            "quotes that are not in the verified context or extremely widely "
            "known."
        )
    else:
        research_block = ""
        accuracy_note = (
            "No verified research notes were supplied for this subject. Do "
            "not state specific dates, financial figures, or quotes unless "
            "they are extremely well-established public knowledge. Describe "
            "the general pattern and mechanism rather than inventing specific "
            "claims you cannot back."
        )

    return f"""Write a case study for Metis Advisory Group analyzing {subject}
through the lens of the {pillar} pillar.
{angle_line}{research_block}
Mirror this structure, adapting section headers to the subject rather than
copying them verbatim:
1. Open with one concrete, specific fact about the subject's origin or a
   structural decision that set the pattern. Not a hook.
2. Name the operating principle or mechanism underneath the subject's
   approach. Give this section its own short header.
3. A section on leadership structure and accountability: who is responsible
   for holding to that principle, and how.
4. An implications section: several short header-led observations in the
   form "Label: one sentence", each naming one concrete downstream effect.
5. A short section addressed to the reader (a Metis client) naming two to
   four transferable principles -- the actual lesson, not a recap.
6. Name one real tension or trade-off in the subject's model and how they
   manage it. Do not pretend the model is frictionless.
7. Close on an earned synthesis, not a summary.

Section headers: put each on its own line, alone in its paragraph, two to six
words, Title Case, no ending punctuation -- so they read as section breaks.

{accuracy_note}
{revision_note}
Requirements:
- {CASE_STUDY_RULES['min_words']} to {CASE_STUDY_RULES['max_words']} words
- Anchor claims to specific named people, dates, or decisions, not generic
  praise
- Quote a named source directly at least once if the context supports it
- Short declarative sentences; vary the rhythm
- No hashtags, no emoji, no calls to action
- End on an earned observation, not a summary or a bow

Write only the case study body, including its header lines. No title, no
preamble, no explanation."""


def draft_case_study(subject: str, pillar: str, angle: str = None,
                     research_notes: str = None, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for a case study. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        MODEL,
        build_prompt=lambda feedback: _build_case_study_prompt(
            subject, pillar, angle=angle, research_notes=research_notes, feedback=feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=CASE_STUDY_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="case_study_writer",
        temperature=CASE_STUDY_RULES["temperature"],
    )


def write_case_study(subject: str, pillar: str, angle: str = None,
                     research_notes: str = None) -> str:
    """Thin wrapper for callers that only want the final text."""
    return draft_case_study(subject, pillar, angle=angle, research_notes=research_notes)["text"]


def propose_metadata(case_study_text: str, pillar: str, subject: str) -> dict:
    """One cheap, ungated Gemini call to derive a title and a one-sentence dek
    from a finished case study, for the site card and article header. Runs on
    the Flash model at promote time (not per draft). Falls back to a
    truncated first line if parsing fails, so publishing never hard-crashes
    on a metadata hiccup."""
    from gemini_client import generate
    import json

    prompt = f"""This is a finished Metis Advisory Group case study analyzing
{subject} (pillar: {pillar}). Write a title and a one-sentence dek (a subhead
that says what the case study argues), both in the same restrained voice as
the piece.

CASE STUDY:
{case_study_text}

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
        first = case_study_text.strip().split("\n", 1)[0]
        title = (first[:70] + "...") if len(first) > 70 else first
    return {"title": title, "dek": dek}


if __name__ == "__main__":
    import sys

    from doc_output import append_to_doc

    subject_arg = " ".join(sys.argv[1:]) or "Newman's Own"
    pillar = "Team Dynamics & Culture Engineering"

    print(f"Using model: {MODEL}\n")
    print("=" * 70)
    print(f"Drafting case study on: {subject_arg}")
    print(f"Pillar: {pillar}")
    print("=" * 70)
    result = draft_case_study(subject_arg, pillar)
    case_study = result["text"]
    append_to_doc(DRAFTS_DOC, "[Case study] " + subject_arg, case_study)
    print(f"[SAVED] Appended to '{DRAFTS_DOC}' after {result['attempts']} attempt(s)")

    word_count = len(case_study.split())
    print(f"[LENGTH] {word_count} words "
          f"(target {CASE_STUDY_RULES['min_words']}-{CASE_STUDY_RULES['max_words']})")

    e = result["evaluation"]
    if e["passed"]:
        print(f"[GUARDRAILS] Passed. voice_score={e['voice_score']}/10, tone={e['tone']}")
    else:
        print(f"[GUARDRAILS] Did not pass after {result['attempts']} attempts: {e['feedback']}")
