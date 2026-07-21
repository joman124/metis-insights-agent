# -*- coding: utf-8 -*-
"""
The Metis Scout agent: finds trending topics that Metis's audience (executives,
founders, boards) is talking about, using Gemini with Google Search grounding
so results reflect current events rather than the model's training-data recall.

Run:  python -m agents.scout ["optional topic to focus the search"]
"""

import json
import os
import sys

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

PILLARS = [
    "Leadership",
    "AI & Work",
    "Culture",
    "Methods",
    "Research",
]
PLATFORMS = ["linkedin", "substack"]

SYSTEM_INSTRUCTION = (
    "You are a research scout for Metis Advisory Group, a strategy and "
    "leadership-psychology firm advising executives, founders, and boards. "
    "Find current, real news and discussion that these leaders care about, at "
    "the intersection of leadership, organizational culture, and AI's effect "
    "on how companies work.\n\n"
    "Content pillars (every suggestion must map to exactly one):\n"
    "- Leadership: how executives decide, align, and hold accountability\n"
    "- AI & Work: integrating AI as a digital workforce, not a toy\n"
    "- Culture: psychological safety, engagement, what people really do\n"
    "- Methods: how to diagnose and measure organizational problems\n"
    "- Research: findings leaders should know but usually misread\n\n"
    "Target platforms: linkedin (the Metis business page, fast reactions) or "
    "substack (Notes, quick thoughts). Metis's voice is measured and anti-hype: "
    "it does not moralize, it measures."
)


def find_topics(topic: str = None, count: int = 5) -> list:
    """Return a list of topic briefings, each a dict with: headline, source,
    relevance_score, suggested_angle, suggested_pillar, suggested_platform."""
    focus = (
        f' Focus specifically on: "{topic}".' if topic
        else " Find what is trending in the past 48 hours."
    )
    prompt = f"""Search for {count} current, real news items or discussions that
executives, founders, and boards are paying attention to, at the intersection of
leadership, organizational culture, and AI at work.{focus}

For each one, return an object with exactly these six keys:
- headline: the real headline or topic, in your own words
- source: the publication or site name
- relevance_score: integer 1-10, how relevant to senior leaders making
  decisions about people, culture, and AI adoption
- suggested_angle: one specific, non-obvious sentence Metis could take, in a
  measured advisory voice
- suggested_pillar: exactly one of {PILLARS}
- suggested_platform: exactly one of {PLATFORMS}

Return ONLY a JSON array of {count} objects. No markdown code fences, no
preamble, no explanation - just the raw JSON array."""

    # Imported lazily so the module imports without google-genai installed
    # (routing/tests do not need it); only this grounded call does.
    from google.genai import types
    from gemini_client import generate

    # Same grounding pattern as the After Work Scout: a thinking model with
    # Google Search grounding can return finish_reason=STOP but empty text
    # (the whole turn went to thought parts). disable_thinking makes it emit
    # the JSON answer.
    raw = generate(
        MODEL,
        prompt,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        disable_thinking=True,
    )
    return _parse_json_array(raw)


def _parse_json_array(raw: str) -> list:
    """Strip markdown fences if the model added them anyway, then parse.
    Fails with the raw output shown rather than a bare JSONDecodeError."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise SystemExit(
            "\n[SCOUT] Gemini did not return valid JSON. Raw output:\n" + raw[:800]
        )
    if not isinstance(data, list):
        raise SystemExit(f"\n[SCOUT] Expected a JSON array of topics, got: {type(data)}")
    return data


if __name__ == "__main__":
    requested_topic = " ".join(sys.argv[1:]) or None
    print(f"Using model: {MODEL}")
    print(f"Topic filter: {requested_topic or '(none - trending past 48 hours)'}\n")
    briefing = find_topics(requested_topic)
    print(json.dumps(briefing, indent=2))
