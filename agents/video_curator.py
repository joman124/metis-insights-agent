# -*- coding: utf-8 -*-
"""
The Metis Video Curator agent: finds trending, viral AI videos on YouTube,
X/Twitter, and other social platforms, then posts them to the Metis LinkedIn
page with a sharp Metis-voice commentary caption -- the "AI Ecosystem" playbook
of riding hot clips for reach, done in Metis's measured register.

How it works:
  1. find_viral_videos() -- Gemini + Google Search grounding surfaces real,
     currently-viral AI video clips (title, creator, source URL, why it matters).
  2. select_top() -- picks the most on-brand candidate.
  3. draft_caption() -- writes Metis commentary through the same voice
     guardrails the text agents use (PLATFORM_RULES["video_caption"]).
  4. curate() -- assembles a post package, saves it to a review docx, and posts
     the commentary WITH A LINK BACK to the original creator via
     linkedin_publisher.post_text.

CONTENT RIGHTS: the default, safe behavior is a share-with-commentary post that
links to and credits the original creator. It does NOT re-upload the video file.
Native re-upload (which LinkedIn favors for reach) lives in
linkedin_publisher.post_video and is gated behind an explicit human approval,
because re-uploading someone else's copyrighted clip risks takedowns and breaks
platform terms. Use native re-upload only for clips Metis owns or has licensed.

Run:  python -m agents.video_curator ["optional focus topic"]
"""

import json
import os
import sys

from metis_voice_profile import (VOICE_SYSTEM_PROMPT, ANTI_AI_TELL_PROMPT,
                                  PLATFORM_RULES)
from guardrails import draft_with_guardrails
import engagement

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
WRITER_MODEL = os.getenv("GEMINI_WRITER_MODEL", "gemini-pro-latest")
SYSTEM_INSTRUCTION = VOICE_SYSTEM_PROMPT + "\n\n" + ANTI_AI_TELL_PROMPT

CAPTION_RULES = PLATFORM_RULES["video_caption"]
QUEUE_DOC = "Metis Video Queue.docx"

DISCOVERY_SYSTEM = (
    "You are a video scout for Metis Advisory Group, a strategy and "
    "leadership-psychology firm. You find real, currently-viral short videos "
    "about AI -- on YouTube, X/Twitter, TikTok, Instagram, LinkedIn -- that "
    "senior leaders are sharing and reacting to. You favor clips a measured "
    "advisory brand can credibly comment on (a striking demo, a leadership "
    "moment, a real workplace-AI story), not hype reels or ads."
)


def find_viral_videos(topic: str = None, count: int = 5) -> list:
    """Return a list of viral-video candidates, each a dict with: title,
    creator, platform, source_url, why_it_matters, relevance_score."""
    focus = (
        f' Focus specifically on: "{topic}".' if topic
        else " Find what has gone viral in the past 7 days."
    )
    prompt = f"""Search for {count} real, currently-viral short videos about AI
that senior business leaders are sharing.{focus}

For each one, return an object with exactly these six keys:
- title: the video's real title or a short description of it
- creator: the channel / account / person who made it
- platform: youtube, x, tiktok, instagram, or linkedin
- source_url: the real link to the video
- why_it_matters: one sentence on why Metis's audience of executives cares
- relevance_score: integer 1-10, fit for a measured leadership-advisory brand

Only include videos you can point to a real URL for. Return ONLY a JSON array
of {count} objects. No markdown code fences, no preamble - just the raw JSON."""

    # Imported lazily so the module imports without google-genai installed
    # (tests exercise select_top/build_post without it); only this call needs it.
    from google.genai import types
    from gemini_client import generate

    raw = generate(
        MODEL,
        prompt,
        system_instruction=DISCOVERY_SYSTEM,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        disable_thinking=True,
    )
    return _parse_json_array(raw)


def select_top(videos: list) -> dict:
    """Pick the most on-brand candidate (highest relevance_score)."""
    if not videos:
        return None
    return max(videos, key=lambda v: v.get("relevance_score", 0))


def _build_caption_prompt(video: dict, feedback: str = None) -> str:
    revision_note = (
        f"\nA previous draft was rejected. Fix this before writing: {feedback}\n"
        if feedback else ""
    )
    return f"""Write a LinkedIn caption for the Metis page that reshares this
viral AI video with Metis's own commentary:

VIDEO: {video.get('title')}
CREATOR: {video.get('creator')}
WHY IT MATTERS: {video.get('why_it_matters')}
{revision_note}
You are not describing the video. You are adding the sharp advisory take that
makes a leader stop: what this clip really shows about how companies lead,
decide, or adopt AI. Assume the video is attached; do not summarize it
shot by shot.

Requirements:
- {CAPTION_RULES['min_words']} to {CAPTION_RULES['max_words']} words
- Open with one concrete, specific line, not a question
- Measured and confident. Anti-hype. No hustle language.
- Do NOT include the video link or the creator's name in your text; those are
  added separately as a credit line.
- End on a line that invites a reply
- Add {CAPTION_RULES['min_hashtags']} to {CAPTION_RULES['max_hashtags']}
  relevant hashtags on the last line
- No emoji

Write only the caption. No preamble, no explanation."""


