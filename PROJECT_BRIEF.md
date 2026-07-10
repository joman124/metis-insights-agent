# PROJECT_BRIEF.md -- Metis Insights Agent

## The business

**Metis Advisory Group** (metisag.com) is a leadership and organizational-
psychology consultancy founded by Dr. John Mansoor. It advises executives,
founders, and boards -- executive coaching, organizational consulting,
leadership development, retainer advisory, workshops and keynotes.

Tagline: **"Wisdom at Work. Guided by Insight. Grounded in Humanity."**
Brand line: *"Change rarely fails for lack of strategy. It fails when insight
is missing."*

## The job to be done

Build out the **Insights** section of the site with a steady supply of
on-brand writing, without John having to draft each piece from scratch. The
system researches what leaders are thinking about, plans coverage across the
firm's five pillars, drafts in the Metis voice, checks the draft against that
voice, and hands John reviewable drafts. John approves and promotes; the piece
lands on the site.

## What the audience gets

Two formats, matched to the existing Insights page design:

- **Essays** -- long-form (800-1500 words), published about **quarterly**.
  These are the featured and archive pieces. The site itself promises "three
  or four essays a year, when the work has taught us something worth holding
  onto." The cadence is deliberately slow; the pipeline respects that.
- **Field notes** -- short observations (150-400 words), published about
  **monthly**. The denser notes-list rows on the page.

Both are "written for leaders, not algorithms" -- no SEO padding, no hooks,
no hype.

## The five pillars (content taxonomy)

Straight from the site (`site/data.js` -> `window.METIS.PILLARS`), and the
single source of truth in `pillars.py`:

1. Self-Mastery & Executive Psychology
2. Strategic Thinking & Decision Architecture
3. Communication, Influence & Relational Leadership
4. Team Dynamics & Culture Engineering
5. Organizational Systems & Change Psychology

The Strategist rotates coverage across these; the Insights page filter chips
map one-to-one to them.

## Where topics come from

Scout searches **real business developments from the trailing three months** --
leadership transitions, restructurings, culture and return-to-office shifts,
enterprise AI adoption, governance and succession -- and reads them through an
organizational-psychology lens, tagging each to a pillar. Metis is not
chasing daily news; it is finding the quarter's developments worth a
considered take.

## Distribution

Primary home is the website Insights section. Approved pieces may later be
chopped up and reposted to LinkedIn or Substack, and folded into an email
newsletter -- but the **newsletter is deferred** until there is an email list
to send to. Each essay/field note gets a real permalink page so any future
repost has something to link back to.

## Scope guardrails

- Newsletter: out of scope for now.
- No autonomous publishing: John reviews drafts and promotes deliberately.
- No secondary Metis brands or offerings pulled in; stay on the Insights job.
