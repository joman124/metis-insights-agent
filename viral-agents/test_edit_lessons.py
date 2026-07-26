# -*- coding: utf-8 -*-
"""
Unit tests for the edit-learning loop (edit_lessons.py).

Covers the behavior the dashboard depends on, with no API calls: recording
before/after pairs, ignoring no-op edits, merging repeated lessons with counts,
capping the injected list, and building the prompt block. Distillation itself is
tested with a stubbed model call so the test stays free and offline.

Run:  python test_edit_lessons.py
"""

import json
import os
import tempfile

import edit_lessons


def _isolate():
    """Point the module at a fresh temp dir so tests never touch real data."""
    tmp = tempfile.mkdtemp()
    edit_lessons.HISTORY_PATH = os.path.join(tmp, "edit_history.json")
    edit_lessons.LESSONS_PATH = os.path.join(tmp, "edit_lessons.json")
    return tmp


def test_records_real_edit():
    _isolate()
    res = edit_lessons.record_edit("The agent wrote this.",
                                   "John shipped this instead.",
                                   context="linkedin post about AI pilots")
    assert res["recorded"] is True
    rows = json.load(open(edit_lessons.HISTORY_PATH, encoding="utf-8"))
    assert len(rows) == 1
    assert rows[0]["original"] == "The agent wrote this."
    assert rows[0]["edited"] == "John shipped this instead."
    assert rows[0]["distilled"] is False
    assert "AI pilots" in rows[0]["context"]
    print("[PASS] records a real edit")


def test_ignores_noop_and_empty_edits():
    _isolate()
    same = "Identical text."
    assert edit_lessons.record_edit(same, same)["recorded"] is False
    assert edit_lessons.record_edit(same, "  " + same + "  ")["recorded"] is False
    assert edit_lessons.record_edit("", "something")["recorded"] is False
    assert edit_lessons.record_edit("something", "")["recorded"] is False
    assert not os.path.exists(edit_lessons.HISTORY_PATH)
    print("[PASS] ignores no-op and empty edits")


def test_merge_counts_repeats_and_caps():
    _isolate()
    edit_lessons._merge_lessons(["Cut the closing question.",
                                 "Lead with the number."])
    edit_lessons._merge_lessons(["cut the closing question."])  # case-insensitive
    rows = json.load(open(edit_lessons.LESSONS_PATH, encoding="utf-8"))
    by_text = {r["lesson"]: r["count"] for r in rows}
    assert by_text["Cut the closing question."] == 2, by_text
    assert by_text["Lead with the number."] == 1, by_text
    # Most-repeated first, so the strongest signal leads the prompt.
    assert rows[0]["lesson"] == "Cut the closing question."

    # Overlong and empty rules are dropped; the stored list stays capped.
    edit_lessons._merge_lessons(["x" * 201, "   "])
    rows = json.load(open(edit_lessons.LESSONS_PATH, encoding="utf-8"))
    assert len(rows) == 2, rows
    edit_lessons._merge_lessons(["rule %d" % i for i in range(30)])
    rows = json.load(open(edit_lessons.LESSONS_PATH, encoding="utf-8"))
    assert len(rows) == edit_lessons.MAX_LESSONS, len(rows)
    print("[PASS] merges repeats with counts, drops junk, caps the list")


def test_lessons_prompt_shape():
    _isolate()
    # No lessons and no API key: an empty block, so prompts are unchanged.
    key = os.environ.pop("GEMINI_API_KEY", None)
    try:
        assert edit_lessons.lessons_prompt() == ""
        edit_lessons._merge_lessons(["Cut the closing question."])
        block = edit_lessons.lessons_prompt()
        assert "Standing corrections" in block
        assert "- Cut the closing question." in block
    finally:
        if key is not None:
            os.environ["GEMINI_API_KEY"] = key
    print("[PASS] prompt block is empty when unlearned, listed when learned")


def test_distill_marks_batch_and_merges(monkeypatch_generate=None):
    _isolate()
    os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "test-key")
    edit_lessons.record_edit("Draft with a closing question?",
                             "Draft with a closing statement.")

    # Stub the model call: distillation must not hit the network in tests.
    import gemini_client
    real_generate = gemini_client.generate
    gemini_client.generate = lambda *a, **k: '["Cut the closing question."]'
    try:
        made = edit_lessons.distill_pending()
    finally:
        gemini_client.generate = real_generate

    assert made == 1, made
    assert edit_lessons.lessons() == ["Cut the closing question."]
    rows = json.load(open(edit_lessons.HISTORY_PATH, encoding="utf-8"))
    assert rows[0]["distilled"] is True, "batch must be marked so it is not re-sent"
    # Nothing pending now, so a second pass is a no-op (and costs nothing).
    assert edit_lessons.distill_pending() == 0
    print("[PASS] distill merges lessons and marks the batch done")


def test_distill_survives_bad_model_output():
    _isolate()
    os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "test-key")
    edit_lessons.record_edit("before text", "after text")
    import gemini_client
    real_generate = gemini_client.generate
    gemini_client.generate = lambda *a, **k: "not json at all"
    try:
        # Must not raise: a bad distill can never break drafting.
        assert edit_lessons.distill_pending() == 0
    finally:
        gemini_client.generate = real_generate
    assert edit_lessons.lessons() == []
    print("[PASS] bad model output is swallowed, not raised")


if __name__ == "__main__":
    test_records_real_edit()
    test_ignores_noop_and_empty_edits()
    test_merge_counts_repeats_and_caps()
    test_lessons_prompt_shape()
    test_distill_marks_batch_and_merges()
    test_distill_survives_bad_model_output()
    print("OK")
