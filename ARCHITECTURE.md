# ARCHITECTURE.md -- Metis Insights Agent

## The flow

```
                 +-------------------+
   request  -->  |   Orchestrator    |  deterministic keyword routing (no LLM)
                 +---------+---------+
                           |
          +----------------+---------------------------+
          |                |                           |
     +----v----+     +-----v-----+               +-----v-----+
     |  Scout  |     | Strategist|               |  Analyst  |
     | (LLM +  |     | (pure     |<-- adjustments--| (pure     |
     | search) |     |  logic)   |   (+1/-1/0)    |  logic)   |
     +----+----+     +-----+-----+               +-----------+
          | briefing       | cycle plan (calendar.json)
          +-------+--------+
                  |
         +--------v---------+        +--------------------+
         |  Essay Writer /  |  uses  |    guardrails      |
         | Field Note Writer|------->| generate-evaluate- |
         | (LLM, pro model) |        |  revise + judge    |
         +--------+---------+        +--------------------+
                  | draft text
                  v
        Insights Drafts.docx  (John reviews)
                  |
                  v  promote (from the UI)
        +-------------------------+
        |   content_publisher     |  writes into metis-website checkout
        |   + site_builder        |
        +-----------+-------------+
                    |
     content/insights-data.json  +  insights/<slug>.html
                    |
              (John commits + pushes to metis-website)
```

## Agents and modules

| File | Role | LLM? |
|------|------|------|
| `agents/scout.py` | Finds trailing-3-month business developments via Gemini + Google Search grounding; tags each to a pillar and a format. | Yes (Flash, grounding, thinking off) |
| `agents/strategist.py` | Plans one cycle: balances pillars over a rolling window, applies cadence (quarterly essay / monthly field note), matches Scout topics. Writes `calendar.json`. | No |
| `agents/essay_writer.py` | Drafts long-form essays through the guardrail loop. Also `propose_metadata()` (title + dek) at promote time. | Yes (pro model) |
| `agents/field_note_writer.py` | Drafts short field notes through the guardrail loop. Also `propose_title()`. | Yes (pro model) |
| `agents/analyst.py` | Reads reader engagement, computes per-pillar read-through vs a target, emits `+1/-1/0` pillar adjustments + a summary. | No |
| `agents/orchestrator.py` | Routes NL requests to the above; `route()` is deterministic and unit-testable. | No (routing) |
| `guardrails.py` | Generate-evaluate-revise loop; first-pass rule checks + LLM-as-judge voice score. Brand-agnostic; imports brand data from `voice_profile.py`. | Yes (judge, Flash, temp 0) |
| `voice_profile.py` | The Metis voice: system prompts, banned phrases, antithesis patterns, reference passages (+ loader), judge instruction, per-format `CONTENT_RULES`. | -- |
| `pillars.py` | The five Metis Pillars (single source of truth, mirrors site `data.js`). | -- |
| `content_publisher.py` | `promote_to_site()`: writes `insights-data.json`, generates the article page, records history. | Only if title/dek omitted |
| `site_builder.py` | Slugs, read-time, paragraph HTML, and the standalone article-page template. | No |
| `gemini_client.py` | Shared Gemini wrapper: retry/backoff, plain-English errors, thinking toggle. | -- |
| `observability.py` | Appends every decision to `logs/agent_trace.jsonl`. | No |
| `doc_output.py` | Appends drafts to `Insights Drafts.docx`. | No |
| `app.py` | Streamlit UI: ask-the-agent + plan / drafts / trace tabs + promote button. | Wraps the above |

## Cadence knobs (editorial, tune in `agents/strategist.py`)

- `FIELD_NOTES_PER_CYCLE = 1` -- short notes per monthly cycle.
- `ESSAY_INTERVAL_DAYS = 90` -- an essay is planned only if none published in
  the trailing 90 days (quarterly).
- `PILLAR_WINDOW_DAYS = 365` -- window for balancing pillar coverage (long,
  because Metis publishes slowly).

The "right" cadence is an editorial call. These constants are the dials.

## Memory (JSON state, in `memory/`)

- `calendar.json` -- the current cycle plan: list of
  `{slot, format, pillar, topic, source_headline}`. Overwritten each plan run.
- `content_history.json` -- one entry per promoted piece:
  `{title, date, pillar, format, href, status}`. Feeds the Strategist's pillar
  balance and cadence checks. Written by `content_publisher.record_publish()`.
- `pillar_tracker.json` -- snapshot of per-pillar counts (debug view),
  overwritten by the Strategist.
- `engagement_data.json` -- per-piece reader metrics
  `{pillar, format, views, reads, avg_seconds}`. Read by the Analyst. **Nothing
  writes it yet** -- wire real analytics in here (see TODO in `analyst.py`).

## Publishing model (no CMS)

`content_publisher.resolve_site_dir()` locates a metis-website checkout
(`METIS_SITE_DIR`, else `../metis-website`, else falls back to `./site_output/`).
Promoting an approved draft:

1. builds a structured entry (slug, title, dek, read-time, `body_html`, pillar
   `topic` key, byline);
2. slots it into `content/insights-data.json` (`featured` / `essays` / `notes`);
3. writes `insights/<slug>.html` from `site_builder.render_article()`;
4. records the publish in `content_history.json`.

On the site, `site/insights-loader.js` fetches `insights-data.json` and renders
the featured essay, the essay grid, and the notes list, tagging each item with
its pillar `key` so the existing filter chips work. If the fetch fails
(e.g. opened over `file://`), the hardcoded fallback markup in `insights.html`
remains. Committing/pushing to metis-website is manual and deliberate.

## Tech stack

Gemini via `google-genai`; Streamlit UI; JSON files for memory; `python-docx`
for review drafts. No database, no server. The live site stays static
HTML/CSS/JS -- article pages are generated at publish time, not in the browser.
