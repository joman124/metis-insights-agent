# -*- coding: utf-8 -*-
"""
Publishing surface for approved drafts. Replaces the old LinkedIn/Substack
publish_log: instead of just recording that a post went out, promote_to_site()
turns an approved draft into real site content --

  1. builds a structured entry and appends it to the site's
     content/insights-data.json (which the Insights page renders via
     site/insights-loader.js),
  2. generates a standalone article page at insights/<slug>.html
     (site_builder.render_article), and
  3. records the publish event in this repo's memory/content_history.json,
     so the Strategist's pillar balance and the Analyst see what went out.

It writes into a local checkout of the metis-website repo when it can find one
(METIS_SITE_DIR in .env, or ../metis-website next to this repo); otherwise it
writes into ./site_output/ so nothing is lost. Either way, committing and
pushing those files to metis-website stays a deliberate, manual step -- this
tool never touches git.

CLI:
    python content_publisher.py            # list what's in the site data file
"""

import json
import os
from datetime import date

import site_builder
from pillars import key_for, PILLAR_NAMES

MEMORY_DIR = "memory"
CONTENT_HISTORY_PATH = os.path.join(MEMORY_DIR, "content_history.json")
DRAFTS_DOC = "Insights Drafts.docx"

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_RELPATH = os.path.join("content", "insights-data.json")
ARTICLE_DIR = "insights"

_EMPTY_DATA = {"featured": None, "essays": [], "notes": []}


# --------------------------------------------------------------------------
# Where the site content lives
# --------------------------------------------------------------------------
def resolve_site_dir() -> dict:
    """Find the directory to write site content into. Returns
    {"path": str, "is_site": bool}: is_site True means a real metis-website
    checkout was found; False means we fell back to ./site_output/."""
    candidates = []
    env_dir = os.getenv("METIS_SITE_DIR")
    if env_dir:
        candidates.append(env_dir if os.path.isabs(env_dir)
                          else os.path.join(_REPO_ROOT, env_dir))
    candidates.append(os.path.join(os.path.dirname(_REPO_ROOT), "metis-website"))

    for path in candidates:
        if path and os.path.isdir(path) and os.path.exists(
                os.path.join(path, "insights.html")):
            return {"path": os.path.abspath(path), "is_site": True}

    fallback = os.path.join(_REPO_ROOT, "site_output")
    return {"path": fallback, "is_site": False}


def _data_path(site_dir: str) -> str:
    return os.path.join(site_dir, DATA_RELPATH)


def load_data(site_dir: str) -> dict:
    """Load content/insights-data.json from a site dir, or a fresh empty
    structure if it does not exist yet."""
    path = _data_path(site_dir)
    if not os.path.exists(path):
        return json.loads(json.dumps(_EMPTY_DATA))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(_EMPTY_DATA))
    for key, default in _EMPTY_DATA.items():
        data.setdefault(key, default)
    return data


