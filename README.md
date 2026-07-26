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

One virtualenv at the repo root serves **both** apps -- the studio runs them in
a single process, and `viral-agents/` deliberately has no venv of its own (a
second copy only caused version drift).

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
pip install -r viral-agents/requirements.txt

copy .env.example .env        # Windows  (cp on macOS/Linux)
# then edit .env: paste the SAME GEMINI_API_KEY used by the After Work project
python check_setup.py         # confirms the key works, lists callable models
```

Each app loads the `.env` beside it, so `viral-agents/.env` is separate and
needs the same key. Note that `check_setup.py` only proves a key can *list*
models; a key can list fine and still fail every generate call with
`403 PERMISSION_DENIED` if its project has been denied access.

## Run it

The normal way in is the **Metis Content Studio**: one dark dashboard with both
halves of the operation behind a sidebar you can switch between freely.

```bash
streamlit run dashboard.py       # or double-click "Metis Content Studio.bat"
```

| Sidebar page | What it does | How content goes out |
| --- | --- | --- |
| **Viral Content** | Hot-topic LinkedIn posts + Substack Notes (Create / Review) | Edit in the Review queue, then **Approve + post** publishes to the Metis LinkedIn page (honors `LINKEDIN_DRY_RUN`) |
| **Essays & Field Notes** | Long-form pieces for the website | Edit in the Drafts tab, then **Publish to site** writes the site data file + article page |

Both pages are edit-then-publish: whatever is in the box is what goes out.

The studio runs the two apps in one process, so it lives at the repo root and
each page keeps its own folder, `.env`, drafts, and memory. Either app still
runs standalone (`streamlit run app.py` here, or in `viral-agents/`).

### The system learns from your edits

Editing a draft before you publish it is the most honest feedback the writers
get, so it is captured (`edit_lessons.py`):

1. Save or publish an edited draft -> the before/after pair is recorded in
   `memory/edit_history.json`. Instant, no API call.
2. At the next draft run, those pairs are distilled into short standing
   corrections in `memory/edit_lessons.json` (one cheap Flash call).
3. Every later draft prompt carries those corrections, most-repeated first.

See what has been learned in the **"What the writers have learned from your
edits"** panel on either page. Corrections are style and structure rules, never
topic content, and each page learns separately -- a LinkedIn hook rule should
not reshape a quarterly essay. Delete a line from `edit_lessons.json` to drop
a lesson; the loop degrades to silence if anything fails, and never blocks a
save, a post, or a draft.

```bash
streamlit run app.py             # just the essays/field-notes app

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
