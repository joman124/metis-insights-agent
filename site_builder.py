# -*- coding: utf-8 -*-
"""
Renders an approved draft into a standalone static article page for the
metis-website repo, matching the Insights page's header, footer, and design
system (colors_and_type.css). Article pages live at insights/<slug>.html, so
all shared assets are referenced with a "../" prefix.

Pure string templating (no external template engine), pure ASCII source. The
live site stays "just HTML/CSS/JS" -- these pages are generated at publish
time, not built in the visitor's browser.
"""

import re
import unicodedata
from datetime import date

from voice_profile import CONTENT_RULES

BYLINE_NAME = "Dr. John Mansoor"
BYLINE_ROLE = "Founding Partner"


def slugify(title: str) -> str:
    """A filesystem- and URL-safe slug from a title."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "untitled"


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def paragraphs_html(body: str) -> str:
    """Turn a plain-text body (paragraphs separated by blank lines) into
    escaped <p> blocks."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]
    if not blocks:
        blocks = [body.strip()]
    return "\n        ".join("<p>" + _escape(b).replace("\n", "<br>") + "</p>" for b in blocks)


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


_ARTICLE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%% | Insights | Metis Advisory Group</title>
  <meta name="description" content="%%DEK%%">
  <link rel="icon" type="image/png" href="../assets/logo-deep-indigo-transparent.png">
  <link rel="stylesheet" href="../colors_and_type.css">
  <style>
    body { margin:0; font-family: var(--font-sans); font-weight: 300; background: var(--bone-200); color: var(--metis-deep-indigo); -webkit-font-smoothing: antialiased; }
    a { color: inherit; }
    .top { position: fixed; top:0; left:0; right:0; height:72px; display:flex; align-items:center; padding:0 48px; background: rgba(246,244,242,0.85); backdrop-filter: blur(14px); border-bottom: 1px solid rgba(28,30,63,0.06); z-index:100; }
    .top .brand { display:flex; align-items:center; gap:12px; text-decoration:none; color: var(--metis-deep-indigo); border:0; font-weight:600; }
    .top nav { display:flex; gap:28px; margin-left:48px; flex:1; justify-content: flex-end; padding-right: 24px; }
    .top nav a { font-size:13px; text-decoration:none; border:0; color: var(--slate-700); }
    .top nav a.active { color: var(--metis-deep-indigo); font-weight:500; }
    .top .cta { display:inline-flex; align-items:center; gap:8px; padding:11px 18px; border-radius:8px; background:var(--metis-charred-plum); color:var(--bone-200); font-size:13px; font-weight:500; text-decoration:none; border:0; }
    main { padding: 128px 24px 96px; }
    article { max-width: 720px; margin: 0 auto; }
    .back { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--metis-charred-plum); text-decoration: none; border-bottom: 1px solid currentColor; padding-bottom: 2px; }
    .eyebrow { font-family: var(--font-mono); font-size: 11px; font-weight:500; letter-spacing:0.2em; text-transform:uppercase; color:var(--metis-charred-plum); margin: 40px 0 0; }
    h1 { font-size: clamp(34px, 5vw, 56px); font-weight: 300; letter-spacing: -0.025em; line-height: 1.06; margin: 18px 0 20px; text-wrap: balance; }
    .dek { font-size: 20px; line-height: 1.5; font-weight: 300; color: var(--slate-700); margin: 0 0 32px; }
    .meta { display:flex; gap:16px; font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--slate-600); font-weight:500; padding: 24px 0; border-top: 1px solid rgba(28,30,63,0.10); border-bottom: 1px solid rgba(28,30,63,0.10); }
    .meta .dot { color: var(--metis-charred-plum); }
    .article-body { font-size: 18px; line-height: 1.7; font-weight: 300; color: var(--metis-deep-indigo); margin-top: 40px; }
    .article-body p { margin: 0 0 24px; }
    .byline { display:flex; align-items:center; gap:14px; margin-top: 56px; padding-top: 24px; border-top: 1px solid rgba(28,30,63,0.10); }
    .byline .name { font-size: 13px; font-weight: 500; color: var(--metis-deep-indigo); }
    .byline .role { font-family: var(--font-display); font-style: italic; font-size: 13px; color: var(--slate-600); }
    footer { background: var(--metis-deep-indigo); color: var(--bone-200); padding: 64px 48px 36px; margin-top: 96px; }
    footer .row { display:flex; justify-content: space-between; align-items: center; max-width: 1120px; margin:0 auto; }
    footer .row a { color: var(--bone-200); font-size: 13px; margin-left: 24px; text-decoration: none; border: 0; }
    footer .quote { font-family: var(--font-display); font-style: italic; font-size: 20px; max-width: 380px; line-height: 1.4; }
    @media (max-width: 820px) { .top { padding: 0 20px; } main { padding: 104px 20px 64px; } footer { padding: 56px 24px 32px; } footer .row { flex-direction: column; align-items: flex-start; gap: 24px; } }
  </style>
