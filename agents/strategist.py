# -*- coding: utf-8 -*-
"""
The Strategist agent: plans what to publish this cycle and under which pillar.
Reads persistent state from memory/ (content history + rolling pillar
distribution), balances pillar coverage, applies Metis's deliberately slow
cadence, and writes the plan to memory/calendar.json. Pure logic, no Gemini
calls.

Cadence (the editorial call John can tune -- these are the knobs):
  FIELD_NOTES_PER_CYCLE     one short field note per monthly cycle
  ESSAY_INTERVAL_DAYS       one long-form essay per quarter (published only if
                            none has gone out in the trailing 90 days)
  CASE_STUDY_INTERVAL_DAYS  one case study per quarter, same logic as essays.
                            Case studies are as substantial as an essay, so
                            they default to the same cadence; tune separately
                            if that turns out wrong in practice.
This mirrors the site's own promise: "Three or four essays a year" plus a
denser cadence of short observations. Change the constants below to publish
more or less often.

Run:  python -m agents.strategist
"""

import json
import os
from datetime import date, timedelta

from pillars import PILLAR_NAMES

MEMORY_DIR = "memory"
CONTENT_HISTORY_PATH = os.path.join(MEMORY_DIR, "content_history.json")
PILLAR_TRACKER_PATH = os.path.join(MEMORY_DIR, "pillar_tracker.json")
CALENDAR_PATH = os.path.join(MEMORY_DIR, "calendar.json")

# --- Cadence knobs (editorial, tune freely) --------------------------------
FIELD_NOTES_PER_CYCLE = 1        # short observations per monthly cycle
ESSAY_INTERVAL_DAYS = 90         # publish an essay only if none in this trailing window
CASE_STUDY_INTERVAL_DAYS = 90    # publish a case study only if none in this trailing window
# Balance pillar coverage over a long window, since Metis publishes slowly and
# a 30-day window would almost always read as empty.
PILLAR_WINDOW_DAYS = 365


def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data) -> None:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def compute_pillar_distribution(history: list, window_days: int = PILLAR_WINDOW_DAYS) -> dict:
    """Count published pieces per pillar within the rolling window. Pillars
    with no pieces in the window stay at zero, so they rank first for
    balancing."""
    counts = {p: 0 for p in PILLAR_NAMES}
    cutoff = date.today() - timedelta(days=window_days)
    for entry in history:
        try:
            entry_date = date.fromisoformat(entry["date"])
        except (KeyError, ValueError):
            continue
        if entry_date < cutoff:
            continue
        pillar = entry.get("pillar")
        if pillar in counts:
            counts[pillar] += 1
    return counts


def _format_due(history: list, fmt: str, interval_days: int) -> bool:
    """True if no piece of the given format has been published within the
    trailing interval -- i.e. one is due. A fresh/empty history means one is
    due. Shared by essays and case studies, the two interval-gated formats
    (field notes are just a flat per-cycle count instead)."""
    cutoff = date.today() - timedelta(days=interval_days)
    for entry in history:
        if entry.get("format") != fmt:
            continue
        try:
            entry_date = date.fromisoformat(entry["date"])
        except (KeyError, ValueError):
            continue
        if entry_date >= cutoff:
            return False
    return True


def _rank_pillars(distribution: dict, adjustments: dict) -> list:
    """Least-used pillars first. adjustments (+1/-1/0 per pillar, from the
    Analyst) nudge a pillar earlier (+1, it overperforms, do more) or later
    (-1) without overriding the rolling-window balance entirely."""
    return sorted(
        PILLAR_NAMES,
        key=lambda p: (distribution[p] - adjustments.get(p, 0), PILLAR_NAMES.index(p)),
    )


