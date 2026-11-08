# Insights coverage and a 12-month topic calendar

A planning document for the Insights engine. It counts what is published,
shows which pillars are thin, and proposes topics for December 2026 through
November 2027 so each writing session starts from a pick-and-approve step.

Nothing here is a draft and nothing here is approved for publication. Each
topic is a starting brief for the writers; John chooses, reorders or drops
them, and every piece still goes through review before it is promoted.

## 1. What is published today

Source: `content/insights-data.json` on metis-website `main` (commit
`e673f4d`, read 2026-11-06). Pillar names come from `pillars.py`. The file
holds one `featured` entry, an `essays` list and a `notes` list; the featured
entry is counted once.

| # | Pillar | Essays | Field notes | Case studies | Total |
|---|--------|-------:|------------:|-------------:|------:|
| 01 | Self-Mastery & Executive Psychology | 2 | 0 | 0 | 2 |
| 02 | Strategic Thinking & Decision Architecture | 0 | 0 | 0 | 0 |
| 03 | Communication, Influence & Relational Leadership | 0 | 0 | 0 | 0 |
| 04 | Team Dynamics & Culture Engineering | 0 | 0 | 0 | 0 |
| 05 | Organizational Systems & Change Psychology | 0 | 0 | 0 | 0 |
| | **All pillars** | **2** | **0** | **0** | **2** |

The two published pieces:

- *The Cognitive Cost of the Unflappable Leader* (essay, 2026-07-25)
- *The Psychology of the Partial Exit* (essay, 2026-08-02, featured)

`memory/content_history.json` in this repo lists the same two pieces.

What the count shows: the whole body of work sits in one pillar, and the
field-note format has not appeared on the site yet. A prospect who filters
the Insights page by any of four chips finds nothing.

## 2. How the calendar is weighted

- Cadence follows `CLAUDE.md`: one essay a quarter, one field note a month.
- The four empty pillars each get one essay. Self-Mastery, already at two
  essays, gets none.
- Field notes go three each to Strategy, Communication and Teams & Culture,
  two to Change, one to Self-Mastery. Change gets two because its essay
  already covers the largest change topic of the year.
- No pillar gets field notes in consecutive months, and no month carries an
  essay and a field note from the same pillar, so the Insights page grows
  evenly instead of in runs.
- Case studies are not scheduled. They depend on a real engagement and a
  consent decision, which the calendar cannot supply.

If the calendar runs as written, coverage at November 2027 is:

| Pillar | Now | + Essays | + Notes | Nov 2027 |
|--------|----:|---------:|--------:|---------:|
| Self-Mastery | 2 | 0 | 1 | 3 |
| Strategy | 0 | 1 | 3 | 4 |
| Communication | 0 | 1 | 3 | 4 |
| Teams & Culture | 0 | 1 | 3 | 4 |
| Change | 0 | 1 | 2 | 3 |
| **Total** | **2** | **4** | **12** | **18** |

## 3. Essays (one a quarter)

| Month | Pillar | Working title | The leader's situation it answers |
|-------|--------|---------------|-----------------------------------|
| Feb 2027 | Strategic Thinking & Decision Architecture | Decisions That Will Not Stay Made | A CEO whose executive team agrees in the room and reopens the same decision a week later, so commitments slip and the CEO ends up deciding everything alone. |
| May 2027 | Team Dynamics & Culture Engineering | The Inherited Team | An executive taking over a senior team still loyal to the predecessor, who must earn authority without purging people or pretending nothing changed. |
| Aug 2027 | Organizational Systems & Change Psychology | Change Fatigue Is a Sequencing Problem | A leader about to launch a third major initiative in two years, facing staff who comply on paper and wait for this one to pass. |
| Nov 2027 | Communication, Influence & Relational Leadership | How Bad News Travels Up | A CEO who keeps learning about problems late because each layer below softens what it reports. |

## 4. Field notes (one a month)

| Month | Pillar | Working title | The leader's situation it answers |
|-------|--------|---------------|-----------------------------------|
| Dec 2026 | Team Dynamics & Culture Engineering | The Offsite That Changed Nothing | A leader planning the January offsite whose last one produced good conversation and no change in how the team behaves. |
| Jan 2027 | Organizational Systems & Change Psychology | What a Second Reorg Teaches the Organization | A leader weighing another restructure within eighteen months of the last one. |
| Feb 2027 | Communication, Influence & Relational Leadership | The Hallway Version of the Decision | A leader whose announced decisions are reinterpreted in side conversations before they reach the front line. |
| Mar 2027 | Strategic Thinking & Decision Architecture | Choosing a Successor Is Choosing a Strategy | A board chair or CEO picking a successor when the next phase calls for a different leadership profile from the current one. |
| Apr 2027 | Team Dynamics & Culture Engineering | Two Executives Who Will Not Work Together | A CEO who keeps mediating between two direct reports and has started routing work around the conflict. |
| May 2027 | Self-Mastery & Executive Psychology | When the Founder Is the Bottleneck | A founder-CEO whose company has outgrown the habit of approving every decision personally. |
| Jun 2027 | Communication, Influence & Relational Leadership | The Feedback Senior Leaders Stop Receiving | An executive whose direct reports have stopped telling them what is not working, and who reads the quiet as agreement. |
| Jul 2027 | Strategic Thinking & Decision Architecture | The Pre-Mortem Nobody Runs | A leader about to commit to a large bet with a team that agreed to it too quickly. |
| Aug 2027 | Team Dynamics & Culture Engineering | Hiring for the Culture You Say You Have | A leader whose senior hires leave within a year because the culture they were sold differs from the one they joined. |
| Sep 2027 | Organizational Systems & Change Psychology | Middle Managers Carry the Change | A leader whose transformation is endorsed at the top and stalls one layer down. |
| Oct 2027 | Communication, Influence & Relational Leadership | A Board That Wants to Operate | A CEO whose directors reach into operating decisions, and who has to reset the line without damaging the relationship. |
| Nov 2027 | Strategic Thinking & Decision Architecture | The Annual Plan as a Negotiation | A leader whose planning cycle has turned into a contest over budgets, with the strategic choices made by default. |

## 5. Using this with the engine

- **Scout still supplies the news peg.** Each topic above is a standing
  situation, not a news story. When a month comes up, run Scout as usual and
  pair the topic with a current development that shows it; the style guide
  asks for a named person, date or decision, and the calendar does not
  supply one.
- **One overlap with the existing plan.** `memory/calendar.json` holds a
  field-note slot on a CEO succession (Strategy pillar) that has not been
  written. The March 2027 note covers the same situation; use that slot's
  source headline for it, or replace it with a fresher one.
- **Titles are working titles.** The writers return their own titles; these
  exist so John can tell topics apart when choosing.
- **Re-count before each quarter.** If John publishes off-calendar, or a case
  study goes live, re-run the count in section 1 and move the next pieces
  toward whichever pillar is now thinnest.
