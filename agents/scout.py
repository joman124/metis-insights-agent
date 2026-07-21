# -*- coding: utf-8 -*-
"""
The Scout agent: finds notable business events and developments from the
trailing three months that senior leaders are talking about, using Gemini
with Google Search grounding so results reflect current events rather than
the model's training-data recall. Each finding is mapped to one of the five
Metis Pillars and to a content format (essay or field note).

Metis publishes slowly and for leaders, so Scout is not chasing daily news.
It looks for the developments of the last quarter with enough substance for
an organizational-psychology reading -- leadership changes, restructurings,
culture and return-to-office shifts, AI adoption inside enterprises, notable
governance or succession stories.

Run:  python -m agents.scout ["optional theme to focus the search"]
"""

import json
import os
import sys
from datetime import date, timedelta

from google.genai import types

from gemini_client import generate
from pillars import PILLAR_NAMES

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

FORMATS = ["essay", "field_note"]
LOOKBACK_DAYS = 90

SYSTEM_INSTRUCTION = (
    "You are a research scout for Metis Advisory Group, a leadership and "
    "organizational-psychology consultancy that advises executives, founders, "
    "and boards. Find recent, real business developments a senior leader would "
    "recognize and that reward an organizational-psychology reading. Prefer "
    "substance over churn: leadership transitions, restructurings, culture and "
    "return-to-office shifts, enterprise AI adoption, governance and "
    "succession, notable management decisions.\n\n"
    "Every suggestion must map to exactly one of the five Metis Pillars:\n"
    "- Self-Mastery & Executive Psychology: the leader's inner work, "
    "regulation under pressure, knowing oneself in role\n"
    "- Strategic Thinking & Decision Architecture: how consequential decisions "
    "get framed and made\n"
    "- Communication, Influence & Relational Leadership: being understood, "
    "influence without performance\n"
    "- Team Dynamics & Culture Engineering: how groups actually move, the "
    "patterns under the org chart\n"
    "- Organizational Systems & Change Psychology: change that lasts, systems "
    "metabolising change\n\n"
    "Formats: 'essay' (a quarterly long-form piece worth 800-1500 words) or "
    "'field_note' (a short monthly observation, 150-400 words)."
)


def find_topics(theme: str = None, count: int = 5) -> list:
    """Return a list of topic briefings, each a dict with: headline, source,
    relevance_score, suggested_angle, suggested_pillar, suggested_format."""
    today = date.today()
    since = today - timedelta(days=LOOKBACK_DAYS)
    focus = (
        f' Focus specifically on developments related to: "{theme}".' if theme
        else " Cover a spread of industries and pillars, not five versions of "
             "the same story."
    )
    prompt = f"""Search for {count} real business developments reported between
{since.isoformat()} and {today.isoformat()} (the trailing three months) that a
senior leadership audience would find worth thinking about.{focus}

For each one, return an object with exactly these six keys:
- headline: the real development, in your own words
- source: the publication or outlet name
- relevance_score: integer 1-10, how well it rewards an organizational-
  psychology reading for leaders (not just how big the news was)
- suggested_angle: one specific sentence on the reading Metis could take,
  naming the underlying pattern -- not a generic summary
- suggested_pillar: exactly one of {PILLAR_NAMES}
- suggested_format: exactly one of {FORMATS}

Return ONLY a JSON array of {count} objects. No markdown code fences, no
preamble, no explanation - just the raw JSON array."""

    # The Flash model is a thinking model; with Google Search grounding it can
    # return finish_reason=STOP but empty text (the whole turn goes to thought
    # parts). Disabling thinking for this grounded call makes it emit the JSON
    # again. The writer agents keep thinking for draft quality.
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
    requested_theme = " ".join(sys.argv[1:]) or None
    print(f"Using model: {MODEL}")
    print(f"Lookback: last {LOOKBACK_DAYS} days")
    print(f"Theme filter: {requested_theme or '(none - spread across pillars)'}\n")
    briefing = find_topics(requested_theme)
    print(json.dumps(briefing, indent=2))