def _match_scout_topic(pillar: str, fmt: str, used_headlines: set, scout_briefing: list):
    """Prefer a Scout topic matching both pillar and format; fall back to one
    matching just the pillar; return None if nothing fits."""
    for want_format in (fmt, None):
        for topic in scout_briefing or []:
            if topic.get("headline") in used_headlines:
                continue
            if topic.get("suggested_pillar") != pillar:
                continue
            if want_format is not None and topic.get("suggested_format") != want_format:
                continue
            return topic
    return None


def _match_case_study_subject(pillar: str, used_headlines: set, scout_briefing: list):
    """Case studies need a named subject, so this does NOT fall back to a
    pillar-only match the way _match_scout_topic does for essay/field_note --
    a case study slot with no subject is useless downstream. Prefer the
    ranked pillar; fall back to any pillar rather than skip the slot, since a
    good subject anywhere beats none."""
    for want_pillar in (pillar, None):
        for topic in scout_briefing or []:
            if topic.get("headline") in used_headlines:
                continue
            if topic.get("suggested_format") != "case_study":
                continue
            if not topic.get("suggested_subject"):
                continue
            if want_pillar is not None and topic.get("suggested_pillar") != want_pillar:
                continue
            return topic
    return None


def plan_cycle(scout_briefing: list = None, pillar_adjustments: dict = None) -> list:
    """Build one cycle's plan. Always plans FIELD_NOTES_PER_CYCLE field notes;
    adds one essay if a quarterly essay is due. Each item's pillar is the next
    least-used pillar (so coverage rotates), matched to a Scout topic when one
    is available. Writes and returns the plan."""
    history = _load_json(CONTENT_HISTORY_PATH, [])
    distribution = compute_pillar_distribution(history)
    _save_json(PILLAR_TRACKER_PATH, distribution)

    adjustments = pillar_adjustments or {}
    ranked = _rank_pillars(distribution, adjustments)

    # Decide the slots for this cycle: essay and case study first (if due),
    # then field notes.
    slots = []
    if _format_due(history, "essay", ESSAY_INTERVAL_DAYS):
        slots.append("essay")
    if _format_due(history, "case_study", CASE_STUDY_INTERVAL_DAYS):
        slots.append("case_study")
    slots.extend(["field_note"] * FIELD_NOTES_PER_CYCLE)

    used_headlines = set()
    plan = []
    labels = {"essay": "Essay", "case_study": "Case study", "field_note": "Field note"}
    for i, fmt in enumerate(slots):
        pillar = ranked[i % len(ranked)]
        if fmt == "case_study":
            match = _match_case_study_subject(pillar, used_headlines, scout_briefing)
        else:
            match = _match_scout_topic(pillar, fmt, used_headlines, scout_briefing)
        if match:
            used_headlines.add(match["headline"])
            # Trust Scout's pillar tag when we matched on it.
            pillar = match.get("suggested_pillar", pillar)

        bank_pick = None
        if fmt == "case_study" and not match:
            # Scout found nothing usable this cycle -- fall back to the
            # curated subject bank instead of leaving the slot empty.
            from case_study_subjects import pick_subject
            bank_pick = pick_subject(pillar, history)
            if bank_pick:
                pillar = bank_pick["pillar"]

        item = {
            "slot": f"{labels[fmt]} {sum(1 for p in plan if p['format'] == fmt) + 1}",
            "format": fmt,
            "pillar": pillar,
            "topic": (match["suggested_angle"] if match
                     else bank_pick["angle"] if bank_pick else None),
            "source_headline": (match["headline"] if match
                                else "Metis case-study idea bank (%s)" % bank_pick["category"]
                                if bank_pick else None),
        }
        if fmt == "case_study":
            item["subject"] = ((match.get("suggested_subject") or None) if match
                               else bank_pick["subject"] if bank_pick else None)
            item["research_notes"] = bank_pick["research_notes"] if bank_pick else None
        plan.append(item)

    _save_json(CALENDAR_PATH, plan)
    return plan


if __name__ == "__main__":
    cycle_plan = plan_cycle()
    print(json.dumps(cycle_plan, indent=2))
