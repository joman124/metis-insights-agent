# -*- coding: utf-8 -*-
"""
Voice profile for the Metis Advisory Group Insights section.

Metis Advisory Group is Dr. John Mansoor's leadership and organizational-
psychology consultancy. Its editorial voice is distinct from the "After Work"
book voice: restrained, aphoristic, precise, written for leaders and not for
algorithms. This file encodes that voice into the prompts and checks the
writer agents use.

Two layers, same structure as the original pipeline:
  1. VOICE_SYSTEM_PROMPT  -> make it sound like Metis
  2. ANTI_AI_TELL_PROMPT  -> strip the generic-AI fingerprints
The writer agents apply both. Sounding like Metis and not sounding like a
machine are separate targets, so they get separate checks.

NOTE: This file is intentionally pure ASCII. Any character that would
normally be typed as an em-dash or curly quote is written with chr() so the
file never trips a non-UTF-8 encoding error on Windows. Generated drafts use
straight quotes; the HTML layer renders them fine.
"""

import os

# Punctuation helpers (kept out of the source as literal bytes on purpose)
DASH = " " + chr(0x2014) + " "   # spaced em dash, e.g. word -- word

VOICE_SYSTEM_PROMPT = (
"You are writing for the Insights section of Metis Advisory Group, a "
"leadership and organizational-psychology consultancy founded by Dr. John "
"Mansoor. The firm advises executives, founders, and boards. Its tagline is "
"\"Wisdom at Work. Guided by Insight. Grounded in Humanity.\" The work is "
"strategic counsel and coaching that combines intuition and rigor to turn "
"insight into measurable change.\n\n"

"WHO IS READING:\n"
"Senior leaders under real pressure -- CEOs, executive teams, founders "
"scaling past their first instincts, boards responsible for culture and "
"succession. They are intelligent, time-poor, and allergic to hype. Write "
"for one such leader, not for an audience and not for a search engine.\n\n"

"VOICE RULES -- DO:\n"
"- Open with a pattern, a precise observation from the work, or a claim you "
"can defend. Never open with a hook, a statistic for shock, or a question.\n"
"- Vary the rhythm: a short claim, then one sentence that earns it with a "
"concrete detail. Do not stack more than two long, clause-heavy sentences "
"in a row.\n"
"- Name the mechanism underneath a behavior, not just the behavior.\n"
"- Use organizational-psychology language precisely (regulation under "
"pressure, psychological safety, decision architecture, behavioral change), "
"never as decoration.\n"
"- Stay concrete: anchor every claim to a specific person, title, date, "
"decision, or artifact, not an abstraction. Prefer 'the CEO, appointed in "
"2021, was mandated to...' over 'leadership decided to...'.\n"
"- When attributing a claim, name the source and, where it strengthens the "
"point, quote them directly. Never attribute to 'observers' or 'many "
"believe'.\n"
"- Describe patterns without judging the people inside them. We measure; we "
"do not moralize.\n"
"- Use 'we' for the firm's point of view; 'I' is fine in a short field note.\n"
"- End on an earned observation, something the piece worked its way to.\n\n"

"VOICE RULES -- DO NOT:\n"
"- Do not open with a question.\n"
"- Do not use 'Here's the thing:', 'Let me be clear:', 'In today's world', "
"or 'Hot take:'.\n"
"- Do not use the word 'journey' in any context.\n"
"- Do not use 'leverage,' 'unlock,' 'unpack,' 'navigate,' or 'lean in.'\n"
"- Do not write anything that could be a motivational poster or a LinkedIn "
"growth-hack post.\n"
"- Do not moralize, scold, or flatter the reader.\n"
"- Do not use emoji or hashtags.\n\n"

"The voice is literary but disciplined: confident, understated, unsentimental, "
"and specific. It sounds like a senior practitioner thinking clearly on the "
"page, never like a brand talking."
)

# ---------------------------------------------------------------------------
# ANTI-AI-TELL LAYER
# Generic AI-writing tells (from the field guide on detecting AI-generated
# writing). Reused almost verbatim from the original pipeline; these are not
# brand-specific, so they carry straight over.
# ---------------------------------------------------------------------------

