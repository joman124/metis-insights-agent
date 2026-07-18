# -*- coding: utf-8 -*-
"""
The Metis Orchestrator: routes natural-language requests to the right agent.

Routing itself (route()) is deterministic keyword matching, not a Gemini call,
so it is fully unit-testable without an API key. Only the agent pipelines it
dispatches to (handle_request()) need one.

Run:  python -m agents.orchestrator "post a viral video about AI agents"
"""

import json
import re
import sys
import time

_TOPIC_PATTERNS = [
    re.compile(r"\babout\s+(.+)$", re.IGNORECASE),
    re.compile(r"\breact(?:ing)? to\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bon\s+(.+)$", re.IGNORECASE),
]


def _extract_topic(request: str):
    """Pull a topic out of phrasing like 'go viral about X'. Returns None if
    nothing matches, so callers can fall back to Scout."""
    for pattern in _TOPIC_PATTERNS:
        match = pattern.search(request)
        if match:
            return match.group(1).strip().strip(".\"'")
    return None


def route(request: str):
    """Classify a request into (intent, topic). Checked in this order so
    'viral video' routes to video (the more specific surface), and both win
    over a bare 'trending' lookup."""
    lowered = request.lower()

    if any(p in lowered for p in ("video", "clip", "reel")):
        return "video", _extract_topic(request)

    if any(p in lowered for p in ("viral", "go viral", "react to", "hot take")):
        return "viral", _extract_topic(request)

    if "trending" in lowered:
        return "trending", _extract_topic(request)

    return "unknown", _extract_topic(request)


def handle_request(request: str) -> str:
    """Route the request and run the matched agent pipeline. Imports agents
    lazily inside each handler so routing stays importable without an API key;
    only the branch that actually runs needs GEMINI_API_KEY set."""
    from observability import log_decision

    intent, topic = route(request)
    log_decision(
        agent="orchestrator", action="route",
        inputs={"request": request},
        decision={"intent": intent, "topic": topic},
    )

    if intent == "video":
        return _handle_video(topic)
    if intent == "viral":
        return _handle_viral(topic)
    if intent == "trending":
        return _handle_trending(topic)
    return ("[ORCHESTRATOR] Did not recognize that request. Try things like "
            "\"Go viral about X\", \"Post a viral video about Y\", or "
            "\"What's trending?\"")


def _handle_viral(topic) -> str:
    """Fast reaction to a hot topic: draft a viral LinkedIn post and auto-post
    it (dry run unless LINKEDIN_DRY_RUN=false), then draft a Substack Note for
    a human to post. If no topic was given, Scout picks the hottest one."""
    from agents.viral import draft_viral_linkedin, draft_note
    from linkedin_publisher import post_text
    from doc_output import append_to_doc
    from guardrails import CALL_PACING_SECONDS
    import safety
    import posting_policy
    import posts_ledger

    if not topic:
        from agents.scout import find_topics
        briefing = find_topics()
        if not briefing:
            return ("[ORCHESTRATOR] Scout found nothing hot to react to. Try "
                    "again with a specific topic, e.g. \"go viral about X.\"")
        topic = briefing[0].get("suggested_angle") or briefing[0].get("headline")
        time.sleep(CALL_PACING_SECONDS)

    verdict = safety.assess(topic)
    dup = posting_policy.is_duplicate(topic)
    warnings = []
    if dup["duplicate"]:
        warnings.append(f"Note: close to a recent post ('{dup['match']}').")

    li = draft_viral_linkedin(topic)
    time.sleep(CALL_PACING_SECONDS)
    note = draft_note(topic)
    append_to_doc("Metis LinkedIn Posts.docx", topic, li["text"])
    append_to_doc("Metis Substack Notes.docx", topic, note["text"])
    posts_ledger.add(topic, note["text"], "substack", status="queued")

    if not verdict["safe"]:
        posts_ledger.add(topic, li["text"], "linkedin", status="queued")
        li_status = ("HELD for review (sensitive topic: " + verdict["reason"] +
                     "). Approve with: python review.py list")
    else:
        publish = post_text(li["text"])
        if publish["dry_run"]:
            posts_ledger.add(topic, li["text"], "linkedin", status="queued")
            li_status = ("Drafted and saved to 'Metis LinkedIn Posts.docx' (DRY "
                         "RUN -- not posted; queued for review).")
        else:
            rec = posts_ledger.add(topic, li["text"], "linkedin", status="posted")
            posts_ledger.mark_posted(rec["id"], publish["post_id"])
            li_status = f"Posted to the Metis page (id {publish['post_id']})."

    prefix = ("\n".join(warnings) + "\n\n") if warnings else ""
    return (
        f"[ORCHESTRATOR] {prefix}Viral reaction to: {topic}\n\n"
        f"LINKEDIN POST:\n{li['text']}\n\n{li_status}\n\n"
        f"SUBSTACK NOTE (saved to 'Metis Substack Notes.docx' to post):\n"
        f"{note['text']}"
    )


def _handle_video(topic) -> str:
    """Find a viral AI video, draft Metis commentary, and post it with a link
    back to the creator (dry run unless LINKEDIN_DRY_RUN=false)."""
    from agents.video_curator import curate

    package = curate(topic)
    v = package["video"]
    pub = package["publish"]
    if pub.get("held"):
        status = (f"HELD for review (sensitive: {pub.get('reason')}). "
                  "Approve with: python review.py list")
    elif pub["dry_run"]:
        status = ("Saved to 'Metis Video Queue.docx' (DRY RUN -- not posted; "
                  "set LINKEDIN_DRY_RUN=false to go live).")
    else:
        status = f"Posted to the Metis page (id {pub['post_id']})."
    return (
        f"[ORCHESTRATOR] Video reaction:\n"
        f"  {v.get('title')} -- {v.get('creator')} ({v.get('platform')})\n"
        f"  {v.get('source_url')}\n\n"
        f"LINKEDIN POST BODY:\n{package['commentary']}\n\n{status}"
    )


def _handle_trending(topic) -> str:
    from agents.scout import find_topics
    briefing = find_topics(topic)
    return "[ORCHESTRATOR] Trending for leaders:\n" + json.dumps(briefing, indent=2)


if __name__ == "__main__":
    user_request = " ".join(sys.argv[1:]) or "What's trending?"
    print(f"Request: {user_request}\n")
    print(handle_request(user_request))
