# -*- coding: utf-8 -*-
"""
Renders an approved draft into a standalone static article page for the
metis-website repo. The page uses the site's shared chrome and styles
(colors_and_type.css, site/site.css, site/article.css) and scripts (motion,
the Insights feed for related reading, the reading-progress bar), so a new
essay looks like every other article on metisag.com. Article pages live at
insights/<slug>.html, so all shared assets are referenced with a "../" prefix.

Pieces are credited to the firm, never to an individual: the site speaks as
Metis Advisory Group throughout, and no personal name, email address or
location appears on a generated page.

Pure string templating (no external template engine), pure ASCII source. The
live site stays "just HTML/CSS/JS" -- these pages are generated at publish
time, not built in the visitor's browser.
"""

import json
import re
import unicodedata
from datetime import date
from urllib.parse import quote

from pillars import PILLARS
from voice_profile import CONTENT_RULES

# Firm byline. Stored on every insights-data.json entry and shown on the page.
BYLINE_NAME = "Metis Advisory Group"
BYLINE_ROLE = "Insights"

SITE_URL = "https://www.metisag.com"
BOOKING_URL = "https://calendly.com/jomansoor/30min"
_CHIP = {p["key"]: p["chip"] for p in PILLARS}
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def slugify(title: str) -> str:
    """A filesystem- and URL-safe slug from a title."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "untitled"


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


_URL_RE = re.compile(r"https?://[^\s<>\"]+")


def _linkify(escaped: str) -> str:
    """Wrap bare http(s) URLs in an anchor. Runs AFTER _escape, so the input is
    already HTML-safe (quotes are &quot;, so a URL cannot break out of the href
    attribute) and only well-formed http(s) links become anchors. Lets the
    discovery-call CTA render clickable on the article page."""
    return _URL_RE.sub(
        lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>'
                  % (m.group(0), m.group(0)),
        escaped,
    )


def paragraphs_html(body: str) -> str:
    """Turn a plain-text body (paragraphs separated by blank lines) into
    escaped <p> blocks, with bare URLs linked."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]
    if not blocks:
        blocks = [body.strip()]
    return "\n        ".join(
        "<p>" + _linkify(_escape(b)).replace("\n", "<br>") + "</p>" for b in blocks)


def read_time(body: str, fmt: str = "essay") -> str:
    """A 'N min read' label from the word count and the format's reading
    speed."""
    wpm = CONTENT_RULES.get(fmt, CONTENT_RULES["essay"])["words_per_minute"]
    minutes = max(1, round(len(body.split()) / wpm))
    return f"{minutes} min read"


def quarter_label(published_date: str = None) -> str:
    """A 'YYYY . Qn' label (year and quarter) used on field-note rows."""
    d = date.fromisoformat(published_date) if published_date else date.today()
    q = (d.month - 1) // 3 + 1
    return f"{d.year} " + chr(0x00B7) + f" Q{q}"


_ARROW = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
          'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" '
          'x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/></svg>')

