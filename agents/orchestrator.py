# -*- coding: utf-8 -*-
"""
The Orchestrator: routes natural-language requests to the right agent(s).

Routing itself (route()) is deterministic keyword matching, not a Gemini
call, so it is fully unit-testable without an API key. Only the agent
pipelines it dispatches to (handle_request()) need one.

Drafts are written to a single review document ("Insights Drafts.docx"),
headed "[Essay] ..." or "[Field note] ..." so the Streamlit UI can section
them. Nothing is promoted to the live site here -- John reviews the docx,
then promotes approved pieces from the UI (content_publisher.promote_to_site).

Run:  python -m agents.orchestrator "What should we publish this quarter?"
"""

import json
import re
import sys
import time

DRAFTS_DOC = "Insights Drafts.docx"

_TOPIC_PATTERNS = [
    re.compile(r"\babout\s+(.+)$", re.IGNORECASE),
    re.compile(r"\breacting to\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bon\s+(.+)$", re.IGNORECASE),
]


def _extract_topic(request: str):
    """Pull a topic out of phrasing like 'write a field note about X'.
    Returns None if nothing matches, so callers can fall back to Scout."""
    for pattern in _TOPIC_PATTERNS:
        match = pattern.search(request)
        if match:
            return match.group(1).strip().strip(".\"'")
    return None


def route(request: str):
    """Classify a request into (intent, topic). Checked in this order so more
    specific phrasing (plan, trending) wins over a bare format-name match."""
    lowered = request.lower()

    if any(p in lowered for p in ("what should we publish", "what should i publish",
                                  "plan the quarter", "plan this quarter",
                                  "this quarter", "this cycle", "plan the cycle",
                                  "content plan")):
        return "plan_cycle", None

    if any(p in lowered for p in ("trending", "what's happening", "whats happening",
                                  "in the news", "scout")):
        return "trending", _extract_topic(request)

    if "essay" in lowered:
        return "essay", _extract_topic(request)

    if "field note" in lowered or "note" in lowered:
        return "field_note", _extract_topic(request)

    if any(p in lowered for p in ("engagement", "performance", "numbers",
                                  "metrics", "read-through", "how are we doing")):
        return "engagement", None

    return "unknown", _extract_topic(request)


def handle_request(request: str) -> str:
    """Route the request and run the matched agent pipeline. Imports agents
    lazily inside each handler so routing stays importable without an API
    key; only the branch that actually runs needs GEMINI_API_KEY set."""
    from observability import log_decision

    intent, topic = route(request)
    log_decision(
        agent="orchestrator", action="route",
        inputs={"request": request},
        decision={"intent": intent, "topic": topic},
    )

    if intent == "plan_cycle":
        return _handle_plan_cycle()
    if intent == "trending":
        return _handle_trending(topic)
    if intent == "essay":
        return _handle_essay(topic)
    if intent == "field_note":
        return _handle_field_note(topic)
    if intent == "engagement":
        return _handle_engagement()
    return ("[ORCHESTRATOR] Did not recognize that request. Try things like "
            "\"What should we publish this quarter?\", \"What's trending?\", "
            "\"Draft an essay about board AI governance\", or "
            "\"Write a field note about return-to-office\".")


def _default_pillar_for(topic, briefing):
    """Best-effort pillar for an ad-hoc topic: match it against a Scout
    briefing item if one mentions it; otherwise fall back to the first pillar."""
    from pillars import PILLAR_NAMES
    if briefing:
        for item in briefing:
            if topic and item.get("suggested_angle") and topic.lower() in item["suggested_angle"].lower():
                return item.get("suggested_pillar", PILLAR_NAMES[0])
    return PILLAR_NAMES[0]


def _handle_plan_cycle() -> str:
    from agents.scout import find_topics
    from agents.strategist import plan_cycle
    from agents.analyst import get_pillar_adjustments
    from agents.essay_writer import write_essay
    from agents.field_note_writer import write_field_note
    from doc_output import append_to_doc
    from guardrails import CALL_PACING_SECONDS

    briefing = find_topics()
    adjustments = get_pillar_adjustments()
    plan = plan_cycle(scout_briefing=briefing, pillar_adjustments=adjustments)

    lines = ["[ORCHESTRATOR] Cycle plan:"]
    for i, item in enumerate(plan):
        if i > 0:
            # Each item runs its own revise loop of Gemini calls; pause between
            # items too so a multi-item plan does not burst the per-minute cap.
            time.sleep(CALL_PACING_SECONDS)

        topic = item["topic"] or item["pillar"]
        pillar = item["pillar"]
        lines.append(f"  {item['slot']}: {pillar} ({item['format']}) - {topic}")

        if item["format"] == "essay":
            text = write_essay(topic, pillar)
            append_to_doc(DRAFTS_DOC, "[Essay] " + topic, text)
        else:
            text = write_field_note(topic, pillar)
            append_to_doc(DRAFTS_DOC, "[Field note] " + topic, text)

    lines.append("Drafts saved to '%s'. Review, then promote approved pieces "
                 "from the UI." % DRAFTS_DOC)
    return "\n".join(lines)


def _handle_trending(topic) -> str:
    from agents.scout import find_topics
    briefing = find_topics(topic)
    return "[ORCHESTRATOR] Trending (trailing 3 months):\n" + json.dumps(briefing, indent=2)


def _handle_essay(topic) -> str:
    from agents.scout import find_topics
    from agents.essay_writer import write_essay
    from doc_output import append_to_doc

    briefing = None
    if not topic:
        briefing = find_topics()
        essays = [b for b in briefing if b.get("suggested_format") == "essay"] or briefing
        if not essays:
            return "[ORCHESTRATOR] Scout found nothing to work from. Try a specific topic."
        topic = essays[0]["suggested_angle"]
        pillar = essays[0].get("suggested_pillar")
    else:
        pillar = _default_pillar_for(topic, briefing)

    text = write_essay(topic, pillar)
    append_to_doc(DRAFTS_DOC, "[Essay] " + topic, text)
    return f"[ORCHESTRATOR] Essay draft ({pillar}) saved to '{DRAFTS_DOC}':\n\n{text}"


def _handle_field_note(topic) -> str:
    from agents.scout import find_topics
    from agents.field_note_writer import write_field_note
    from doc_output import append_to_doc

    briefing = None
    if not topic:
        briefing = find_topics()
        notes = [b for b in briefing if b.get("suggested_format") == "field_note"] or briefing
        if not notes:
            return "[ORCHESTRATOR] Scout found nothing to work from. Try a specific topic."
        topic = notes[0]["suggested_angle"]
        pillar = notes[0].get("suggested_pillar")
    else:
        pillar = _default_pillar_for(topic, briefing)

    text = write_field_note(topic, pillar)
    append_to_doc(DRAFTS_DOC, "[Field note] " + topic, text)
    return f"[ORCHESTRATOR] Field note draft ({pillar}) saved to '{DRAFTS_DOC}':\n\n{text}"


def _handle_engagement() -> str:
    from agents.analyst import weekly_summary
    return weekly_summary()


if __name__ == "__main__":
    user_request = " ".join(sys.argv[1:]) or "What should we publish this quarter?"
    print(f"Request: {user_request}\n")
    print(handle_request(user_request))
