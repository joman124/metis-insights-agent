# -*- coding: utf-8 -*-
"""
Checks for the discovery-call CTA (t40): the CTA_BLOCK constant, the append_cta
helper the writer agents use, and the article-page URL auto-linking that makes
the CTA link clickable. No API key needed -- pure string logic.

Run:  python test_cta_block.py
"""

from voice_profile import CTA_BLOCK, append_cta
import site_builder


def test_cta_block_shape():
    assert "calendly.com/jomansoor/30min" in CTA_BLOCK, "CTA must carry the booking link"
    assert CTA_BLOCK.lower().startswith("if this resonates"), \
        "CTA must use the 'If this resonates, ...' framing"
    # One paragraph, 2-3 sentences.
    sentence_count = CTA_BLOCK.rstrip(".").count(". ") + 1
    assert 2 <= sentence_count <= 3, "CTA should be 2-3 sentences, got %d" % sentence_count
    assert "\n\n" not in CTA_BLOCK, "CTA is a single paragraph"
    assert CTA_BLOCK.isascii(), "voice_profile.py is pure ASCII"


def test_append_cta_adds_block_as_own_paragraph():
    body = "A finished essay body.\n\nWith two paragraphs."
    out = append_cta(body)
    assert out.endswith(CTA_BLOCK), "CTA must be appended at the end"
    assert out == body + "\n\n" + CTA_BLOCK, "CTA must be its own blank-line-separated paragraph"


def test_append_cta_is_idempotent():
    body = "Essay body."
    once = append_cta(body)
    twice = append_cta(once)
    assert once == twice, "append_cta must not double-append"
    assert once.count(CTA_BLOCK) == 1


def test_published_cta_link_is_clickable():
    html = site_builder.paragraphs_html(append_cta("The body."))
    assert '<a href="https://calendly.com/jomansoor/30min"' in html, \
        "bare CTA URL must render as an anchor on the article page"
    assert 'rel="noopener"' in html


def test_linkify_does_not_break_escaping():
    # Non-URL angle brackets still get escaped; only http(s) URLs are linked.
    html = site_builder.paragraphs_html("Risk < reward and a > b.")
    assert "&lt;" in html and "&gt;" in html
    assert "<a " not in html


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("[PASS] " + name)
    print("\nAll CTA checks passed.")