# Mirrors the article pages in metis-website (insights/*.html). Every
# non-ASCII character is written as an HTML entity so this source stays ASCII.
_ARTICLE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%% | Insights | Metis Advisory Group</title>
  <meta name="description" content="%%DEK%%">
  <link rel="canonical" href="%%URL%%">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#1C1E3F">
  <meta property="og:site_name" content="Metis Advisory Group">
  <meta property="og:type" content="article">
  <meta property="article:published_time" content="%%ISO_DATE%%">
  <meta property="article:author" content="Metis Advisory Group">
  <meta property="article:section" content="%%PILLAR%%">
  <meta property="og:title" content="%%TITLE%% | Insights | Metis Advisory Group">
  <meta property="og:description" content="%%DEK%%">
  <meta property="og:url" content="%%URL%%">
  <meta property="og:image" content="%%SITE%%/assets/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" type="image/png" href="../assets/logo-deep-indigo-transparent.png">
  <link rel="apple-touch-icon" href="../assets/logo-deep-indigo.png">
  <link rel="alternate" type="application/json" title="Metis Insights" href="../content/insights-data.json">
  <link rel="preload" href="../fonts/LibreFranklin-Light.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="stylesheet" href="../colors_and_type.css">
  <link rel="stylesheet" href="../site/site.css">
  <script src="../site/reveal.js"></script>
  <link rel="stylesheet" href="../site/article.css">
  <script type="application/ld+json">%%JSONLD%%</script>
  <!-- Calendly popup widget -->
  <link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
  <script src="https://assets.calendly.com/assets/external/widget.js" async></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="top">
    <a class="brand" href="../index.html" aria-label="Metis Advisory Group, home">
      <img src="../assets/logo-deep-indigo-transparent.png" alt="" width="34" height="34">
      <span>Metis Advisory Group</span>
    </a>
    <nav id="site-nav" aria-label="Primary">
      <a href="../businesses.html">For Businesses</a>
      <a href="../individuals.html">For Individuals</a>
      <a href="../insights.html" class="nav-insights" aria-current="page"><span class="pulse-dot" aria-hidden="true"></span>Insights</a>
      <a href="../approach.html">Approach</a>
      <a href="../contact.html">Contact</a>
      <a class="btn btn--primary nav-cta-mobile" href="%%BOOKING%%" target="_blank" rel="noopener" data-calendly>Book a free conversation</a>
    </nav>
    <a class="btn btn--primary btn--sm" href="%%BOOKING%%" target="_blank" rel="noopener" data-calendly>Book a call %%ARROW%%</a>
    <button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false" aria-label="Open menu"><span></span><span></span><span></span></button>
  </header>

  <main id="main">
    <div class="read-progress" aria-hidden="true"><span></span></div>
    <article>
      <header class="art-head">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="../insights.html">&larr;&nbsp; Insights</a><span aria-hidden="true">/</span><a href="../insights.html#topic=%%TOPIC%%">%%CHIP%%</a></nav>
        <p class="eyebrow eyebrow--rule">%%PILLAR%%</p>
        <h1>%%TITLE%%</h1>
        <p class="dek">%%DEK%%</p>
        <div class="art-meta">
          <span class="avatar" aria-hidden="true"><img src="../assets/logo-soft-bone-transparent.png" alt=""></span>
          <div class="who"><div class="n">%%BYLINE_NAME%%</div><div class="r">%%BYLINE_ROLE%%</div></div>
          <div class="facts"><span>%%FORMAT_LABEL%%</span><span class="dot">&middot;</span><span>%%READ_TIME%%</span><span class="dot">&middot;</span><time datetime="%%ISO_DATE%%">%%DATE%%</time></div>
        </div>
      </header>

      <div class="article-body">
        %%BODY%%
      </div>
      <div class="art-fin" aria-hidden="true"><span></span><span></span><span></span></div>

      <footer class="art-end">
        <div class="author-card">
          <span class="avatar" aria-hidden="true"><img src="../assets/logo-soft-bone-transparent.png" alt=""></span>
          <div>
            <span class="k">From the practice</span>
            <h2>Metis Advisory Group</h2>
            <p>A psychologically informed advisory practice grounded in clinical psychology. We consult with organizations and coach the people who lead them; Insights is where we write down what the work teaches us.</p>
            <div class="links">
              <a class="link-arrow" href="../approach.html">Our approach &rarr;</a>
              <a class="link-arrow" href="../services.html">Work with us &rarr;</a>
            </div>
          </div>
        </div>
        <div class="share">
          <span class="lbl">Share</span>
          <a href="https://www.linkedin.com/sharing/share-offsite/?url=%%QURL%%" target="_blank" rel="noopener">LinkedIn</a>
          <a href="mailto:?subject=%%QTITLE%%&amp;body=%%QURL%%">Email</a>
          <button type="button" data-copy-link="%%URL%%"><span>Copy link</span></button>
        </div>
      </footer>
    </article>

    <section class="art-cta">
      <div class="wrap">
        <div class="sec-head" style="margin-bottom:36px">
          <div>
            <p class="eyebrow eyebrow--rule">Is this your situation?</p>
            <h2 class="h2">Let's talk about <em>yours</em>.</h2>
          </div>
          <p>This %%FORMAT_NOUN%% comes out of the work we do with organizations and the leaders inside them. A free 30-minute conversation is the easiest way to find out whether we can help.</p>
        </div>
        <div class="crosssell">
          <a href="../businesses.html"><span><span class="k">For Businesses</span><span class="t">Bring this into your leadership team</span></span><span class="arr">%%ARROW%%</span></a>
          <a href="../individuals.html"><span><span class="k">For Individuals</span><span class="t">Work on this one-to-one</span></span><span class="arr">%%ARROW%%</span></a>
        </div>
      </div>
    </section>

    <section class="section section--raised">
      <div class="wrap">
        <div class="sec-head" data-reveal>
          <div>
            <p class="eyebrow eyebrow--rule">Keep reading</p>
            <h2 class="h2">More from <em>Insights</em>.</h2>
          </div>
          <p>Essays from the same practice. <a class="link-arrow" href="../insights.html" style="margin-left:6px">All insights &rarr;</a></p>
        </div>
        <!-- Filled from content/insights-data.json by site/insights-feed.js -->
        <div class="related-list" data-feed="related" data-topics="%%TOPIC%%" data-limit="3" data-exclude="%%SLUG%%" data-reveal></div>
      </div>
    </section>

    <section class="section--tight" style="padding-top:0">
      <div class="wrap">
        <div class="subscribe" id="subscribe" data-reveal>
          <svg viewBox="0 0 160 100" aria-hidden="true" class="wm"><path d="M40 50 C 40 20 80 20 80 50 C 80 80 120 80 120 50 C 120 20 80 20 80 50 C 80 80 40 80 40 50 Z" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>
          <div>
            <p class="eyebrow eyebrow--rule">The Insights letter</p>
            <h2 class="h2">New essays, <em>the morning</em> they publish.</h2>
            <p>One email when something new goes up. Psychology for people who lead, written without filler. Unsubscribe in one click.</p>
          </div>
          <div>
            <iframe src="https://metisag.substack.com/embed" title="Subscribe to the Metis Insights letter" loading="lazy" frameborder="0" scrolling="no"></iframe>
            <div class="small">Delivered by Substack. Or read it there: <a href="https://metisag.substack.com" target="_blank" rel="noopener" style="color:var(--metis-charred-plum)">metisag.substack.com</a></div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <footer class="foot on-dark">
    <img class="wm" src="../assets/logo-soft-bone-transparent.png" alt="">
    <div class="wrap">
      <div class="foot-grid">
        <div>
          <p class="tagline">Wisdom at Work.<br>Guided by Insight.<br>Grounded in Humanity.</p>
          <a class="letter" href="../insights.html#subscribe"><b>The Insights letter</b><span>New essays on the psychology of leadership, sent when they publish &nbsp;&rarr;</span></a>
        </div>
        <div>
          <h2>For Businesses</h2>
          <ul>
            <li><a href="../businesses.html#consulting">Organizational consulting</a></li>
            <li><a href="../businesses.html#diagnostics">Diagnostics</a></li>
            <li><a href="../businesses.html#leadership-development">Leadership development</a></li>
            <li><a href="../businesses.html#retainer">Retainer advisory</a></li>
            <li><a href="../businesses.html#workshops">Workshops &amp; keynotes</a></li>
          </ul>
        </div>
        <div>
          <h2>For Individuals</h2>
          <ul>
            <li><a href="../individuals.html#executive-coaching">Executive coaching</a></li>
            <li><a href="../individuals.html#group-coaching">Group coaching</a></li>
            <li><a href="../individuals.html#intensives">Leadership intensives</a></li>
            <li><a href="../individuals.html#strategy-sessions">Strategy sessions</a></li>
          </ul>
        </div>
        <div>
          <h2>Insights</h2>
          <ul>
            <li><a href="../insights.html">Latest essays</a></li>
            <li><a href="../insights.html#topic=self-mastery">Self-mastery</a></li>
            <li><a href="../insights.html#topic=teams">Teams &amp; culture</a></li>
            <li><a href="../insights.html#topic=change">Change</a></li>
            <li><a href="../insights.html#subscribe">Subscribe</a></li>
          </ul>
        </div>
        <div>
          <h2>The firm</h2>
          <ul>
            <li><a href="../approach.html">Approach</a></li>
            <li><a href="../services.html">All services</a></li>
            <li><a href="../contact.html">Contact</a></li>
            <li><a href="%%BOOKING%%" target="_blank" rel="noopener" data-calendly>Book a call</a></li>
          </ul>
        </div>
      </div>
      <div class="foot-base">
        <span>&copy; %%YEAR%% Metis Advisory Group, LLC &middot; metisag.com</span>
        <span class="motto">Recognize &middot; Discern &middot; Recalibrate</span>
      </div>
    </div>
  </footer>
  <!-- Motion: weighted scroll, scroll-tied glyphs, card tilt; then site behavior -->
  <script src="../site/smooth-scroll.min.js"></script>
  <script src="../site/glyph-motion.min.js"></script>
  <script src="../site/cursor-fx.min.js"></script>
  <script src="../site/site.js"></script>
  <script src="../site/motion.js"></script>
  <script src="../site/insights-feed.js"></script>
  <script src="../site/article.js"></script>