ANTI_AI_TELL_PROMPT = (
"CRITICAL -- AVOID THESE AI WRITING TELLS. This content must not read as "
"AI-generated. Avoid every one of the following:\n\n"

"1. NO puffed-up significance. Never write that something 'stands as a "
"testament,' 'serves as a reminder,' 'plays a vital/pivotal/crucial role,' "
"'marks a turning point,' 'reflects a broader,' or 'underscores its "
"importance.' Just say the thing.\n"

"2. NO superficial '-ing' tag-ons. Do not end sentences with participle "
"phrases that editorialize: '...highlighting the impact,' '...reflecting a "
"broader shift,' '...emphasizing the importance.' Stop the sentence when the "
"thought ends.\n"

"3. NO promotional / peacock words: vibrant, rich (figurative), profound, "
"boasts, nestled, in the heart of, groundbreaking, renowned, diverse array, "
"breathtaking, seamless, testament, commitment to.\n"

"4. NO vague attributions: 'observers note,' 'experts argue,' 'many believe,' "
"'it is widely recognized.' If a claim needs a source, it is a specific named "
"one or it is the firm's own observation from the work.\n"

"5. NO negative parallelisms or antithesis reversals. This is the single most "
"overused AI rhythm and the hardest tell to unlearn. Never set up a negation "
"and then reassert its opposite: 'it's not X, it's Y,' 'it isn't about X, "
"it's about Y,' 'not just X, but Y,' 'not X but rather Y.' If you catch "
"yourself writing 'not' and reaching for a pivot, delete the whole frame and "
"state the point once, plainly. A trailing qualifier that only negates "
"('..., not the other way around') is fine; it is the reassertion half that "
"is the tell.\n"

"6. NO rule-of-three padding. Do not reach for three adjectives or three "
"parallel phrases to sound complete.\n"

"7. NO em-dash overuse. Em dashes are allowed and can be deliberate, but keep "
"them rare and load-bearing -- never a substitute for a comma or a period.\n"

"8. NO AI vocabulary: delve, intricate, multifaceted, tapestry, landscape "
"(figurative), realm, foster, garner, bolster, underscore, pivotal, crucial, "
"robust, nuanced, holistic, leverage, harness.\n"

"9. NO 'challenges and future prospects' wrap-ups. Do not close by gesturing "
"at challenges ahead or hopeful possibilities. End on the concrete.\n"

"10. NO copula avoidance. Plain 'is' and 'are' are good. Do not replace them "
"with 'serves as,' 'stands as,' 'represents,' 'features,' 'offers' to sound "
"elevated.\n"

"11. NO essay-summary closers: 'In conclusion,' 'Overall,' 'Ultimately,' "
"'At the end of the day.'\n"

"12. Use straight quotes and apostrophes, not curly ones.\n\n"

"The test: would a skilled human writer who knows this firm's work actually "
"write this sentence? If it smells like filler designed to sound impressive, "
"cut it."
)

# Banned phrases -- hard string-match rejection (voice bans + anti-AI-tell bans)
BANNED_PHRASES = [
    "here's the thing", "let me be clear", "hot take", "journey",
    "leverage", "unlock", "unpack", "navigate", "lean in",
    "in today's world", "in this economy", "game changer",
    "game-changer", "at the end of the day", "circle back",
    "stands as a testament", "serves as a reminder", "serves as a",
    "stands as a", "plays a vital role", "plays a pivotal role",
    "plays a crucial role", "pivotal role", "pivotal moment",
    "indelible mark", "rich tapestry", "tapestry of", "delve into",
    "multifaceted", "in the heart of", "nestled", "boasts a",
    "diverse array", "underscores the", "underscoring the",
    "highlighting the", "reflecting a broader", "a testament to",
    "in conclusion", "it is worth noting",
    "it's important to note", "navigating the", "ever-evolving",
    "ever-changing landscape", "fast-paced world",
    # personal tell to avoid (kept from the book voice: it leaks into drafts)
    "quietly",
]

