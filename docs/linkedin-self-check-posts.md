# LinkedIn drafts: field notes to the Leadership self-check (t280)

Status: **DRAFT, UNPOSTED.** Nothing here has been posted or queued. The voice judge was not run on any post, so the voice check is yours.

One post per field note published on metisag.com (content/insights-data.json on metis-website main, after PR #18). Each opens on the note's finding and ends on the self-check link, https://www.metisag.com/self-check, with no call booking. The self-check now ends in a pillar reading, a next read and the call button, so the call is still one click away. Each post's body carries only claims from its note. The closing paragraph is the same in all four and describes the self-check as the page itself does.

Self-Mastery has no published field note, so it has no post here. Its two pieces on the site are essays (The Psychology of the Partial Exit, The Cognitive Cost of the Unflappable Leader). That makes four posts covering four pillars, not five.

How to post one: copy the text block as it stands into LinkedIn by hand, then mark it posted in the Studio the usual way.

| # | Post | Pillar | Words (no URL) | Guardrails | Voice judge | Decision |
|---|---|---|---|---|---|---|
| 1 | The offsite that changed nothing | Team Dynamics & Culture Engineering | 128 | clean | not run | [ ] post [ ] edit [ ] drop |
| 2 | Choosing a successor is choosing a strategy | Strategic Thinking & Decision Architecture | 138 | clean | not run | [ ] post [ ] edit [ ] drop |
| 3 | The hallway version of the decision | Communication, Influence & Relational Leadership | 142 | clean | not run | [ ] post [ ] edit [ ] drop |
| 4 | What a second reorg teaches the organization | Organizational Systems & Change Psychology | 130 | clean | not run | [ ] post [ ] edit [ ] drop |

What "clean" means: `guardrails.run_guardrails` (root, field-note rules) and `viral-agents/guardrails.run_guardrails` (LinkedIn rules, max 1 em dash) were run on each full post on 2026-11-24. Every post has 0 banned phrases, 0 antithesis reversals, 0 negative parallelisms, 0 flagged fragment triads, 0 em dashes and no curly quotes. Every post is inside the 50 to 150 word range in `PLATFORM_RULES["linkedin_viral"]`.

Two places these drafts break `PLATFORM_RULES["linkedin_viral"]` on purpose, because the task asked for them:

- **A link in the body.** The rule is `allow_links_in_body: False`, and the task needs the self-check link. If you'd rather keep the link out of the body, post without the URL line and put it in the first comment.
- **No hashtags.** The rule asks for 3 to 5. Hashtags after the link would stop the post ending on it, and the sector writes for leaders, not algorithms. Add them if you want them.

---

## 1. The offsite that changed nothing

**Pillar:** Team Dynamics & Culture Engineering · **Source note:** https://www.metisag.com/insights/the-offsite-that-changed-nothing · **Guardrails:** clean · **Voice judge:** not run

```text
Most leadership offsites end well. Six weeks later the weekly meeting runs exactly as it did before.

Behavior learned in one setting stays tied to the cues of that setting. An offsite removes the agenda, the seating, the inbox and the quarterly number. When the team returns, those triggers return, and the old behavior with them.

So the work of an offsite is in the translation back. Before the team leaves, each commitment gets written as a specific behavior in a specific recurring meeting, owned by a named executive, with a date to review it.

The leadership self-check is ten statements, two for each of the five areas we work in. It ends by showing which area to look at first, and your answers stay in your browser.

https://www.metisag.com/self-check
```

---

## 2. Choosing a successor is choosing a strategy

**Pillar:** Strategic Thinking & Decision Architecture · **Source note:** https://www.metisag.com/insights/choosing-a-successor-is-choosing-a-strategy · **Guardrails:** clean · **Voice judge:** not run

```text
A board that picks a successor before it agrees on what the next phase of the business requires ends up choosing on familiarity. Familiarity favors the candidate who most resembles the current CEO.

Protecting a position and changing it call for different leaders. A board that has not said which one it is asking for will default to protection, because protection is what the outgoing CEO models every day.

We ask boards to write the strategic brief before the candidate profile. One page: what the company must stop doing, what it must start, and which current strengths the next CEO is expected to wind down.

The leadership self-check is ten statements, two for each of the five areas we work in. It ends by showing which area to look at first, and your answers stay in your browser.

https://www.metisag.com/self-check
```

---

## 3. The hallway version of the decision

**Pillar:** Communication, Influence & Relational Leadership · **Source note:** https://www.metisag.com/insights/the-hallway-version-of-the-decision · **Guardrails:** clean · **Voice judge:** not run

```text
Every announced decision has a second version, and it is the one most of the organization acts on. It forms in the hour after the meeting, when the people who were in the room explain it to their own teams.

An executive who lost the argument in the room rarely repeats the reasons that beat them. A memo or an all-hands settles the facts and does little for the meaning.

What works better happens before the announcement. Ask each executive who will relay the decision to say, in the room, how they will explain it to their team. You hear the hallway version while you can still correct it.

The leadership self-check is ten statements, two for each of the five areas we work in. It ends by showing which area to look at first, and your answers stay in your browser.

https://www.metisag.com/self-check
```

---

## 4. What a second reorg teaches the organization

**Pillar:** Organizational Systems & Change Psychology · **Source note:** https://www.metisag.com/insights/what-a-second-reorg-teaches-the-organization · **Guardrails:** clean · **Voice judge:** not run

```text
A second reorg that arrives within eighteen months of the first teaches the organization a rule about time: structures here are provisional, so investing in them is a bad bet.

People keep the old informal routes alive, commit lightly to the new reporting lines, and wait. Leaders read this as resistance. It is accurate learning from what the organization has seen.

When the first change was never finished, the stronger move is often to finish it. Name what it was meant to fix, give each gap an owner, and allow it the twelve months it never had.

The leadership self-check is ten statements, two for each of the five areas we work in. It ends by showing which area to look at first, and your answers stay in your browser.

https://www.metisag.com/self-check
```
