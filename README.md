# Metis Insights Agent

A multi-agent system that researches, plans, drafts, and voice-checks content
for the **Insights** section of the Metis Advisory Group website -- long-form
**essays** (about quarterly) and short **field notes** (about monthly), in the
Metis brand voice. John reviews and promotes; the system does the rest.

Adapted from the After Work / kaggle-agent-capstone pipeline: the generic
engine (research -> plan -> draft -> guardrail-check -> publish -> learn)
carried over; the voice, taxonomy, formats, and publishing target were
rewritten for Metis. See `PROJECT_BRIEF.md`, `ARCHITECTURE.md`, and
`STYLE_GUIDE.md`.

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env        # Windows  (cp on macOS/Linux)
# then edit .env: paste the SAME GEMINI_API_KEY used by the After Work project
python check_setup.py         # confirms the key works, lists callable models
```

## Run it

```bash
# The UI (recommended): ask the agent, review drafts, promote to the site
streamlit run app.py

# Or drive agents directly:
python -m agents.scout "return-to-office mandates"      # trending briefing
python -m agents.strategist                             # plan the cycle
python -m agents.essay_writer                           # draft one essay
python -m agents.field_note_writer                      # draft one field note
python -m agents.orchestrator "What should we publish this quarter?"
python content_publisher.py                             # show current site data
```

Drafts are written to `Insights Drafts.docx` for review. Promoting a draft
(from the UI) writes `content/insights-data.json` and a generated
`insights/<slug>.html` into your metis-website checkout.

## Publishing to the site

By default the publisher looks for a metis-website checkout beside this repo
(`../metis-website`) or at `METIS_SITE_DIR` in `.env`. Promote an approved
draft, then in the metis-website repo:

```bash
git add content/insights-data.json insights/
git commit -m "Publish: <title>"
git push
```

The Insights page renders the data file via `site/insights-loader.js`. If no
site checkout is found, promoted files land in `./site_output/` instead so
nothing is lost.

## Voice

The voice bar starts provisional: the judge scores against placeholder
excerpts from the site's marketing copy. Drop real Metis-voice samples into
`voice_reference/` (one `.txt` per sample) to replace them -- see that folder's
README. `STYLE_GUIDE.md` is the human-readable source of truth.

## Not built yet

- Email newsletter (deferred until there is a list).
- Real reader analytics feeding `memory/engagement_data.json` (the Analyst
  reads it; nothing writes it yet).