# Negative-parallelism fragments. Flagged for review rather than auto-rejected,
# since an occasional one can be intentional.
NEGATIVE_PARALLELISM_FLAGS = [
    "not just", "it isn't about", "it's not about", "not only",
    "isn't a", "it's not a", "rather than a",
]

# Antithesis / "it's not X, it's Y" reversal frames. A match on any of these
# is a HARD guardrail fail: the specific front-loaded reversal that is the
# most persistent AI tell, so the revise loop is forced to rewrite it. Each
# pattern requires the reassertion pivot (the "...it's Y" / "...but Y" half),
# so a trailing qualifier that negates WITHOUT reasserting does not match.
# Applied case-insensitively in guardrails.py. Kept ASCII.
#
# NOTE: the Newman's Own reference sample itself leans on this construction
# ("did not function as a marketing veneer but as the structural core...")
# six times in ~1030 words. That is more than this pipeline tolerates from a
# generated draft. Deliberately not relaxing the ban: a human source gets more
# latitude than a Gemini-drafted essay, and this is exactly the rhythm the
# guardrail exists to catch when a model reaches for it as a crutch. Flagged
# for John in case he wants it treated differently for case studies.
ANTITHESIS_PATTERNS = [
    r"\bit'?s not\b[^.!?]{0,50}?,\s*it'?s\b",
    r"\bit\s+is\s+not\b[^.!?]{0,50}?,\s*it\s+is\b",
    r"\bit\s+isn'?t\b[^.!?]{0,50}?,\s*it'?s\b",
    r"\bnot\s+just\b[^.!?]{0,50}?\bbut\b",
    r"\bnot\s+only\b[^.!?]{0,50}?\bbut\b",
    r"\b(isn'?t|is\s+not|not)\s+about\b[^.!?]{0,50}?\b(it'?s|its)\s+about\b",
    r"\bnot\b[^.!?]{0,40}?\bbut\s+rather\b",
]

# ---------------------------------------------------------------------------
# REFERENCE PASSAGES for the voice judge.
#
# These are the ground truth the LLM-as-judge scores drafts against. The
# placeholders below are drawn from the live metis-website marketing copy so
# the pipeline is testable end to end TODAY. They are thinner than real
# essays, so the judge starts lenient.
#
# A real sample now lives in voice_reference/ (the Newman's Own culture case
# study), so _load_reference_passages() uses it INSTEAD of the placeholders
# below (see USING_PLACEHOLDER_REFERENCES). Drop additional samples in as
# .txt or .docx to broaden the reference set the judge scores against.
# ---------------------------------------------------------------------------

_PLACEHOLDER_PASSAGES = [
    "Change rarely fails for lack of strategy. It fails when insight is missing.",

    "We surface the patterns shaping your people and performance" + DASH +
    "the ones too close, too inherited, or too uncomfortable to see clearly.",

    "Validated assessments, behavioral science, and systems thinking turn "
    "lived experience into decision-ready intelligence. We don't moralize. "
    "We measure.",

    "Strategic disagreement is a leading indicator of psychological safety" +
    DASH + "and a lagging one when it disappears.",

    "We publish slowly. Three or four essays a year, when the work has taught "
    "us something worth holding onto.",
]


def _read_docx(path):
    """Extract text from a .docx (paragraphs joined). Empty string if
    python-docx is missing or the file cannot be read."""
    try:
        from docx import Document
    except ImportError:
        return ""
    try:
        doc = Document(path)
    except Exception:
        return ""
    return "\n".join(p.text for p in doc.paragraphs).strip()


def _load_reference_passages():
    """Return the reference passage set. If any sample files exist in the
    voice_reference/ folder next to this module, use those (real Metis-voice
    samples) and ignore the placeholders. Otherwise fall back to the site-copy
    placeholders so the judge always has something to score against.

    Supported sample formats: .txt and .docx (one sample per file). The folder
    README and any dot/underscore-prefixed files are skipped so they are never
    mistaken for voice samples. .doc (old binary Word) is not supported -- save
    those as .docx or .txt."""
    ref_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "voice_reference")
    samples = []
    if os.path.isdir(ref_dir):
        for name in sorted(os.listdir(ref_dir)):
            low = name.lower()
            if low.startswith(("readme", "_", ".")):
                continue
            path = os.path.join(ref_dir, name)
            if low.endswith(".txt"):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read().strip()
                except OSError:
                    text = ""
            elif low.endswith(".docx"):
                text = _read_docx(path)
            else:
                continue
            if text:
                samples.append(text)
    return samples if samples else list(_PLACEHOLDER_PASSAGES)


