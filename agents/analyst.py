# -*- coding: utf-8 -*-
"""
The Analyst agent: ingests reader-engagement data, computes performance per
pillar, compares it against a target read-through rate, and produces
recommendations the Strategist can use to adjust pillar weighting over time.
Pure logic, no Gemini calls.

Each entry in memory/engagement_data.json is one published piece's metrics:
{"pillar": str, "format": "essay"|"field_note", "views": int, "reads": int,
 "avg_seconds": int}
where a "read" is a view that scrolled/stayed long enough to count as read
(read-through). avg_seconds is recorded for the weekly report but does not
drive the adjustment.

DEFAULT_TARGET_RATE is a placeholder benchmark (40% read-through) until real
numbers exist.

TODO: nothing writes engagement_data.json yet -- the Insights page has no
analytics wired up. When it does (Vercel Analytics, Plausible, or similar),
feed views/reads/avg_seconds per pillar into memory/engagement_data.json and
replace DEFAULT_TARGET_RATE with a real target.

Run:  python -m agents.analyst
"""

import json
import os

from pillars import PILLAR_NAMES

MEMORY_DIR = "memory"
ENGAGEMENT_PATH = os.path.join(MEMORY_DIR, "engagement_data.json")

DEFAULT_TARGET_RATE = 0.40  # reads / views (read-through rate)


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_performance(engagement_data: list) -> dict:
    """Aggregate read-through by pillar. Returns
    {pillar: {"post_count": int, "rate": float}}, where rate is the
    views-weighted read-through rate across all of that pillar's pieces."""
    totals = {}
    for entry in engagement_data:
        pillar = entry.get("pillar")
        if not pillar:
            continue
        bucket = totals.setdefault(pillar, {"reads": 0, "views": 0, "post_count": 0})
        bucket["reads"] += entry.get("reads", 0)
        bucket["views"] += entry.get("views", 0)
        bucket["post_count"] += 1

    performance = {}
    for pillar, bucket in totals.items():
        rate = bucket["reads"] / bucket["views"] if bucket["views"] > 0 else 0.0
        performance[pillar] = {"post_count": bucket["post_count"], "rate": rate}
    return performance


def compare_to_target(performance: dict, target_rate: float = DEFAULT_TARGET_RATE) -> list:
    """Classify each pillar's rate against target_rate. Returns a list of
    {"pillar", "post_count", "rate", "target", "status"} where status is
    "above", "below", or "at" (within 10% of target either way)."""
    comparison = []
    for pillar, stats in performance.items():
        rate = stats["rate"]
        if rate >= target_rate * 1.1:
            status = "above"
        elif rate <= target_rate * 0.9:
            status = "below"
        else:
            status = "at"
        comparison.append({
            "pillar": pillar,
            "post_count": stats["post_count"],
            "rate": rate,
            "target": target_rate,
            "status": status,
        })
    return comparison


def pillar_adjustments(comparison: list) -> dict:
    """Turn a comparison list into {pillar: +1/-1/0} for the Strategist:
    +1 means do more of this pillar (it overperforms), -1 means do less."""
    adjustments = {}
    for row in comparison:
        if row["status"] == "above":
            adjustments[row["pillar"]] = 1
        elif row["status"] == "below":
            adjustments[row["pillar"]] = -1
        else:
            adjustments[row["pillar"]] = 0
    return adjustments


def get_pillar_adjustments(engagement_data: list = None, target_rate: float = DEFAULT_TARGET_RATE) -> dict:
    """Convenience entry point for the Orchestrator: load engagement data
    (or use what was passed in), compute performance, and return adjustments.
    Pillars with no data yet are simply absent (adjustment 0 by default)."""
    if engagement_data is None:
        engagement_data = _load_json(ENGAGEMENT_PATH, [])
    performance = compute_performance(engagement_data)
    comparison = compare_to_target(performance, target_rate=target_rate)
    return pillar_adjustments(comparison)


def weekly_summary(engagement_data: list = None, target_rate: float = DEFAULT_TARGET_RATE) -> str:
    """Human-readable performance report, one line per pillar with data."""
    if engagement_data is None:
        engagement_data = _load_json(ENGAGEMENT_PATH, [])
    performance = compute_performance(engagement_data)
    comparison = compare_to_target(performance, target_rate=target_rate)

    if not comparison:
        return ("[ANALYST] No engagement data yet. Nothing to report. (Wire the "
                "Insights page up to analytics and feed memory/engagement_data.json.)")

    comparison.sort(key=lambda row: row["rate"], reverse=True)
    lines = [f"[ANALYST] Performance summary (target read-through: {target_rate:.0%}):"]
    for row in comparison:
        lines.append(
            f"  {row['pillar']}: {row['rate']:.0%} read-through over "
            f"{row['post_count']} piece(s) - {row['status']} target"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    data = _load_json(ENGAGEMENT_PATH, [])
    if not data:
        print("[ANALYST] memory/engagement_data.json is empty; using mock data for this run.\n")
        data = [
            {"pillar": "Self-Mastery & Executive Psychology", "format": "essay",
             "views": 2000, "reads": 1100, "avg_seconds": 240},
            {"pillar": "Strategic Thinking & Decision Architecture", "format": "essay",
             "views": 1800, "reads": 540, "avg_seconds": 90},
            {"pillar": "Team Dynamics & Culture Engineering", "format": "field_note",
             "views": 1500, "reads": 900, "avg_seconds": 120},
            {"pillar": "Organizational Systems & Change Psychology", "format": "field_note",
             "views": 1200, "reads": 360, "avg_seconds": 60},
        ]

    print(weekly_summary(data))
    print()
    print("[ANALYST] Pillar adjustments for the Strategist:")
    print(json.dumps(get_pillar_adjustments(data), indent=2))