def save_data(site_dir: str, data: dict) -> str:
    path = _data_path(site_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


# --------------------------------------------------------------------------
# History write-back (feeds Strategist / Analyst)
# --------------------------------------------------------------------------
def _load_history() -> list:
    if not os.path.exists(CONTENT_HISTORY_PATH):
        return []
    try:
        with open(CONTENT_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def record_publish(title: str, pillar: str, fmt: str, href: str,
                   published_date: str) -> dict:
    """Append one publish event to memory/content_history.json (idempotent on
    title). Schema matches what the Strategist reads: date + pillar + format."""
    history = _load_history()
    for entry in history:
        if entry.get("title") == title:
            return entry
    entry = {"title": title, "date": published_date, "pillar": pillar,
             "format": fmt, "href": href, "status": "published"}
    history.append(entry)
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(CONTENT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    return entry


# --------------------------------------------------------------------------
# Promote a draft into site content
# --------------------------------------------------------------------------
def _unique_slug(base: str, data: dict, site_dir: str) -> str:
    existing = set()
    for e in ([data.get("featured")] + data.get("essays", []) + data.get("notes", [])):
        if e and e.get("slug"):
            existing.add(e["slug"])
    slug = base
    i = 2
    while slug in existing or os.path.exists(
            os.path.join(site_dir, ARTICLE_DIR, slug + ".html")):
        slug = f"{base}-{i}"
        i += 1
    return slug


def promote_to_site(body: str, fmt: str, pillar: str, title: str = None,
                    dek: str = None, featured: bool = None,
                    status: str = "Published", published_date: str = None,
                    site_dir: str = None) -> dict:
    """Promote one approved draft into site content. body is the draft text,
    fmt is 'essay' or 'field_note', pillar is a full Metis pillar name.

    title/dek are derived from the body via the writer agents when not given
    (one cheap Gemini call). featured defaults to True for essays (newest
    essay becomes the featured slot) and is ignored for field notes.

    Returns a dict describing what was written (entry, data_path,
    article_path, site_dir, is_site, history_entry)."""
    if fmt not in ("essay", "field_note"):
        raise ValueError("fmt must be 'essay' or 'field_note', got %r" % fmt)
    if pillar not in PILLAR_NAMES:
        raise ValueError("Unknown pillar %r. Expected one of: %s"
                         % (pillar, ", ".join(PILLAR_NAMES)))

    # Derive metadata lazily (keeps this module importable without an API key
    # unless a caller actually omits the title).
    if title is None or (fmt == "essay" and dek is None):
        if fmt == "essay":
            from agents.essay_writer import propose_metadata
            meta = propose_metadata(body, pillar)
            title = title or meta["title"]
            dek = dek if dek is not None else meta["dek"]
        else:
            from agents.field_note_writer import propose_title
            title = title or propose_title(body, pillar)

    published_date = published_date or date.today().isoformat()
    resolved = resolve_site_dir() if site_dir is None else {"path": site_dir, "is_site": True}
    site_dir = resolved["path"]

    data = load_data(site_dir)
    slug = _unique_slug(site_builder.slugify(title), data, site_dir)
    href = f"{ARTICLE_DIR}/{slug}.html"

    entry = {
        "id": slug,
        "slug": slug,
        "title": title,
        "dek": dek or "",
        "pillar": pillar,
        "topic": key_for(pillar),      # short slug -> site filter chips
        "format": fmt,
        "status": status,
        "read_time": site_builder.read_time(body, fmt),
        "published_date": published_date,
        "href": href,
        "body_html": site_builder.paragraphs_html(body),
        "byline_name": site_builder.BYLINE_NAME,
        "byline_role": site_builder.BYLINE_ROLE,
    }
    if fmt == "field_note":
        entry["date"] = site_builder.quarter_label(published_date)

    # Slot it into the data structure.
    if fmt == "essay":
        make_featured = True if featured is None else featured
        if make_featured:
            if data.get("featured"):
                data["essays"].insert(0, data["featured"])
            data["featured"] = entry
        else:
            data["essays"].insert(0, entry)
    else:
        data["notes"].insert(0, entry)

    data_path = save_data(site_dir, data)

    # Generate the standalone article page.
    article_path = os.path.join(site_dir, ARTICLE_DIR, slug + ".html")
    os.makedirs(os.path.dirname(article_path), exist_ok=True)
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(site_builder.render_article(entry))

    history_entry = record_publish(title, pillar, fmt, href, published_date)

    return {
        "entry": entry,
        "data_path": data_path,
        "article_path": article_path,
        "site_dir": site_dir,
        "is_site": resolved["is_site"],
        "history_entry": history_entry,
    }


if __name__ == "__main__":
    resolved = resolve_site_dir()
    print("Site dir: %s (%s)" % (
        resolved["path"],
        "metis-website checkout" if resolved["is_site"] else "local fallback"))
    data = load_data(resolved["path"])
    feat = data.get("featured")
    print("Featured: " + (feat["title"] if feat else "(none)"))
    print("Essays: %d" % len(data.get("essays", [])))
    print("Field notes: %d" % len(data.get("notes", [])))
