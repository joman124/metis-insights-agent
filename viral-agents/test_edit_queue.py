# -*- coding: utf-8 -*-
"""
Regression test for editing a queued post in the approval queue UI.

Drives the real app.py in-process with Streamlit's AppTest harness (no browser,
no model calls): seed a queued item, type into its edit box, click "Save edits", and
assert the new text is persisted to the ledger and a confirmation is shown and
stays on screen. This guards the bug where a save silently discarded the edit
(or hid its confirmation behind an immediate rerun).

The approval queue lives on the Review page, so the test must switch pages
first. AppTest cannot drive st.navigation's callable pages, so it sets
METIS_STUDIO=1 -- the same flag the unified dashboard sets -- which puts the app
on its sidebar-radio page switch, and selects "Review" through that.

Run:  python test_edit_queue.py
"""

import json
import os
import tempfile

import edit_lessons
import posts_ledger


def test_edit_persists_and_confirms():
    from streamlit.testing.v1 import AppTest

    # Isolate the ledger to a temp file so the test never touches real data.
    tmp = tempfile.mkdtemp()
    ledger = os.path.join(tmp, "posts.json")
    # Same for the edit-learning files: a save records the before/after pair
    # (edit_lessons.record_edit), and the test must not pollute real memory.
    edit_lessons.HISTORY_PATH = os.path.join(tmp, "edit_history.json")
    edit_lessons.LESSONS_PATH = os.path.join(tmp, "edit_lessons.json")
    original = "Most AI pilots die in the gap between demo and deploy."
    posts_ledger.save([], path=ledger)
    seeded = posts_ledger.add(
        topic="AI pilots stall before production", text=original,
        platform="linkedin", pillar="Strategic Thinking", path=ledger)
    rid = seeded["id"]

    # Point the app's module-level LEDGER_PATH at the temp file for this run.
    posts_ledger.LEDGER_PATH = ledger

    # Radio-based page switch (see module docstring), then open Review.
    os.environ["METIS_STUDIO"] = "1"
    at = AppTest(script_path="app.py", default_timeout=60).run()
    assert not at.exception, at.exception
    at.radio[0].set_value("Review").run()
    assert not at.exception, at.exception

    new_text = "Pilots stall in the deploy gap, not the demo. Fix the operating model."
    at.text_area(key="edit-%s" % rid).set_value(new_text).run()
    at.button(key="sv-%s" % rid).click().run()

    # 1. The edit is persisted to the ledger.
    saved = json.load(open(ledger, encoding="utf-8"))
    assert saved[0]["text"] == new_text, saved[0]["text"]
    assert saved[0]["status"] == "queued"

    # 2. A success confirmation is shown and survives (no rerun eats it).
    successes = [s.value for s in at.success]
    assert any(rid in s and "updated" in s for s in successes), successes

    # 3. The edit box still shows the new text (item did not vanish/collapse).
    assert at.text_area(key="edit-%s" % rid).value == new_text

    # 4. The before/after pair was recorded for the learning loop (no API
    # call happens at save time; distillation is deferred to draft time).
    recorded = json.load(open(edit_lessons.HISTORY_PATH, encoding="utf-8"))
    assert len(recorded) == 1, recorded
    assert recorded[0]["original"] == original
    assert recorded[0]["edited"] == new_text
    assert recorded[0]["distilled"] is False

    print("[PASS] edit persists, confirms, stays visible, and is recorded "
          "for learning:", repr(new_text))


if __name__ == "__main__":
    test_edit_persists_and_confirms()
    print("OK")
