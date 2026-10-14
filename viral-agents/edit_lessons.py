# -*- coding: utf-8 -*-
"""
Learn from John's edits.

When John edits a queued draft before approving it, the gap between what the
agent wrote and what John shipped is the most honest feedback the system gets.
This module records those before/after pairs and, at the next draft run,
distills them into short standing corrections that are injected into every
writer prompt -- so the writers stop making the mistakes John keeps fixing.

Two files in memory/:
  edit_history.json  -- raw {original, edited} pairs, appended at save time.
                        No API call happens here, so saving an edit stays
                        instant.
  edit_lessons.json  -- distilled standing corrections with counts, updated
                        lazily by distill_pending() right before the next
                        draft (where the caller is already paying for model
                        calls).

Design rules:
  - Never raise. A failure to record or distill must never block a save, an
    approval, or a draft. Every public function swallows its own errors.
  - No API call at save time; distillation is deferred to draft time.
  - Lessons are style/structure rules, not topic content. The distiller is
    told to ignore purely topical edits.
"""

import json
import os
from datetime import datetime, timezone

HISTORY_PATH = os.path.join("memory", "edit_history.json")
LESSONS_PATH = os.path.join("memory", "edit_lessons.json")
MAX_HISTORY = 200      # raw pairs kept on disk
MAX_LESSONS = 12       # standing corrections injected into prompts
MAX_PAIR_CHARS = 1500  # per-text cap when sending pairs to the model
MAX_PAIRS_PER_DISTILL = 6


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path, data):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_edit(original, edited, context=""):
    """Record one before/after editing pair. Cheap and instant: appends to
    edit_history.json and returns. Distillation into lessons happens later,
    at draft time. Never raises."""
    try:
        original = (original or "").strip()
        edited = (edited or "").strip()
        if not original or not edited or original == edited:
            return {"recorded": False}
        history = _load_json(HISTORY_PATH, [])
        history.append({
            "timestamp": _now(),
            "context": str(context or "")[:200],
            "original": original[:MAX_PAIR_CHARS * 4],
            "edited": edited[:MAX_PAIR_CHARS * 4],
            "distilled": False,
        })
        _save_json(HISTORY_PATH, history[-MAX_HISTORY:])
        return {"recorded": True}
    except Exception:
        return {"recorded": False}


def _merge_lessons(new_lessons):
    """Fold freshly distilled rules into edit_lessons.json: bump the count on
    a repeat, append a new one, keep the list capped at MAX_LESSONS sorted by
    how often the correction has come up."""
    data = _load_json(LESSONS_PATH, [])
    for lesson in new_lessons:
        lesson = " ".join(str(lesson).split()).strip()
        if not lesson or len(lesson) > 200:
            continue
        for row in data:
            if row["lesson"].lower() == lesson.lower():
                row["count"] = row.get("count", 1) + 1
                row["last_seen"] = _now()
                break
        else:
            data.append({"lesson": lesson, "count": 1,
                         "first_seen": _now(), "last_seen": _now()})
    data.sort(key=lambda r: (r.get("count", 1), r.get("last_seen", "")),
              reverse=True)
    _save_json(LESSONS_PATH, data[:MAX_LESSONS])


def distill_pending():
    """Turn undistilled history pairs into standing corrections with one
    Flash call. Called lazily from lessons_prompt() at draft time. Returns
    the number of new lessons merged. Never raises."""
    try:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return 0
        history = _load_json(HISTORY_PATH, [])
        pending = [h for h in history if not h.get("distilled")]
        if not pending:
            return 0
        batch = pending[-MAX_PAIRS_PER_DISTILL:]

        blocks = []
        for i, h in enumerate(batch, 1):
            blocks.append(
                "PAIR %d (%s)\nAGENT DRAFT:\n%s\n\nEDITOR'S FINAL VERSION:\n%s"
                % (i, h.get("context") or "post",
                   h["original"][:MAX_PAIR_CHARS],
                   h["edited"][:MAX_PAIR_CHARS]))
        prompt = (
            "You improve a writing system by studying its editor's corrections.\n"
            "Below are before/after pairs: what the agent drafted vs what the\n"
            "editor actually shipped.\n\n"
            + "\n\n".join(blocks) +
            "\n\nDerive the smallest set of standing corrections (0 to 3) that\n"
            "future drafts should follow so the editor stops having to make\n"
            "the same fixes.\n\n"
            "Rules for each correction:\n"
            "- Generalizable writing guidance (style, structure, tone, length),\n"
            "  never topic-specific content\n"
            "- Imperative and specific, under 20 words\n"
            "- Only include it if the pairs clearly support it\n\n"
            "Return ONLY a JSON array of strings. Return [] if the edits are\n"
            "purely topical. No markdown fences, no preamble.")

        from anthropic_client import generate
        model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
        raw = generate(model, prompt, temperature=0.2).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        lessons = json.loads(raw)
        if not isinstance(lessons, list):
            lessons = []
        lessons = [l for l in lessons if isinstance(l, str) and l.strip()]

        if lessons:
            _merge_lessons(lessons)
        # Mark the batch distilled even when it produced no lessons, so purely
        # topical edits are not re-sent to the model forever. (batch entries
        # are references into history, so this mutates the right rows.)
        for h in batch:
            h["distilled"] = True
        _save_json(HISTORY_PATH, history)
        return len(lessons)
    except Exception:
        return 0


def lessons():
    """The current standing corrections, most-repeated first. Never raises."""
    try:
        return [r["lesson"] for r in _load_json(LESSONS_PATH, [])]
    except Exception:
        return []


def lessons_prompt():
    """The prompt block writers inject. Distills any pending edits first
    (one Flash call, at most), then returns the standing corrections as an
    instruction block -- or an empty string when there is nothing learned
    yet. Never raises."""
    try:
        distill_pending()
        current = lessons()
        if not current:
            return ""
        return (
            "\nThe editor has corrected past drafts. Standing corrections "
            "to honor:\n"
            + "\n".join("- " + l for l in current) + "\n")
    except Exception:
        return ""
