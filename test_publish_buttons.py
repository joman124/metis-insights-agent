# -*- coding: utf-8 -*-
"""
Tests for the two publish buttons in the essays Drafts tab.

The property worth protecting: "Write files only" must never push. A wiring
slip there would put an unreviewed essay on the public site, so it is asserted
directly rather than assumed.

Both the publisher and the git layer are stubbed, so this touches no files, no
network, and never the real metis-website checkout.

Run:  python test_publish_buttons.py
"""

import os
import tempfile

import content_publisher
import edit_lessons
import site_git

ROOT = os.path.dirname(os.path.abspath(__file__))


class _Recorder:
    """Stands in for promote_to_site + site_git.publish_files and records how
    the UI called them."""

    def __init__(self):
        self.promoted = []
        self.pushed = []
        self.site_dir = tempfile.mkdtemp()

    def promote(self, **kwargs):
        self.promoted.append(kwargs)
        return {
            "entry": {"title": "A Test Essay", "slug": "a-test-essay"},
            "data_path": os.path.join(self.site_dir, "content", "insights-data.json"),
            "article_path": os.path.join(self.site_dir, "insights", "a-test-essay.html"),
            "site_dir": self.site_dir,
            "is_site": True,
            "history_entry": {},
        }

    def publish_files(self, **kwargs):
        self.pushed.append(kwargs)
        return {"ok": True, "pushed": True, "commit": "abc1234",
                "branch": "main",
                "msg": "Published and pushed (abc1234 on main)."}


def _seed_drafts_doc():
    """Write a one-essay fixture and point the app at it via METIS_DRAFTS_DOC.

    Without this the Drafts tab renders no rows at all: load_drafts() reads
    'Insights Drafts.docx', which is John's local review artifact and is not
    in the repo, so on a clean checkout there are no promote/live buttons to
    click and every test here dies with KeyError: 'promote-essay-0'.

    Built with the real doc_output.append_to_doc(), so this also exercises the
    write -> parse round trip rather than hand-rolling a fake docx.
    """
    import doc_output
    path = os.path.join(tempfile.mkdtemp(), "Insights Drafts.docx")
    doc_output.append_to_doc(
        path,
        "[Essay] A Test Essay",
        "First paragraph of the test essay.\n\nSecond paragraph.",
    )
    os.environ["METIS_DRAFTS_DOC"] = path
    return path


def _install(rec):
    content_publisher.promote_to_site = rec.promote
    site_git.publish_files = rec.publish_files
    # Keep the learning loop off real memory files.
    tmp = tempfile.mkdtemp()
    edit_lessons.HISTORY_PATH = os.path.join(tmp, "edit_history.json")
    edit_lessons.LESSONS_PATH = os.path.join(tmp, "edit_lessons.json")
    _seed_drafts_doc()


def _run_app():
    from streamlit.testing.v1 import AppTest
    at = AppTest(script_path=os.path.join(ROOT, "app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def test_write_files_only_never_pushes():
    rec = _Recorder()
    _install(rec)
    at = _run_app()
    at.button(key="promote-essay-0").click().run()
    assert not at.exception, at.exception
    assert len(rec.promoted) == 1, rec.promoted
    assert rec.pushed == [], "Write files only must never push: %r" % (rec.pushed,)
    infos = " ".join(m.value for m in at.info)
    assert "not public yet" in infos.lower(), infos
    print("[PASS] 'Write files only' writes but never pushes")


def test_publish_and_push_live_pushes_the_written_files():
    rec = _Recorder()
    _install(rec)
    at = _run_app()
    at.button(key="live-essay-0").click().run()
    assert not at.exception, at.exception
    assert len(rec.promoted) == 1, rec.promoted
    assert len(rec.pushed) == 1, "the live button must push once: %r" % (rec.pushed,)

    call = rec.pushed[0]
    # It must push exactly the files the publisher just wrote -- nothing else.
    expected = [
        os.path.join(rec.site_dir, "content", "insights-data.json"),
        os.path.join(rec.site_dir, "insights", "a-test-essay.html"),
    ]
    assert call["paths"] == expected, call["paths"]
    assert call["site_dir"] == rec.site_dir, call
    assert "A Test Essay" in call["message"], call["message"]

    successes = " ".join(s.value for s in at.success)
    assert "pushed" in successes.lower(), successes
    print("[PASS] 'Publish + push live' pushes exactly the written files")


def test_failed_push_is_reported_and_does_not_look_like_success():
    rec = _Recorder()
    _install(rec)
    site_git.publish_files = lambda **kw: {
        "ok": False, "pushed": False, "commit": "def5678", "branch": "main",
        "msg": "Committed locally (def5678) but the push failed, so it is not live yet."}
    at = _run_app()
    at.button(key="live-essay-0").click().run()
    assert not at.exception, at.exception
    errors = " ".join(e.value for e in at.error)
    assert "not live yet" in errors.lower(), errors
    # The write itself still succeeded, and the UI should say so.
    successes = " ".join(s.value for s in at.success)
    assert "wrote" in successes.lower(), successes
    print("[PASS] a failed push is surfaced as an error, not a success")


if __name__ == "__main__":
    test_write_files_only_never_pushes()
    test_publish_and_push_live_pushes_the_written_files()
    test_failed_push_is_reported_and_does_not_look_like_success()
    print("OK")
