# -*- coding: utf-8 -*-
"""
Streamlit UI for the Metis Insights Agent.

The front door John sees. It wraps the Orchestrator so a natural-language
request ("What should we publish this quarter?") runs the whole agent pipeline,
and it renders the system's real state -- the planned cycle, the generated
drafts, and the observability trace -- without needing any API call. From the
Drafts tab, an approved piece can be promoted to the site
(content_publisher.promote_to_site): that writes content/insights-data.json and
a standalone article page into the metis-website checkout for John to commit.

Run:  streamlit run app.py

Kept pure ASCII on purpose: non-UTF-8 saves on Windows crash Python on
em-dashes and curly quotes.
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv

from pillars import PILLAR_NAMES
from voice_profile import USING_PLACEHOLDER_REFERENCES

load_dotenv(override=True)

CALENDAR_PATH = os.path.join("memory", "calendar.json")
TRACE_PATH = os.path.join("logs", "agent_trace.jsonl")
DRAFTS_DOC = "Insights Drafts.docx"


# --------------------------------------------------------------------------
# Data helpers (read-only; no Gemini calls, safe to run anytime)
# --------------------------------------------------------------------------
def load_calendar():
    if not os.path.exists(CALENDAR_PATH):
        return []
    try:
        with open(CALENDAR_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []


def load_drafts(doc_path):
    """Parse the drafts .docx into a list of {heading, body, format, topic}.

    doc_output.append_to_doc() writes a level-1 title once, then a level-2
    heading per draft ("[Essay] <topic> -- <date>" / "[Field note] ...")
    followed by body paragraphs. We group on the level-2 headings.
    """
    if not os.path.exists(doc_path):
        return []
    try:
        from docx import Document
    except ImportError:
        return []
    try:
        doc = Document(doc_path)
    except OSError:
        return []

    entries = []
    current = None
    for para in doc.paragraphs:
        text = para.text.strip()
        style = para.style.name if para.style else ""
        if style == "Heading 1":
            continue
        if style == "Heading 2":
            if current:
                entries.append(current)
            current = {"heading": text, "body": []}
        elif current is not None and text:
            current["body"].append(text)
    if current:
        entries.append(current)

    for e in entries:
        e["body"] = "\n\n".join(e["body"])
        heading = e["heading"]
        if heading.startswith("[Field note]"):
            e["format"] = "field_note"
            rest = heading[len("[Field note]"):].strip()
        elif heading.startswith("[Case study]"):
            e["format"] = "case_study"
            rest = heading[len("[Case study]"):].strip()
        elif heading.startswith("[Essay]"):
            e["format"] = "essay"
            rest = heading[len("[Essay]"):].strip()
        else:
            e["format"] = "essay"
            rest = heading
        # Strip the trailing " -- <date>" doc_output appends.
        e["topic"] = rest.rsplit(" -- ", 1)[0].strip()
    return entries


def load_trace(limit=40):
    if not os.path.exists(TRACE_PATH):
        return []
    rows = []
    try:
        with open(TRACE_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows[-limit:]


def has_api_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def render_draft_column(entries, fmt, label):
    """One Drafts-tab column of drafts of a given format, each in an expander
    with a 'Promote to site' control that runs content_publisher.promote_to_site
    -- writing the site data file + article page and recording history."""
    drafts = [e for e in entries if e["format"] == fmt]
    if not drafts:
        st.info("No %s drafts yet in %s." % (label.lower(), DRAFTS_DOC))
        return

    st.caption("%d %s draft(s)" % (len(drafts), label.lower()))

    # Recover a default pillar from the calendar by matching the draft topic.
    topic_to_pillar = {}
    for d in load_calendar():
        key = d.get("topic") or d.get("pillar")
        if key:
            topic_to_pillar[key] = d.get("pillar")

    promoted = st.session_state.setdefault("promoted", set())

    for i, e in enumerate(reversed(drafts)):
        heading = e["heading"]
        title = heading[:90] + ("..." if len(heading) > 90 else "")
        with st.expander(title):
            if heading in promoted:
                st.success("Promoted to the site this session.")
                st.write(e["body"])
                continue
            # Editable draft: John can revise the text (and optionally set the
            # title) right here before it is published. The edited text is what
            # gets promoted.
            edited_body = st.text_area(
                "Draft (edit freely before publishing)", value=e["body"],
                height=360, key="body-%s-%d" % (fmt, i))
            title_override = st.text_input(
                "Title (optional -- leave blank to auto-generate)",
                key="title-%s-%d" % (fmt, i))
            subject = None
            if fmt == "case_study":
                subject = st.text_input(
                    "Subject (the company or leader this case study analyzes)",
                    value=e["topic"], key="subject-%s-%d" % (fmt, i))
            st.divider()
            guess = topic_to_pillar.get(e["topic"])
            default_idx = PILLAR_NAMES.index(guess) if guess in PILLAR_NAMES else 0
            pillar = st.selectbox(
                "Pillar", PILLAR_NAMES, index=default_idx,
                key="pillar-%s-%d" % (fmt, i),
            )
            featured = True
            if fmt == "essay":
                featured = st.checkbox(
                    "Set as the featured essay", value=True,
                    key="feat-%s-%d" % (fmt, i))
            publish_disabled = not has_api_key() or (fmt == "case_study" and not (subject or "").strip())
            if st.button("Publish to site", key="promote-%s-%d" % (fmt, i),
                         type="primary", disabled=publish_disabled):
                from content_publisher import promote_to_site
                with st.spinner("Writing site data + article page..."):
                    try:
                        result = promote_to_site(
                            body=edited_body, fmt=fmt, pillar=pillar,
                            title=(title_override.strip() or None),
                            featured=featured if fmt == "essay" else None,
                            subject=(subject.strip() if subject else None))
                        promoted.add(heading)
                        where = "metis-website checkout" if result["is_site"] \
                            else "./site_output (no site checkout found)"
                        st.success(
                            "Promoted \"%s\".\nWrote to %s.\n- data: %s\n- page: %s"
                            % (result["entry"]["title"], where,
                               result["data_path"], result["article_path"]))
                        st.caption("Commit and push those files to metis-website "
                                   "to publish.")
                    except SystemExit as exc:
                        st.error(str(exc))
                    except Exception as exc:  # noqa: BLE001
                        st.error("Promote failed: %s" % exc)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
st.set_page_config(page_title="Metis Insights Agent", layout="wide")

st.title("Metis Insights Agent")
st.caption(
    "A multi-agent system that researches, plans, and drafts Insights content "
    "in the Metis Advisory Group voice. John reviews and promotes; the system "
    "does the rest.")

# ---- Sidebar --------------------------------------------------------------
with st.sidebar:
    st.header("System status")
    if has_api_key():
        st.success("GEMINI_API_KEY loaded")
    else:
        st.error("No GEMINI_API_KEY found. Live runs are disabled.")
        st.caption("Set it in .env (reuse the After Work key), then restart. "
                   "Read-only views still work.")

    if USING_PLACEHOLDER_REFERENCES:
        st.warning("Voice judge is scoring against placeholder site-copy "
                   "samples. Drop real essays into voice_reference/ (.txt or "
                   ".docx) to raise the bar.")

    st.divider()
    st.subheader("Publishing")
    auto_publish = st.checkbox(
        "Auto-publish passing drafts to the site",
        value=False, key="auto_publish",
        help="When on, any draft that PASSES the voice guardrails is written "
             "straight to the site (content/insights-data.json + article "
             "page). Drafts that fail always fall back to the docx for review. "
             "You still commit + push metis-website to make them live.",
        disabled=USING_PLACEHOLDER_REFERENCES)
    if USING_PLACEHOLDER_REFERENCES:
        st.caption("Auto-publish is locked until real voice samples are in "
                   "voice_reference/ -- do not auto-publish against placeholder "
                   "voice.")
    elif auto_publish:
        st.caption("On: passing drafts publish automatically. Review still "
                   "happens at the git commit step.")

    st.write("**Models**")
    st.write("- Agents / judge: `%s`" % (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"))
    st.write("- Writers: `%s`" % (os.getenv("GEMINI_WRITER_MODEL") or "gemini-pro-latest"))

    st.divider()
    st.header("The agents")
    st.markdown(
        "1. **Scout** - Google Search grounding, trailing-3-month business events\n"
        "2. **Strategist** - plans the cycle over pillar balance + cadence\n"
        "3. **Essay Writer** - long-form drafts through guardrails\n"
        "4. **Field Note Writer** - short drafts through guardrails\n"
        "5. **Case Study Writer** - named-subject analysis through guardrails\n"
        "6. **Analyst** - learns from read-through, adjusts pillars")

    st.divider()
    st.header("The five pillars")
    st.markdown("\n".join("- " + p for p in PILLAR_NAMES))

    st.divider()
    with st.expander("Case study idea bank"):
        st.caption(
            "Strategist falls back to this list when Scout finds no "
            "case-study subject on its own. Type any of these into "
            "\"Ask the agent\" (e.g. \"Write a case study about Pixar\") to "
            "request one directly.")
        from case_study_subjects import CASE_STUDY_SUBJECTS
        by_category = {}
        for entry in CASE_STUDY_SUBJECTS:
            by_category.setdefault(entry["category"], []).append(entry["subject"])
        for category, subjects in by_category.items():
            st.markdown("**%s** - %s" % (category, ", ".join(subjects)))


# ---- Main: ask the agent --------------------------------------------------
st.subheader("Ask the agent")

col_a, col_b = st.columns([3, 1])
with col_a:
    request = st.text_input(
        "Request",
        value="What should we publish this quarter?",
        label_visibility="collapsed",
        placeholder="e.g. What should we publish this quarter?")
with col_b:
    run = st.button("Run", type="primary", width="stretch", disabled=not has_api_key())

st.caption(
    "Examples: \"What should we publish this quarter?\" (full cycle plan), "
    "\"What's trending?\", \"Draft an essay about board AI governance\", "
    "\"Write a field note about return-to-office\", \"Write a case study "
    "about <company or leader>\".")

with st.expander("Note on live runs (cost + time)"):
    st.markdown(
        "A full cycle plan makes many live Gemini calls (Scout, then each "
        "writer's revise loop) and can take a few minutes with rate-limit "
        "pacing. It also draws on the prepaid API balance. For a fast, free "
        "demo, use the **This Cycle's Plan**, **Drafts**, and **Agent Trace** "
        "tabs below -- they render real output with no API calls.")

if run and request.strip():
    from agents.orchestrator import route

    intent, topic = route(request)
    st.info("Routed to intent: **%s**%s"
            % (intent, ("  |  topic: %s" % topic) if topic else ""))
    with st.spinner("Running the agent pipeline... this can take a few minutes for a full plan."):
        try:
            from agents.orchestrator import handle_request
            result = handle_request(
                request, auto_publish=st.session_state.get("auto_publish", False))
            st.success("Done. See the response below for where each draft went.")
            st.text_area("Response", value=result, height=360)
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error("Run failed: %s" % exc)

st.divider()

# ---- Tabs -----------------------------------------------------------------
tab_plan, tab_drafts, tab_trace = st.tabs(
    ["This Cycle's Plan", "Drafts", "Agent Trace"])

with tab_plan:
    calendar = load_calendar()
    if not calendar:
        st.info("No plan yet. Run \"What should we publish this quarter?\" to generate one.")
    else:
        planned = sum(1 for d in calendar if d.get("topic"))
        st.caption("%d item(s) planned, %d with a Scout-matched topic."
                   % (len(calendar), planned))
        rows = []
        for d in calendar:
            rows.append({
                "Slot": d.get("slot", ""),
                "Format": d.get("format", ""),
                "Pillar": d.get("pillar", ""),
                "Topic / Headline": d.get("source_headline") or d.get("topic") or "(open)",
            })
        st.dataframe(rows, width="stretch", hide_index=True)

with tab_drafts:
    st.caption(
        "Review a draft, pick its pillar, then promote it. Promoting writes "
        "the site data file and a standalone article page into your "
        "metis-website checkout; commit and push to publish.")
    entries = load_drafts(DRAFTS_DOC)
    left, mid, right = st.columns(3)
    with left:
        st.markdown("### Essays")
        render_draft_column(entries, "essay", "Essay")
    with mid:
        st.markdown("### Case studies")
        render_draft_column(entries, "case_study", "Case study")
    with right:
        st.markdown("### Field notes")
        render_draft_column(entries, "field_note", "Field note")

with tab_trace:
    trace = load_trace()
    if not trace:
        st.info("No trace yet. It fills in as the agents make decisions.")
    else:
        st.caption("Last %d decisions from logs/agent_trace.jsonl" % len(trace))
        rows = []
        for r in trace:
            scores = r.get("scores") or {}
            decision = r.get("decision") or {}
            rows.append({
                "Time (UTC)": (r.get("timestamp", "") or "")[:19].replace("T", " "),
                "Agent": r.get("agent", ""),
                "Action": r.get("action", ""),
                "Passed": decision.get("passed", ""),
                "Voice": scores.get("voice_score", ""),
                "Tone": scores.get("tone", ""),
                "Intent": decision.get("intent", ""),
            })
        st.dataframe(rows, width="stretch", hide_index=True)