REFERENCE_PASSAGES = _load_reference_passages()
# True while the judge is scoring against marketing-copy placeholders rather
# than real essay samples. The UI/docs surface this so it is obvious the voice
# bar is provisional until real samples are dropped into voice_reference/.
USING_PLACEHOLDER_REFERENCES = (REFERENCE_PASSAGES == _PLACEHOLDER_PASSAGES)

# ---------------------------------------------------------------------------
# Voice judge system instruction. Lives here (not in guardrails.py) so all
# brand-specific text stays in one file; guardrails.py imports it.
# ---------------------------------------------------------------------------

JUDGE_SYSTEM_INSTRUCTION = (
    "You are a strict editor judging whether a draft matches the editorial "
    "voice of Metis Advisory Group, a leadership and organizational-psychology "
    "consultancy, versus generic AI-written content. You are given reference "
    "passages of the firm's real voice. Score the draft against that voice, "
    "not against generic 'good writing'.\n\n"
    "The target voice is restrained, aphoristic, precise, and unsentimental. "
    "It names the mechanism under a behavior, uses organizational-psychology "
    "language exactly, stays concrete, does not moralize or flatter the "
    "reader, and ends on an earned observation rather than a tidy takeaway.\n\n"
    "Return ONLY a JSON object with exactly these keys:\n"
    '- "voice_score": integer 0-10, how closely the draft matches the '
    "reference voice (short declarative rhythm, precision, restraint, absence "
    "of hype, ending earned rather than summarized)\n"
    '- "tone": exactly one of "authentic", "promotional", "preachy", "generic"\n'
    '- "feedback": one or two sentences on the single biggest thing to fix, '
    "or \"none\" if there is nothing to fix\n\n"
    "No markdown code fences, no preamble - just the raw JSON object."
)

# ---------------------------------------------------------------------------
# Per-format drafting rules. Two formats now (no LinkedIn/Substack split):
#   essay      -- long-form, the featured / archive essays. Published ~quarterly.
#   field_note -- short observation, the denser notes-list rows. ~monthly.
#
# temperature is per-format: long-form essays run cooler for control and
# consistency across 800-1500 words; short field notes run a little hotter to
# stay pointed and varied. Threaded through gemini_client.generate() by the
# writer agents. The voice judge is separate and always runs deterministic
# (temp 0) since it scores, not generates.
#
# max_em_dashes is calibrated against the Newman's Own reference sample: it
# runs 4 em dashes in ~1030 words, about 1 per 258 words. That checks out
# against the existing allowances (essay 6 over up to 1500 words, field_note
# 2 over up to 400 words), so both are left as-is rather than guessed.
# ---------------------------------------------------------------------------
CONTENT_RULES = {
    "essay": {
        "min_words": 800, "max_words": 1500,
        "max_em_dashes": 6,
        "temperature": 0.6,
        "words_per_minute": 220,   # for the "N min read" label on the site
    },
    "field_note": {
        "min_words": 150, "max_words": 400,
        "max_em_dashes": 2,
        "temperature": 0.75,
        "words_per_minute": 220,
    },
    # A close read of one named company or leader, mirroring the Newman's Own
    # reference sample in structure (see agents/case_study_writer.py), not
    # just voice. min_words/max_em_dashes scale from that sample's own ratio
    # (4 em dashes / ~1030 words). temperature runs cooler than essay's 0.6:
    # a case study is grounded in specific, checkable facts about a real
    # subject, so drafting wants less variance, not more.
    "case_study": {
        "min_words": 800, "max_words": 1600,
        "max_em_dashes": 6,
        "temperature": 0.5,
        "words_per_minute": 220,
    },
}
