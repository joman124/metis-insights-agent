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


def handle_request(request: str, auto_publish: bool = False) -> str:
    """Route the request and run the matched agent pipeline. Imports agents
    lazily inside each handler so routing stays importable without an API
    key; only the branch that actually runs needs GEMINI_API_KEY set.

    auto_publish: when True, a draft that PASSES the voice guardrails is
    promoted straight to the site (content/insights-data.json + article page)
    instead of only being saved to the review docx. Drafts that fail the
    guardrails always fall back to the docx, never auto-published."""
    from observability import log_decision

    intent, topic = route(request)
    log_decision(
        agent="orchestrator", action="route",
        inputs={"request": request, "auto_publish": auto_publish},
        decision={"intent": intent, "topic": topic},
    )

    if intent == "plan_cycle":
        return _handle_plan_cycle(auto_publish)
    if intent == "trending":
        return _handle_trending(topic)
    if intent == "essay":
        return _handle_essay(topic, auto_publish)
    if intent == "field_note":
        return _handle_field_note(topic, auto_publish)
    if intent == "engagement":
        return _handle_engagement()
    return ("[ORCHESTRATOR] Did not recognize that request. Try things like "
            "\"What should we publish this quarter?\", \"What's trending?\", "
            "\"Draft an essay about board AI governance\", or "
            "\"Write a field note about return-to-office\".")


def _deliver(fmt, topic, pillar, result, auto_publish, lines):
    """Route one finished draft to the site (if auto_publish and it passed the
    guardrails) or to the review docx (otherwise). Appends a status line."""
    from doc_output import append_to_doc

    text = result["text"]
    passed = result["evaluation"]["passed"]
    label = "[Essay] " if fmt == "essay" else "[Field note] "

    if auto_publish and passed:
        from content_publisher import promote_to_site
        res = promote_to_site(body=text, fmt=fmt, pillar=pillar)
        target = "site" if res["is_site"] else "site_output"
        lines.append("    -> published to %s: %s (\"%s\")"
                     % (target, res["entry"]["href"], res["entry"]["title"]))
        return

    append_to_doc(DRAFTS_DOC, label + topic, text)
    if auto_publish and not passed:
        lines.append("    -> did NOT pass guardrails; saved to docx for review "
                     "instead of publishing")
    else:
        lines.append("    -> draft saved to docx")


def _default_pillar_for(topic, briefing):
    """Best-effort pillar for an ad-hoc topic: match it against a Scout
    briefing item if one mentions it; otherwise fall back to the first pillar."""
    from pillars import PILLAR_NAMES
    if briefing:
        for item in briefing:
            if topic and item.get("suggested_angle") and topic.lower() in item["suggested_angle"].lower():
                return item.get("suggested_pillar", PILLAR_NAMES[0])
    return PILLAR_NAMES[0]


def _handle_plan_cycle(auto_publish=False) -> str:
    from agents.scout import find_topics
    from agents.strategist import plan_cycle
    from agents.analyst import get_pillar_adjustments
    from agents.essay_writer import draft_essay
    from agents.field_note_writer import draft_field_note
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
            result = draft_essay(topic, pillar)
        else:
            result = draft_field_note(topic, pillar)
        _deliver(item["format"], topic, pillar, result, auto_publish, lines)

    if auto_publish:
        lines.append("Auto-publish on: passing drafts went to the site. Commit "
                     "and push metis-website to make them live.")
    else:
        lines.append("Drafts saved to '%s'. Review, then promote approved "
                     "pieces from the UI." % DRAFTS_DOC)
    return "\n".join(lines)


def _handle_trending(topic) -> str:
    from agents.scout import find_topics
    briefing = find_topics(topic)
    return "[ORCHESTRATOR] Trending (trailing 3 months):\n" + json.dumps(briefing, indent=2)


def _handle_essay(topic, auto_publish=False) -> str:
    from agents.scout import find_topics
    from agents.essay_writer import draft_essay

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

    result = draft_essay(topic, pillar)
    lines = [f"[ORCHESTRATOR] Essay draft ({pillar}):"]
    _deliver("essay", topic, pillar, result, auto_publish, lines)
    return "\n".join(lines) + "\n\n" + result["text"]


def _handle_field_note(topic, auto_publish=False) -> str:
    from agents.scout import find_topics
    from agents.field_note_writer import draft_field_note

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

    result = draft_field_note(topic, pillar)
    lines = [f"[ORCHESTRATOR] Field note draft ({pillar}):"]
    _deliver("field_note", topic, pillar, result, auto_publish, lines)
    return "\n".join(lines) + "\n\n" + result["text"]


def _handle_engagement() -> str:
    from agents.analyst import weekly_summary
    return weekly_summary()


if __name__ == "__main__":
    user_request = " ".join(sys.argv[1:]) or "What should we publish this quarter?"
    print(f"Request: {user_request}\n")
    print(handle_request(user_request))
