# Case Studies: content-architecture decision doc

**Status:** DECIDED — Option B on all three · **Owner:** metis-insights-agent · **Date:** 2026-10-14 · **Decided:** 2026-10-17

Metis wants a third content line beyond essays and field notes: **Case Studies** of
companies and individual leaders, written in the same voice the Newman's Own sample
anchors. Two architectures are live. Each is buildable; they differ in where the pages
live, how much agent code is net-new, and how confidentiality is handled. This doc lays
out both so the choice is one focused read. Nothing gets built until the three questions
at the end are answered.

Grounding (today's system):

- Two content types exist in `CONTENT_RULES` (`voice_profile.py`): `essay` (800–1500 words,
  ~quarterly, featured + archive) and `field_note` (150–400 words, ~monthly, the notes
  list). Each carries its own word band, temperature, and em-dash ceiling.
- The pipeline is Scout (sources angles) → Strategist (pillar balance) → Essay/Field-note
  Writer, all through the `draft_with_guardrails()` generate-evaluate-revise loop.
- `content_publisher.promote_to_site(body, fmt, pillar, ...)` writes one entry into
  `content/insights-data.json` and a standalone `insights/<slug>.html` into a metis-website
  checkout, then that repo is committed and pushed; production follows `main`.
- Entries are tagged by **pillar** only: `topic = key_for(pillar)` drives the Insights
  filter chips, mirroring `window.METIS.PILLARS` in the site's `site/data.js`. Pillars are
  defined once, in `pillars.py`.

---

## Option A — separate `/case-studies` section, tagged by company and industry

A distinct part of the website with its own landing page and its own taxonomy (company,
industry), parallel to `/insights` rather than inside it.

### Page structure

- `case-studies/index.html` — a landing grid of case-study cards, with filter chips for
  **industry** (and optionally a company directory), styled from the same tokens in
  `colors_and_type.css` as the Insights page.
- `case-studies/<slug>.html` — one page per case study. Longer than an essay; room for a
  situation → intervention → outcome arc, a pull quote, and an attribution line.
- A new data file, `content/case-studies-data.json`, holding its own entry schema:
  `company`, `industry`, `leader_role`, plus the existing title/dek/body/slug/read_time
  fields. Pillar becomes optional metadata rather than the primary axis.
- A nav link to `/case-studies` added to the site header.

### How the agent generates it, relative to essays/field notes

Most net-new work of the two options.

- New `CONTENT_RULES["case_study"]` entry: a longer word band (roughly 600–1200), its own
  temperature and em-dash ceiling, reusing the same guardrails loop.
- New `agents/case_study_writer.py`, modeled on `essay_writer.py`, but prompted for the
  situation/intervention/outcome structure instead of a single argument.
- Scout and Strategist need a second axis. The Strategist today balances by pillar; here it
  would balance (or at least record) by **industry and company**, so a new taxonomy lives
  alongside `pillars.py` rather than inside it.
- `content_publisher` needs a parallel `promote_case_study()` path: a second data file, a
  second article template in `site_builder`, and a second nav/landing surface. This roughly
  doubles the publish plumbing.

### Anonymization / sourcing rules

Hardest confidentiality posture, because named company + industry is the whole point.

- **Named only with written client consent.** No company or leader is named without an
  on-file, signed release. Default state is unpublished.
- Where consent is withheld but the story is still worth telling, fall back to a
  **de-identified profile**: "a mid-market healthcare operator," no logo, no founder name,
  figures rounded or banded so they can't be back-solved.
- A consent field on every entry (`consent: named | anonymized | unpublished`) gates
  promotion: the publisher refuses to write a named page without `consent: named`.
- No real client metrics, quotes, or internal detail until the release covers them.

---

## Option B — Case Studies as a content type inside Insights, tagged by pillar

Case Studies become a third `fmt` next to `essay` and `field_note`, living on the existing
Insights page and tagged by the five Metis pillars like everything else.

### Page structure

- No new section. A case study renders as an Insights article (`insights/<slug>.html`),
  reusing the existing article template.
- On the Insights index it appears as a card with a "Case Study" format label, filtered by
  the **same pillar chips** already on the page. Optionally a format toggle (Essays /
  Field Notes / Case Studies) alongside the pillar filter.
- It slots into `content/insights-data.json` under a new `case_studies` bucket (or the
  existing `essays` bucket with `format: "case_study"`), no new data file.

### How the agent generates it, relative to essays/field notes

Least net-new work — it extends the pipeline rather than forking it.

- Add `CONTENT_RULES["case_study"]` and an `agents/case_study_writer.py` that reuses the
  same `draft_with_guardrails()` loop, as the field-note writer already does.
- Scout and Strategist are **unchanged in shape**: a case study is sourced and
  pillar-balanced exactly like an essay. One more branch in `orchestrator.route()`
  ("case study" → `case_study`) and `_deliver`.
- `promote_to_site()` already takes `fmt` and `pillar`; it needs a `case_study` branch for
  bucketing and read-time, but no second data file, template family, or nav surface. The
  publish path stays single.

### Anonymization / sourcing rules

Same confidentiality duty, but the pillar framing makes de-identification the natural
default rather than the exception.

- Because the lens is a **pillar** (e.g. "Change Psychology"), not a company name, the
  piece reads as "a pattern I saw in change work," and the client can stay anonymous
  without the page feeling hollow.
- Default posture is **anonymized**: role + sector + situation, no names, figures banded.
- Naming a client still requires written consent, enforced by the same `consent` gate —
  but it is the opt-in, not the baseline.
- Reuses the existing voice guardrails (anchor claims to a named person/date, quote
  sources) with one added rule: named detail only where a release exists.

---

## Trade-off at a glance

| | A — separate section | B — type in Insights |
|---|---|---|
| Primary tag | company + industry | Metis pillar |
| New agent code | writer + second taxonomy + second publish path | writer + one route branch |
| Website work | new section, data file, template, nav | reuses Insights surface |
| Confidentiality default | named (needs consent) | anonymized (consent to name) |
| Best when | Case Studies are a marketing showcase of named clients | Case Studies are teaching material under the same banner as essays |

Recommendation (reversible): **start with B.** It ships with the least new code, keeps one
publish path, and makes anonymity the default — which is the safer confidentiality posture
while real client releases don't yet exist. If named, logo-bearing showcases later become a
business need, the entries can be migrated to a dedicated `/case-studies` section without
rewriting the drafting pipeline.

---

## Questions for John

1. **Where do they live?** Case Studies as their own `/case-studies` section (Option A), or
   as a third content type inside Insights (Option B)?

2. **How are they tagged?** By **company and industry** (a new taxonomy beside `pillars.py`),
   or by **Metis pillar** (the existing chips, nothing new)?

3. **What's the confidentiality default?** **Named-by-default** (every case study names the
   client, and we only publish once a signed release is on file), or **anonymized-by-default**
   (de-identified role + sector, and naming a client is the opt-in that needs consent)?

---

## Decision (John, 2026-10-17)

**Option B on all three.** Build spec for next session:

1. **Where:** a third content type inside Insights. No new `/case-studies` section — case
   studies render as Insights articles (`insights/<slug>.html`) and appear on the Insights
   index with a "Case Study" format label.
2. **Tagging:** by **Metis pillar**, using the existing chips. No company/industry taxonomy
   beside `pillars.py`.
3. **Confidentiality:** **named-with-consent** — anonymized (role + sector + situation, figures
   banded) is the baseline; naming a client is the opt-in, gated by the `consent` field
   (`named | anonymized | unpublished`). The publisher refuses to write a named page without
   `consent: named`.

Build surface (from Option B above): add `CONTENT_RULES["case_study"]` + `agents/case_study_writer.py`
reusing `draft_with_guardrails()`; one branch in `orchestrator.route()`/`_deliver`; a `case_study`
branch in `promote_to_site()` for bucketing + read-time. Scout/Strategist unchanged. No second data
file, template family, or nav surface.
