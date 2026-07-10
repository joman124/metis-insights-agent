# STATUS

Current state of the Metis Insights Agent and the open work. Read this after
CLAUDE.md when picking the project back up.

## Done and pushed

Pipeline: Scout, Strategist, essay/field-note/case-study writers, Analyst,
Orchestrator, guardrails, `content_publisher` + `site_builder`, and the
Streamlit UI. Plus:
- Auto-publish toggle in the UI (unlocked -- a real voice sample is in
  `voice_reference/`, see below).
- `voice_reference/` loader reads `.txt` and `.docx` samples.
- Drafts tab is editable: revise a draft's text and title, then publish the
  edited version directly. Three columns now: Essays, Case studies, Field
  notes.

The companion repo **metis-website** renders the Insights page from
`content/insights-data.json` via `site/insights-loader.js`, with the filter
chips mapped to the five Metis Pillars. Case studies are a section on
`insights.html` (not a separate page, per John's call), pillar-tagged like
the other two formats, hidden until the first one is published.

## How publishing works

`content_publisher.promote_to_site()` writes `content/insights-data.json` and a
generated `insights/<slug>.html` into the metis-website checkout
(`METIS_SITE_DIR`, else `../metis-website`, else `./site_output/`), and records
`memory/content_history.json`. Making it live = commit + push metis-website.

## A. Voice (TOV) tuning toward the "Newman's Own" sample -- done

`voice_reference/01-newmans-own-culture-case-study.docx` is the first real
sample; the judge scores against it, `USING_PLACEHOLDER_REFERENCES` is False.
`voice_profile.VOICE_SYSTEM_PROMPT` and `STYLE_GUIDE.md` were tightened
toward its markers (anchor claims to a named person/date/decision, quote
attributed sources, vary sentence rhythm). `max_em_dashes` was checked
against the sample's actual usage and left unchanged (already calibrated).

One deliberate non-change worth knowing: the sample uses "not X, but Y"
constructions six times in ~1,000 words -- exactly what the antithesis
guardrail hard-fails on. Left the ban in place for generated drafts rather
than loosening it (a human source gets more latitude than a model reaching
for that rhythm as a crutch). Reverse this in `voice_profile.ANTITHESIS_PATTERNS`
if John disagrees.

## B. "Case Studies" content line -- done

`agents/case_study_writer.py` drafts a close analysis of one named company or
leader, structured to mirror the Newman's Own sample (section headers,
mechanism-naming, a section addressed to the reader, a named tension) rather
than just its tone. Decisions made along the way, flagged here in case John
wants to revisit any of them:

- **Placement**: a section within `insights.html`, not a separate page (John's
  call).
- **Tagging**: pillar-tagged like essays/notes, reusing the existing filter
  chips (John's call).
- **Cadence**: `CASE_STUDY_INTERVAL_DAYS = 90` in `agents/strategist.py`
  (quarterly, same as essays) -- a default, not something John specified.
- **Accuracy**: this writer has no search grounding of its own. A case study
  names a real subject, so hallucinated facts are a bigger risk than in an
  essay's abstract argument. When Scout supplies a `suggested_subject` with a
  grounded headline, that headline is passed through as `research_notes` and
  the prompt is told to stay inside it; without research_notes, the prompt is
  told to stick to well-established public knowledge rather than invent
  specifics. Worth testing against a real subject before trusting output
  unreviewed.
- Ad hoc requests ("write a case study about X" / "analyze X") work from the
  UI's ask-the-agent box and route through `agents/orchestrator.py`'s new
  `case_study` intent.

## Open follow-ups

- Broaden `voice_reference/` past the one sample when more real writing
  exists -- strengthens the judge's reference set for all three formats.
- Wire real reader analytics into `memory/engagement_data.json` (the Analyst
  reads it but nothing writes it yet).
- Email newsletter (deferred until there is a list).
- Once a real case study is drafted, sanity-check the header-detection
  heuristic in `site_builder.case_study_body_html()` against actual model
  output -- it is a plausible pattern-match on section-header shape (short
  line, Title Case, no ending punctuation), not a hard contract with the
  writer prompt.

## Constraints (do not relearn the hard way)

- All `.py` files must be pure ASCII (use `chr(0x2014)` etc.).
- `google-genai` SDK; model names only in `.env`.
- No live Gemini key in a cloud session (it is in John's local `.env`), so the
  Gemini-calling paths are verified on John's machine; no-API logic and the
  site render are verifiable in-session.
- Claude pushes to GitHub directly (see CLAUDE.md preferences).
