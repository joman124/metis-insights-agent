# -*- coding: utf-8 -*-
"""
Tests for the case-study content type (decision c14: inside Insights, by
pillar, named-with-consent).

The properties worth protecting, asserted directly rather than assumed:
  1. The orchestrator routes "case study" requests to the case_study pipeline,
     and does NOT mistake them for essays or field notes.
  2. promote_to_site accepts fmt="case_study", stamps a consent field, and
     slots the piece into the essay grid (it rides Insights) without taking the
     featured slot.
  3. A case study marked consent="unpublished" is refused -- no page is ever
     written for it, so a story that cannot go out yet cannot leak.
  4. The rendered article page is labeled "Case Study", not "Essay".

No API key and no real site checkout are touched: titles/deks are passed in so
the metadata model call never runs, and output goes to a temp dir.

Run:  python test_case_study.py
"""

import os
import tempfile

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")

from agents.orchestrator import route  # noqa: E402
import content_publisher  # noqa: E402
import site_builder  # noqa: E402
from pillars import PILLAR_NAMES  # noqa: E402

PILLAR = PILLAR_NAMES[0]
BODY = ("A founder kept reshaping the same org chart. Each redraw moved the "
        "conflict without naming who decided what.\n\n"
        "We made the decision rights explicit before touching the structure. "
        "The arguments that followed were the first honest ones in a year.")


def test_routing():
    intent, topic = route("Draft a case study about a stalled succession plan")
    assert intent == "case_study", intent
    assert topic == "a stalled succession plan", topic

    # A hyphenated spelling still routes to case_study.
    assert route("write a case-study on board dynamics")[0] == "case_study"

    # And a plain essay / field note request is NOT captured by the new branch.
    assert route("Draft an essay about board AI governance")[0] == "essay"
    assert route("Write a field note about return-to-office")[0] == "field_note"
    print("[OK] routing: case study, essay, and field note stay distinct")


def _promote(site_dir, consent=None):
    # Keep the publish-history write-back inside the temp dir so the test never
    # touches the repo's real memory/content_history.json.
    content_publisher.MEMORY_DIR = site_dir
    content_publisher.CONTENT_HISTORY_PATH = os.path.join(site_dir, "history.json")
    return content_publisher.promote_to_site(
        body=BODY, fmt="case_study", pillar=PILLAR,
        title="The Reorg That Kept Reorganizing",
        dek="What a team avoids when it changes its shape.",
        site_dir=site_dir, consent=consent)


def test_promote_defaults_and_bucketing():
    with tempfile.TemporaryDirectory() as site_dir:
        res = _promote(site_dir)
        entry = res["entry"]
        assert entry["format"] == "case_study", entry["format"]
        assert entry["consent"] == "anonymized", entry["consent"]  # safe default
        assert entry["pillar"] == PILLAR
        assert entry["topic"], "case study must be pillar-tagged like everything else"

        data = content_publisher.load_data(site_dir)
        # Rides the essay grid, does NOT hijack the featured slot.
        assert data["featured"] is None, "case study must not become featured"
        assert any(e["slug"] == entry["slug"] for e in data["essays"]), \
            "case study should land in the essays bucket"
        assert os.path.exists(res["article_path"]), "article page must be written"
    print("[OK] promote: anonymized default, pillar-tagged, essay grid, not featured")


def test_named_consent_recorded():
    with tempfile.TemporaryDirectory() as site_dir:
        res = _promote(site_dir, consent="named")
        assert res["entry"]["consent"] == "named", res["entry"]["consent"]
        assert res["history_entry"]["consent"] == "named"
    print("[OK] promote: named consent is carried onto the entry and history")


def test_unpublished_is_refused():
    with tempfile.TemporaryDirectory() as site_dir:
        raised = False
        try:
            _promote(site_dir, consent="unpublished")
        except ValueError:
            raised = True
        assert raised, "consent='unpublished' must refuse to promote"
        # Nothing was written.
        assert not os.path.exists(os.path.join(site_dir, "insights")), \
            "no article page may be written for an unpublished case study"
    print("[OK] promote: unpublished case study is refused, no files written")


def test_article_label():
    html = site_builder.render_article(
        {"title": "T", "dek": "D", "pillar": PILLAR, "format": "case_study",
         "read_time": "5 min read", "published_date": "2026-10-19",
         "body_html": "<p>x</p>"})
    assert "Case Study" in html, "article page must be labeled Case Study"
    assert ">Essay<" not in html, "a case study must not be labeled Essay"
    print("[OK] article: labeled 'Case Study', not 'Essay'")


if __name__ == "__main__":
    test_routing()
    test_promote_defaults_and_bucketing()
    test_named_consent_recorded()
    test_unpublished_is_refused()
    test_article_label()
    print("\nAll case-study tests passed.")
