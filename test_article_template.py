# -*- coding: utf-8 -*-
"""
Checks for the generated article page (site_builder.render_article): it uses
the metis-website article chrome, credits the firm rather than a person, and
never prints a personal name, email address or location. No API key needed --
pure string logic.

Run:  python test_article_template.py
"""

import json
import re

import site_builder
import content_publisher

ENTRY = {
    "id": "a-test-essay", "slug": "a-test-essay",
    "title": "A Test Essay", "dek": "A dek with <angle> & ampersand.",
    "pillar": "Team Dynamics & Culture Engineering", "topic": "teams",
    "format": "essay", "read_time": "5 min read", "published_date": "2026-08-02",
    "body_html": "<p>First paragraph.</p>\n        <p>Second.</p>",
}


def test_firm_byline():
    assert site_builder.BYLINE_NAME == "Metis Advisory Group"
    html = site_builder.render_article(ENTRY)
    assert '<div class="n">Metis Advisory Group</div>' in html, "byline must be the firm"
    for banned in ("Mansoor", "Dr. John", "PsyD", "Founding Partner", "drjohnmansoor"):
        assert banned not in html, "article must not name an individual: %r" % banned
    print("[OK] byline: credited to Metis Advisory Group, no personal name")


def test_no_contact_details():
    html = site_builder.render_article(ENTRY)
    # The only mailto is the reader's own share link, which has no address.
    for m in re.finditer(r'mailto:([^"?]*)', html):
        assert m.group(1) == "", "no email address may appear on the page"
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", html), "no email address may appear on the page"
    for banned in ("Phoenix", "Arizona", "Press &amp; partnerships"):
        assert banned not in html, "no location or press details: %r" % banned
    print("[OK] contact: no email address, location or press details")


def test_site_chrome_hooks():
    html = site_builder.render_article(ENTRY)
    for needle in ('href="../site/site.css"', 'href="../site/article.css"',
                   'src="../site/motion.js"', 'src="../site/insights-feed.js"',
                   'src="../site/article.js"', 'class="read-progress"',
                   'href="../businesses.html"', 'href="../individuals.html"',
                   'data-feed="related"', 'data-topics="teams"', 'data-exclude="a-test-essay"',
                   'href="../insights.html#topic=teams">Teams &amp; Culture</a>',
                   '<time datetime="2026-08-02">Aug 2, 2026</time>',
                   'href="https://www.metisag.com/insights/a-test-essay"'):
        assert needle in html, "missing site hook: %s" % needle
    assert "%%" not in html, "every template token must be filled"
    assert "<p>First paragraph.</p>" in html, "body must be inserted as-is"
    print("[OK] chrome: shared styles, scripts, feed hooks and canonical URL present")


def test_escaping_and_json_ld():
    hostile = dict(ENTRY, title="Close </script><b>x</b>", dek='Quote " and <tag>')
    html = site_builder.render_article(hostile)
    assert "<b>x</b>" not in html, "title must be escaped"
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert ld, "JSON-LD block must be present and must not be closed early"
    data = json.loads(ld.group(1))
    assert data["headline"] == hostile["title"], "JSON-LD must round-trip the title"
    assert data["author"]["@type"] == "Organization", "JSON-LD author is the firm"
    print("[OK] escaping: title/dek escaped, JSON-LD intact and firm-authored")


def test_degrades_without_slug_or_topic():
    html = site_builder.render_article(
        {"title": "T", "dek": "D", "pillar": "P", "format": "field_note",
         "read_time": "2 min read", "published_date": "2026-10-19", "body_html": "<p>x</p>"})
    assert ">Field note<" in html and "This field note comes out of" in html
    assert 'data-exclude="t"' in html, "slug falls back to the slugified title"
    assert "%%" not in html
    print("[OK] fallback: renders without slug or topic")


def test_publisher_stores_firm_byline():
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as site_dir:
        # Keep the publish-history write-back inside the temp dir so the test
        # never touches the repo's real memory/content_history.json.
        saved = content_publisher.CONTENT_HISTORY_PATH
        content_publisher.CONTENT_HISTORY_PATH = os.path.join(site_dir, "history.json")
        try:
            content_publisher.promote_to_site(
                "A body paragraph.\n\nAnother.", "essay", "Team Dynamics & Culture Engineering",
                title="Stored Byline", dek="D", site_dir=site_dir)
        finally:
            content_publisher.CONTENT_HISTORY_PATH = saved
        with open(site_dir + "/content/insights-data.json", encoding="utf-8") as f:
            data = json.load(f)
        assert data["featured"]["byline_name"] == "Metis Advisory Group"
        with open(site_dir + "/insights/stored-byline.html", encoding="utf-8") as f:
            assert "Mansoor" not in f.read()
    print("[OK] publish: data entry and article page carry the firm byline")


if __name__ == "__main__":
    test_firm_byline()
    test_no_contact_details()
    test_site_chrome_hooks()
    test_escaping_and_json_ld()
    test_degrades_without_slug_or_topic()
    test_publisher_stores_firm_byline()
    print("\nAll article-template tests passed.")
