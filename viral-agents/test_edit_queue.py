# -*- coding: utf-8 -*-
"""
Regression test for editing a queued post in the approval queue UI.

Drives the real app.py in-process with Streamlit's AppTest harness (no browser,
no Gemini): seed a queued item, type into its edit box, click "Save edits", and
assert the new text is persisted to the ledger and a confirmation is shown and
stays on screen. This guards the bug where a save silently discarded the edit
(or hid its confirmation behind an immediate rerun).

Run:  python test_edit_queue.py
"""

import json
import os
import tempfile

import posts_ledger


def test_edit_persists_and_confirms():
    from streamlit.testing.v1 import AppTest

    # Isolate the ledger to a temp file so the test never touches real data.
    tmp = tempfile.mkdtemp()
    ledger = os.path.join(tmp, "posts.json")
    original = "Most AI pilots die in the gap between demo and deploy."
    posts_ledger.save([], path=ledger)
    seeded = posts_ledger.add(
        topic="AI pilots stall before production", text=original,
        platform="linkedin", pillar="Strategic Thinking", path=ledger)
    rid = seeded["id"]

    # Point the app's module-level LEDGER_PATH at the temp file for this run.
    posts_ledger.LEDGER_PATH = ledger

    at = AppTest(script_path="app.py", default_timeout=60).run()
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

    print("[PASS] edit persists, confirms, and stays visible:", repr(new_text))


if __name__ == "__main__":
    test_edit_persists_and_confirms()
    print("OK")
