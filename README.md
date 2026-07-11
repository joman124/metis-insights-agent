# metis-insights-agent

Fast, on-brand "virality" agents for **Metis Advisory Group**. They react to hot
topics quickly to drive views and engagement for the Metis LinkedIn page (text
and video) and Substack (Notes), in Metis's measured, anti-hype voice.

This repo is self-contained. It mirrors the proven agent infrastructure from the
After Work project (`gemini_client`, `guardrails`, `doc_output`, `observability`)
but ships its own Metis voice profile and its own agents.

## The agents

- **Scout** (`agents/scout.py`) - finds what executives, founders, and boards are
  talking about right now, via Gemini + Google Search grounding.
- **Viral** (`agents/viral.py`) - turns a hot topic into a short LinkedIn post
  and a Substack Note, both drafted through the shared voice guardrails so
  "viral" still sounds like Metis.
- **Video Curator** (`agents/video_curator.py`) - finds trending viral AI videos
  on YouTube / X / TikTok, writes a Metis-voice commentary caption, and posts it
  to the Metis page **with a link back to the original creator** (the "AI
  Ecosystem" reshare playbook, done in Metis's register).
- **Orchestrator** (`agents/orchestrator.py`) - routes natural language:
  "go viral about X", "post a viral video about Y", "what's trending?".

Every generated draft passes an LLM-as-judge voice score against real Metis copy
(`metis_voice_profile.REFERENCE_PASSAGES`); it will not post content that reads
as generic or salesy.

## Posting

- **LinkedIn** posting is automatic through `linkedin_publisher.py` (the official
  Posts API, authored as the Metis **organization** page).
- **Substack** Notes are saved to a review docx for a human to post, because
  Substack has no official posting API.

**Safety: posting defaults to DRY RUN.** Nothing goes live until you set
`LINKEDIN_DRY_RUN=false` in `.env`. In dry run the agents build and log the exact
payload and save drafts, but post nothing.

**Content rights (video):** the default video behavior is a share-with-commentary
post that links to and credits the original creator; it does not re-upload the
clip. Native re-upload (`linkedin_publisher.post_video`) is gated behind an
explicit `approve=True` and is only for clips Metis owns or has licensed -
re-uploading someone else's copyrighted video risks takedowns and breaks
platform terms.

## Setup

1. Create and activate a virtual environment, then install deps:
   ```
   python -m venv .venv
   .venv\Scripts\activate      (Windows)   |   source .venv/bin/activate  (mac/Linux)
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`.
   Run `python check_setup.py` to confirm the key and see available models.
3. Leave `LINKEDIN_DRY_RUN=true` until you have a LinkedIn token (below).

## Going live on LinkedIn (one-time, manual)

Auto-posting needs a LinkedIn access token; this is a manual OAuth step:

1. Create a LinkedIn developer app and associate it with the Metis Company Page.
2. Request the **Community Management API** product and the
   `w_organization_social` scope; make the app an admin of the page.
3. Run the OAuth flow to get an access token.
4. In `.env`, set `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_ACTOR_URN`
   (`urn:li:organization:<your page id>`), and `LINKEDIN_DRY_RUN=false`.

## Run it

```
python -m agents.scout "AI agents"
python -m agents.viral "a survey says most AI pilots never reach production"
python -m agents.video_curator "AI in the enterprise"
python -m agents.orchestrator "go viral about the new AI coding study"
python -m agents.orchestrator "post a viral video about AI agents"
```

Drafts land in `Metis LinkedIn Posts.docx`, `Metis Substack Notes.docx`, and
`Metis Video Queue.docx`; every decision is logged to `logs/agent_trace.jsonl`.
