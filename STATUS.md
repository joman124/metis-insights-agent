# STATUS

Current state of the Metis Insights Agent and the open work. Read this after
CLAUDE.md when picking the project back up.

## Done and on GitHub

Branch `claude/metis-insights-kaggle-adapt-ervcif` (this repo) holds the full
pipeline: Scout, Strategist, essay/field-note writers, Analyst, Orchestrator,
guardrails, `content_publisher` + `site_builder`, and the Streamlit UI. Plus:
- Auto-publish toggle in the UI (locked until real voice samples exist).
- `voice_reference/` loader reads `.txt` and `.docx` samples.
- Drafts tab is editable: revise a draft's text and title, then publish the
  edited version directly.

The companion repo **metis-website** (same branch name) renders the Insights
page from `content/insights-data.json` via `site/insights-loader.js`, with the
filter chips mapped to the five Metis Pillars.

## How publishing works

`content_publisher.promote_to_site()` writes `content/insights-data.json` and a
generated `insights/<slug>.html` into the metis-website checkout
(`METIS_SITE_DIR`, else `../metis-website`, else `./site_output/`), and records
`memory/content_history.json`. Making it live = commit + push metis-website.

## Open work (requested, not yet built)

### A. Voice (TOV) tuning toward the "Newman's Own" sample
Tone is ~80% there; John wants it to read like a specific "Newman's Own" doc.
- The doc (and other samples) must be in `voice_reference/` for the judge to
  score against it and for anyone to read its structure. Get it committed here.
- Then tighten `voice_profile.VOICE_SYSTEM_PROMPT` + `STYLE_GUIDE.md` to the
  sample's markers, recalibrate `CONTENT_RULES[...]['max_em_dashes']`, re-draft,
  compare, iterate. Having real samples flips `USING_PLACEHOLDER_REFERENCES`
  off and unlocks auto-publish.

### B. New "Case Studies" content line
A third content line analyzing specific companies / individual leaders,
mirroring the Newman's Own doc in BOTH tone and structure. Bigger; use plan
mode. Likely touch points:
- `voice_profile.CONTENT_RULES`: add a `case_study` format.
- New `agents/case_study_writer.py` (guardrail loop; prompt mirrors the
  Newman's Own structure -- needs that doc as the template) + metadata helper.
- `agents/scout.py`: optionally surface case-study subjects (companies/leaders).
- `agents/strategist.py`: cadence + pillar tagging for case studies.
- `agents/orchestrator.py`: new intent + handler; extend `_deliver`.
- `content_publisher.py` + `site_builder.py`: new `case_studies` section in the
  data schema (or a parallel `content/case-studies-data.json`) + article pages.
- `app.py`: surface case studies (drafts column, plan tab).
- metis-website: decide placement -- a new `case-studies.html` page + nav item
  (recommended, it's a distinct content line) vs a section inside Insights; add
  a loader + seed data + nav links across pages.
- Open questions for John: separate page or Insights section? Pillar-tagged, or
  filtered by company/industry?

## Constraints (do not relearn the hard way)

- All `.py` files must be pure ASCII (use `chr(0x2014)` etc.).
- `google-genai` SDK; model names only in `.env`.
- No live Gemini key in a cloud session (it is in John's local `.env`), so the
  Gemini-calling paths are verified on John's machine; no-API logic and the
  site render are verifiable in-session.
- Claude pushes to GitHub directly (see CLAUDE.md preferences). If a push is
  blocked, `add_repo` the repo into session scope, then set `origin` to
  `https://github.com/joman124/<repo>` (the session proxies github.com auth).