def draft_caption(video: dict, max_attempts: int = 3) -> dict:
    """Generate-evaluate-revise loop for the commentary caption. Returns
    {"text", "attempts", "evaluation", "history"} from draft_with_guardrails."""
    return draft_with_guardrails(
        WRITER_MODEL,
        build_prompt=lambda feedback: _build_caption_prompt(video, feedback),
        system_instruction=SYSTEM_INSTRUCTION,
        max_em_dashes=CAPTION_RULES["max_em_dashes"],
        max_attempts=max_attempts,
        agent="video_curator",
        temperature=CAPTION_RULES["temperature"],
        # The caption is the post body, so it gets the same reach checks.
        extra_checks=lambda t: engagement.check(t, CAPTION_RULES),
    )


def _credit_line(video: dict) -> str:
    """A consistent attribution + link line appended to the commentary, so the
    original creator is always credited and the post links back to the source."""
    creator = video.get("creator", "the original creator")
    url = video.get("source_url", "")
    return f"Original video by {creator}: {url}".rstrip(": ").rstrip()


def build_post(video: dict, caption_text: str) -> dict:
    """Assemble the full LinkedIn post body (commentary + credit line) and the
    review package for the queue doc."""
    commentary = caption_text.strip() + "\n\n" + _credit_line(video)
    return {
        "video": video,
        "caption": caption_text.strip(),
        "commentary": commentary,
        "credit": _credit_line(video),
    }


def curate(topic: str = None) -> dict:
    """Full pipeline: find viral videos, pick the best, draft Metis commentary,
    save a review package, and post the commentary + source link to LinkedIn
    (dry run unless LINKEDIN_DRY_RUN=false). Native re-upload is NOT done here;
    it stays gated in linkedin_publisher.post_video. Returns the package plus
    the publish result."""
    from linkedin_publisher import post_text
    from doc_output import append_to_doc

    videos = find_viral_videos(topic)
    top = select_top(videos)
    if not top:
        raise SystemExit(
            "\n[VIDEO] No viral videos found to react to. Try again with a "
            "focus topic, e.g. python -m agents.video_curator \"AI agents\"."
        )

    drafted = draft_caption(top)
    package = build_post(top, drafted["text"])

    doc_body = (
        f"Video: {top.get('title')}\n"
        f"Creator: {top.get('creator')} ({top.get('platform')})\n"
        f"Source: {top.get('source_url')}\n"
        f"Why it matters: {top.get('why_it_matters')}\n\n"
        f"CAPTION:\n{package['commentary']}"
    )
    append_to_doc(QUEUE_DOC, top.get("title", "viral video"), doc_body)

    publish = post_text(package["commentary"])
    package["publish"] = publish
    package["evaluation"] = drafted["evaluation"]
    package["candidates"] = videos
    return package


def _parse_json_array(raw: str) -> list:
    """Strip markdown fences if the model added them anyway, then parse."""
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
            "\n[VIDEO] Gemini did not return valid JSON. Raw output:\n" + raw[:800]
        )
    if not isinstance(data, list):
        raise SystemExit(f"\n[VIDEO] Expected a JSON array of videos, got: {type(data)}")
    return data


if __name__ == "__main__":
    focus = " ".join(sys.argv[1:]) or None
    print(f"Discovery model: {MODEL} | Caption model: {WRITER_MODEL}")
    print(f"Focus: {focus or '(none - viral in the past 7 days)'}\n")

    result = curate(focus)
    v = result["video"]
    print("=" * 70)
    print(f"SELECTED: {v.get('title')} -- {v.get('creator')} ({v.get('platform')})")
    print(f"URL: {v.get('source_url')}")
    print("=" * 70)
    print("\nLINKEDIN POST BODY:\n")
    print(result["commentary"])
    e = result["evaluation"]
    status = "passed" if e["passed"] else "did not pass"
    print(f"\n[GUARDRAILS] caption {status}. voice_score={e['voice_score']}/10, "
          f"tone={e['tone']}")
    pub = result["publish"]
    if pub["dry_run"]:
        print(f"\n[LINKEDIN] DRY RUN -- saved to '{QUEUE_DOC}', not posted.")
    else:
        print(f"\n[LINKEDIN] Posted (id {pub['post_id']}).")