</body>
</html>
"""


def pretty_date(published_date: str) -> str:
    """'2026-08-02' -> 'Aug 2, 2026'. Anything unparseable is returned as-is."""
    try:
        d = date.fromisoformat(published_date)
    except (TypeError, ValueError):
        return published_date or ""
    return "%s %d, %d" % (_MONTHS[d.month - 1], d.day, d.year)


def _json_ld(entry: dict, url: str) -> str:
    """BlogPosting structured data, authored by the firm. Escaped so a title
    can never close the surrounding <script> tag."""
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": entry.get("title", ""),
        "description": entry.get("dek") or "",
        "datePublished": entry.get("published_date") or "",
        "dateModified": entry.get("published_date") or "",
        "mainEntityOfPage": url,
        "url": url,
        "image": SITE_URL + "/assets/og-image.png",
        "articleSection": entry.get("pillar", ""),
        "author": {"@type": "Organization", "name": "Metis Advisory Group", "url": SITE_URL + "/"},
        "publisher": {"@type": "Organization", "name": "Metis Advisory Group",
                      "logo": {"@type": "ImageObject", "url": SITE_URL + "/assets/logo-deep-indigo.png"}},
    }
    text = json.dumps(ld, ensure_ascii=True)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_article(entry: dict) -> str:
    """Render a full standalone article page from an insights-data entry.
    Expects keys: title, dek, pillar, format, read_time, published_date,
    body_html; slug and topic are used when present. Missing optional fields
    degrade gracefully."""
    fmt = entry.get("format", "essay")
    format_label = {"field_note": "Field note",
                    "case_study": "Case Study"}.get(fmt, "Essay")
    format_noun = {"field_note": "field note",
                   "case_study": "case study"}.get(fmt, "essay")
    title = entry.get("title", "Untitled")
    slug = entry.get("slug") or slugify(title)
    topic = entry.get("topic", "")
    url = SITE_URL + "/insights/" + slug
    published = entry.get("published_date") or ""
    replacements = {
        "%%TITLE%%": _escape(title),
        "%%DEK%%": _escape(entry.get("dek") or ""),
        "%%PILLAR%%": _escape(entry.get("pillar", "")),
        "%%TOPIC%%": _escape(topic),
        "%%CHIP%%": _escape(_CHIP.get(topic, "Insights")),
        "%%SLUG%%": _escape(slug),
        "%%FORMAT_LABEL%%": format_label,
        "%%FORMAT_NOUN%%": format_noun,
        "%%READ_TIME%%": _escape(entry.get("read_time", "")),
        "%%ISO_DATE%%": _escape(published),
        "%%DATE%%": _escape(pretty_date(published)),
        "%%BYLINE_NAME%%": _escape(BYLINE_NAME),
        "%%BYLINE_ROLE%%": _escape(BYLINE_ROLE),
        "%%URL%%": url,
        "%%QURL%%": quote(url, safe=""),
        "%%QTITLE%%": quote(title, safe=""),
        "%%SITE%%": SITE_URL,
        "%%BOOKING%%": BOOKING_URL,
        "%%ARROW%%": _ARROW,
        "%%YEAR%%": str(date.today().year),
        "%%JSONLD%%": _json_ld(entry, url),
    }
    html = _ARTICLE_TEMPLATE
    for token, value in replacements.items():
        html = html.replace(token, value)
    # The body goes in last, so text inside it that happens to look like a
    # %%TOKEN%% is never substituted.
    return html.replace("%%BODY%%", entry.get("body_html", ""))
