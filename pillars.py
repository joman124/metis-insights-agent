# -*- coding: utf-8 -*-
"""
The five Metis Pillars: the single source of truth for the content taxonomy,
mirroring window.METIS.PILLARS in the metis-website repo (site/data.js). Every
agent that needs the pillar list imports it from here instead of redefining
it, so the taxonomy stays consistent across Scout, Strategist, Analyst, the
publisher, and the Streamlit UI -- and matches the filter chips on the live
Insights page.

Each pillar carries:
  key   -- short slug used as the data-topic / data-filter value on the site
           (drives the Insights page filter chips and the loader)
  n     -- the "01".."05" ordinal shown on the site
  name  -- the canonical pillar name (matches site/data.js exactly)
  chip  -- the short label shown on a filter chip
"""

PILLARS = [
    {
        "key": "self-mastery",
        "n": "01",
        "name": "Self-Mastery & Executive Psychology",
        "chip": "Self-Mastery",
    },
    {
        "key": "strategy",
        "n": "02",
        "name": "Strategic Thinking & Decision Architecture",
        "chip": "Strategy",
    },
    {
        "key": "communication",
        "n": "03",
        "name": "Communication, Influence & Relational Leadership",
        "chip": "Communication",
    },
    {
        "key": "teams",
        "n": "04",
        "name": "Team Dynamics & Culture Engineering",
        "chip": "Teams & Culture",
    },
    {
        "key": "change",
        "n": "05",
        "name": "Organizational Systems & Change Psychology",
        "chip": "Change",
    },
]

# Convenience views the agents actually use.
PILLAR_NAMES = [p["name"] for p in PILLARS]
PILLAR_KEYS = [p["key"] for p in PILLARS]

_BY_NAME = {p["name"]: p for p in PILLARS}
_BY_KEY = {p["key"]: p for p in PILLARS}


def key_for(name: str) -> str:
    """Return the site data-topic slug for a pillar name, or 'self-mastery'
    as a safe default if the name is unrecognized."""
    p = _BY_NAME.get(name)
    return p["key"] if p else PILLARS[0]["key"]


def name_for(key: str) -> str:
    """Return the canonical pillar name for a site slug, or the first pillar
    as a safe default."""
    p = _BY_KEY.get(key)
    return p["name"] if p else PILLARS[0]["name"]


def is_pillar(name: str) -> bool:
    return name in _BY_NAME
