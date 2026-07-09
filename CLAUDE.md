# CLAUDE.md -- Metis Insights Agent

This file orients Claude Code to the project. Read it first, then
`PROJECT_BRIEF.md` and `ARCHITECTURE.md` before writing code.

## What this project is

A multi-agent AI system that researches, plans, drafts, and voice-checks
content for the **Insights** section of the Metis Advisory Group website
(metisag.com). It produces long-form **essays** (published about quarterly)
and short **field notes** (about monthly), in the Metis brand voice, and
promotes approved pieces into the static site as a JSON data file plus a
generated article page.

John reviews and promotes. The system does everything else.

This project is adapted from the "After Work" / kaggle-agent-capstone
pipeline. The generic engine (research -> plan -> draft -> guardrail-check ->
output -> learn) carried over; the voice, the taxonomy, the formats, and the
publishing target were rewritten for Metis.

## Who the user is

Dr. John Mansoor, Founding Partner of Metis Advisory Group. He prompts and
reviews; he is not a developer. Write code that runs cleanly the first time
and explain what to run in plain steps. He is on Windows, Python 3.14,
building locally in a venv.

## Critical voice rule

All generated content must sound like Metis, not like generic AI. Two layers,
both in `voice_profile.py`:

1. `VOICE_SYSTEM_PROMPT` -- the positive target (restrained, aphoristic,
   precise, written for leaders; names the mechanism under a behavior; does
   not moralize).
2. `ANTI_AI_TELL_PROMPT` -- the negative target (strip machine fingerprints).

The human-readable reference is `STYLE_GUIDE.md`. The voice judge scores
drafts against `REFERENCE_PASSAGES`, which are placeholder site-copy excerpts
until real samples are dropped into `voice_reference/` (see that folder's
README). The banned-phrase list and guardrails enforce the voice mechanically.

## Hard technical constraints (inherited, still true)

1. **All source `.py` files must be pure ASCII.** Never put a raw em-dash,
   curly quote, or other non-ASCII byte in a `.py` file. Use `chr(0x2014)`
   etc. Keep `# -*- coding: utf-8 -*-` at the top of every `.py` file.
   (`.md`, `.json`, `.txt`, `.html` files may use UTF-8.)
2. **Use the `google-genai` SDK, not `google-generativeai`.** Import as
   `from google import genai`.
3. **Model names live in `.env`.** `GEMINI_MODEL` (Flash) for Scout and the
   voice judge; `GEMINI_WRITER_MODEL` (a pro model) for the essay/field-note
   writers. Never hard-code model names. `check_setup.py` lists what a key
   can call. Reuse the same key as the After Work project.
4. **Free tier rate-limits aggressively.** Retry-with-backoff on 503/500 and
   a pause between calls live in `gemini_client.py` / `guardrails.py`. Fail
   with plain-English messages on 429/404/auth -- never a raw traceback.
5. **Never put secrets in code.** The API key is in `.env`, which is gitignored.

## The taxonomy: five Metis Pillars

The single source of truth is `pillars.py`, which mirrors
`window.METIS.PILLARS` in the metis-website repo (`site/data.js`). Every agent
imports the pillar list from there. The pillar `key` doubles as the site
filter-chip `data-topic` value. Do not redefine the pillar list anywhere else.

## How content reaches the site

There is no CMS. `content_publisher.promote_to_site()` writes an entry into
`content/insights-data.json` and generates `insights/<slug>.html` inside a
local metis-website checkout (found via `METIS_SITE_DIR`, else
`../metis-website`, else `./site_output/`). The Insights page renders that
JSON via `site/insights-loader.js`. Committing and pushing those files to
metis-website is a **deliberate manual step** -- this tool never runs git.

## Current state

The full pipeline is built: Scout (`agents/scout.py`), Strategist
(`agents/strategist.py`), Essay Writer (`agents/essay_writer.py`), Field Note
Writer (`agents/field_note_writer.py`), Analyst (`agents/analyst.py`), and the
Orchestrator (`agents/orchestrator.py`), all wired to a Streamlit UI
(`app.py`) and the publisher (`content_publisher.py` + `site_builder.py`).
Guardrails and the Gemini client carried over unchanged in behavior.

Open follow-ups: real voice samples in `voice_reference/`; wiring real reader
analytics into `memory/engagement_data.json` (the Analyst reads it but nothing
writes it yet); an email newsletter (deferred until there is a list).

## Working relationship

John engages directly with critique and makes clear decisions. Honest
pushback is welcomed. Do not pad responses. Build outward -- resist
over-polishing any one step.