</head>
<body>
  <header class="top">
    <a class="brand" href="../index.html">
      <img src="../assets/logo-deep-indigo-transparent.png" style="height:32px;" alt="">
      <span>Metis Advisory Group</span>
    </a>
    <nav>
      <a href="../approach.html">Approach</a>
      <a href="../services.html">Services</a>
      <a href="../insights.html" class="active">Insights</a>
      <a href="../contact.html">Contact</a>
    </nav>
    <a class="cta" href="https://calendly.com/jomansoor/30min" target="_blank" rel="noopener">Schedule</a>
  </header>

  <main>
    <article>
      <a class="back" href="../insights.html">&larr;&nbsp; All insights</a>
      <p class="eyebrow">%%PILLAR%%</p>
      <h1>%%TITLE%%</h1>
      <p class="dek">%%DEK%%</p>
      <div class="meta">
        <span>%%FORMAT_LABEL%%</span>
        <span class="dot">%%DOT%%</span>
        <span>%%READ_TIME%%</span>
        <span class="dot">%%DOT%%</span>
        <span>%%DATE%%</span>
      </div>
      <div class="article-body">
        %%BODY%%
      </div>
      <div class="byline">
        <div>
          <div class="name">%%BYLINE_NAME%%</div>
          <div class="role">%%BYLINE_ROLE%%</div>
        </div>
      </div>
    </article>
  </main>

  <footer>
    <div class="row">
      <div class="quote">Wisdom at Work.<br>Guided by Insight.<br>Grounded in Humanity.</div>
      <div>
        <a href="../index.html">Home</a>
        <a href="../approach.html">Approach</a>
        <a href="../services.html">Services</a>
        <a href="../insights.html">Insights</a>
        <a href="../contact.html">Contact</a>
      </div>
    </div>
    <div style="text-align:center; margin-top:48px; font-size:11px; color:var(--slate-400); letter-spacing:0.04em;">%%COPYRIGHT%%</div>
  </footer>
</body>
</html>
"""


def render_article(entry: dict) -> str:
    """Render a full standalone article HTML page from an insights-data entry.
    Expects keys: title, dek, pillar, format, read_time, published_date,
    body_html. Missing optional fields degrade gracefully."""
    fmt = entry.get("format", "essay")
    format_label = "Field note" if fmt == "field_note" else "Essay"
    dek = entry.get("dek") or ""
    replacements = {
        "%%TITLE%%": _escape(entry.get("title", "Untitled")),
        "%%DEK%%": _escape(dek),
        "%%PILLAR%%": _escape(entry.get("pillar", "")),
        "%%FORMAT_LABEL%%": format_label,
        "%%READ_TIME%%": _escape(entry.get("read_time", "")),
        "%%DATE%%": _escape(entry.get("published_date", "")),
        "%%BODY%%": entry.get("body_html", ""),
        "%%BYLINE_NAME%%": BYLINE_NAME,
        "%%BYLINE_ROLE%%": BYLINE_ROLE,
        "%%DOT%%": chr(0x00B7),
        "%%COPYRIGHT%%": chr(0x00A9) + " " + str(date.today().year)
                         + " Metis Advisory Group, LLC " + chr(0x00B7) + " metisag.com",
    }
    html = _ARTICLE_TEMPLATE
    for token, value in replacements.items():
        html = html.replace(token, value)
    return html
