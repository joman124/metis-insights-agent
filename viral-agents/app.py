# -*- coding: utf-8 -*-
"""
Streamlit UI for the Metis viral content agents.

The front door for running the agents and reviewing what they produce. It wraps
the Orchestrator (natural-language requests), the fast-reaction cycle, the video
curator, and the approval queue, and renders the system's real state -- queued
drafts, saved documents, per-pillar performance, and the decision trace --
without needing an API call for the read-only views.

Run:  streamlit run app.py

Pure ASCII on purpose (see the repo's coding rules).
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

TRACE_PATH = os.path.join("logs", "agent_trace.jsonl")
LINKEDIN_DOC = "Metis LinkedIn Posts.docx"
NOTE_DOC = "Metis Substack Notes.docx"
VIDEO_DOC = "Metis Video Queue.docx"


# --------------------------------------------------------------------------
# Read-only helpers (no Gemini calls)
# --------------------------------------------------------------------------
def has_api_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def load_drafts(doc_path):
    """Parse a generated .docx into [{heading, body}], grouping on Heading 2."""
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


def render_drafts(doc_path):
    drafts = load_drafts(doc_path)
    if not drafts:
        st.info("No drafts yet in %s." % doc_path)
        return
    st.caption("%d draft(s) in %s" % (len(drafts), doc_path))
    for e in reversed(drafts):
        label = e["heading"][:90] + ("..." if len(e["heading"]) > 90 else "")
        with st.expander(label):
            st.write(e["body"])


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
st.set_page_config(page_title="Metis - Viral Content Agents", layout="wide")

st.title("Metis: Viral Content Agents")
st.caption(
    "Fast, on-brand reactions to hot topics for the Metis LinkedIn page and "
    "Substack Notes. Everything is drafted through the voice + engagement "
    "guardrails and waits in the approval queue -- nothing posts until you say so."
)

with st.sidebar:
    st.header("System status")
    if has_api_key():
        st.success("GEMINI_API_KEY loaded")
    else:
        st.error("No GEMINI_API_KEY found. Live runs are disabled.")
        st.caption("Set it in .env, then restart. Read-only views still work.")

    st.write("**Models**")
    st.write("- Scout / video / judge: `%s`" % (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"))
    st.write("- Writer: `%s`" % (os.getenv("GEMINI_WRITER_MODEL") or "gemini-2.5-pro"))

    st.divider()
    st.header("The agents")
    st.markdown(
        "1. **Scout** - Google Search grounding, finds hot topics\n"
        "2. **Viral** - short LinkedIn post + Substack Note, best-of-N\n"
        "3. **Video Curator** - reshares viral AI clips with Metis commentary"
    )
    # Live/dry-run switch. Seed from .env once, then this toggle owns it for the
    # session. We re-apply to os.environ on every rerun because load_dotenv(
    # override=True) at the top would otherwise reset it to the .env value, and
    # the publisher reads LINKEDIN_DRY_RUN from the environment at post time.
    if "linkedin_live" not in st.session_state:
        st.session_state.linkedin_live = (
            os.getenv("LINKEDIN_DRY_RUN", "true").strip().lower() == "false"
        )
    # Bound by key (no value=): the widget's state lives in session_state under
    # "linkedin_live", so flipping it either way sticks.
    st.toggle(
        "Post to LinkedIn for real",
        key="linkedin_live",
        help=(
            "OFF = DRY RUN: the agent builds and logs the exact post but sends "
            "nothing (the safe default). ON = approving an item posts it live to "
            "the Metis page. Needs a LinkedIn token in .env -- see "
            "LINKEDIN_SETUP.md."
        ),
    )
    os.environ["LINKEDIN_DRY_RUN"] = (
        "false" if st.session_state.linkedin_live else "true"
    )
    if st.session_state.linkedin_live:
        if os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip():
            st.warning("LIVE: approving an item will post it to the Metis page.")
        else:
            st.error(
                "LIVE is on but no LINKEDIN_ACCESS_TOKEN in .env -- posting will "
                "fail. See LINKEDIN_SETUP.md, or switch the toggle off."
            )
    else:
        st.caption("DRY RUN: nothing posts. Flip the toggle on to go live.")
    st.caption("This toggle lasts for the session; .env sets the startup default.")
    st.divider()
    st.caption("Metis Advisory Group")


# ---- Ask the agent --------------------------------------------------------
st.subheader("Ask the agent")
col_a, col_b = st.columns([3, 1])
with col_a:
    request = st.text_input(
        "Request", value="What's trending?", label_visibility="collapsed",
        placeholder="e.g. go viral about the new AI model release",
    )
with col_b:
    run = st.button("Run", type="primary", width="stretch", disabled=not has_api_key())
st.caption(
    "Examples: \"Go viral about X\", \"Post a viral video about Y\", "
    "\"What's trending?\""
)

if run and request.strip():
    from agents.orchestrator import route, handle_request
    intent, topic = route(request)
    st.info("Routed to intent: **%s**%s"
            % (intent, ("  |  topic: %s" % topic) if topic else ""))
    with st.spinner("Running the agent pipeline..."):
        try:
            st.text_area("Response", value=handle_request(request), height=340)
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error("Run failed: %s" % exc)

st.divider()

# ---- Fast reaction --------------------------------------------------------
st.subheader("Fast reaction")
st.caption(
    "Draft a hot-topic reaction (best-of-N, voice + engagement scored) into the "
    "Approval Queue below. Nothing posts until you approve it."
)
rc_a, rc_b, rc_c = st.columns([3, 1, 1])
with rc_a:
    hot = st.text_input(
        "Hot topic", label_visibility="collapsed",
        placeholder="e.g. most AI pilots never reach production",
    )
with rc_b:
    draft_btn = st.button("Draft + queue", width="stretch", disabled=not has_api_key())
with rc_c:
    cycle_btn = st.button("Auto: find + queue", width="stretch", disabled=not has_api_key())

if draft_btn and hot.strip():
    with st.spinner("Drafting best-of reaction and queuing..."):
        try:
            import run_cycle
            res = run_cycle.queue_topic(hot.strip())
            note = "" if res.get("safe", True) else " (flagged sensitive -- review carefully)"
            st.success("Queued %d item(s)%s. See the Approval Queue tab."
                       % (len(res["queued"]), note))
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error("Failed: %s" % exc)

if cycle_btn:
    with st.spinner("Scouting, ranking, drafting the best one..."):
        try:
            import run_cycle
            res = run_cycle.run()
            if res.get("queued"):
                st.success("Reacted to '%s' and queued %d item(s)."
                           % (res.get("topic", ""), len(res["queued"])))
            else:
                st.warning("Nothing queued: %s" % res.get("reason", "(no topics)"))
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error("Failed: %s" % exc)

# ---- Video reaction -------------------------------------------------------
st.subheader("Video reaction")
st.caption(
    "Find a viral AI video and draft Metis commentary. The source link goes in "
    "the first comment (better reach); native re-upload stays disabled for "
    "copyright reasons."
)
vc_a, vc_b = st.columns([3, 1])
with vc_a:
    vfocus = st.text_input(
        "Video focus", label_visibility="collapsed",
        placeholder="e.g. AI agents in the enterprise",
    )
with vc_b:
    video_btn = st.button("Find + draft video", width="stretch", disabled=not has_api_key())

if video_btn:
    with st.spinner("Finding a viral clip and drafting commentary..."):
        try:
            from agents.video_curator import curate
            pkg = curate(vfocus.strip() or None)
            v = pkg["video"]
            st.success("Selected: %s -- %s (%s)"
                       % (v.get("title"), v.get("creator"), v.get("platform")))
            st.write("**Source:** %s" % v.get("source_url"))
            st.text_area("LinkedIn post body", value=pkg["caption"], height=180)
            st.caption("First comment: %s" % pkg["credit"])
        except SystemExit as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error("Failed: %s" % exc)

st.divider()

# ---- Tabs -----------------------------------------------------------------
tab_queue, tab_drafts, tab_perf, tab_trace = st.tabs(
    ["Approval Queue", "Drafts", "Performance", "Agent Trace"]
)

with tab_queue:
    import posts_ledger
    import review
    queued = posts_ledger.by_status("queued")
    st.caption(
        "Reactions waiting for approval. Edit the text right here, then approve: "
        "**Approve + post** publishes exactly what is in the box (honors "
        "LINKEDIN_DRY_RUN), so you can autopost everything from the dashboard. "
        "A Substack Note is marked done for you to paste in. %d item(s) queued."
        % len(queued)
    )
    if not queued:
        st.info("Nothing queued. Use 'Fast reaction' or 'Video reaction' above.")
    for r in reversed(queued):
        # expanded=True so an item stays open while you work it: clicking any
        # button triggers a Streamlit rerun, and a collapsed expander would hide
        # the edit box (and any save confirmation) right after you click Save,
        # which reads as "editing did nothing."
        with st.expander(("[%s] %s" % (r["platform"], r["topic"]))[:100],
                         expanded=True):
            edited = st.text_area(
                "Edit before posting",
                value=r.get("text") or "",
                height=220,
                key="edit-%s" % r["id"],
            )
            st.caption("%d characters" % len(edited))
            with st.expander("Copy for manual posting"):
                st.caption(
                    "Use the copy icon at the top-right of the box below, then "
                    "paste it into LinkedIn (or Substack) yourself. Handy while "
                    "auto-posting is off or the API is still pending."
                )
                st.code(edited or "", language=None)
            sv, ap, rj = st.columns(3)
            with sv:
                if st.button("Save edits", key="sv-%s" % r["id"], width="stretch"):
                    # No st.rerun() here: the button click already reran the
                    # script with the edited value committed, edit_item has
                    # written it to the ledger, and skipping a second rerun lets
                    # the confirmation below stay on screen.
                    res = review.edit_item(r["id"], edited)
                    (st.success if res["ok"] else st.error)(res["msg"])
            with ap:
                if st.button("Approve + post", key="ap-%s" % r["id"], width="stretch"):
                    # Save whatever is in the box first, so we post the edited
                    # version, then publish.
                    saved = review.edit_item(r["id"], edited)
                    if not saved["ok"]:
                        st.error(saved["msg"])
                    else:
                        try:
                            result = review.approve_item(r["id"])
                        except SystemExit as exc:
                            # publisher raises this with a plain-English message
                            # (e.g. no token while live). Show it, do not crash.
                            result = {"ok": False, "msg": str(exc)}
                        except Exception as exc:  # noqa: BLE001
                            result = {"ok": False, "msg": "Post failed: %s" % exc}
                        (st.success if result["ok"] else st.error)(result["msg"])
                        if result["ok"]:
                            st.rerun()
            with rj:
                if st.button("Reject", key="rj-%s" % r["id"], width="stretch"):
                    review.reject_item(r["id"])
                    st.rerun()

with tab_drafts:
    st.caption("Everything the agents have saved for review.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### LinkedIn Posts")
        render_drafts(LINKEDIN_DOC)
    with c2:
        st.markdown("### Substack Notes")
        render_drafts(NOTE_DOC)
    with c3:
        st.markdown("### Video Queue")
        render_drafts(VIDEO_DOC)

with tab_perf:
    import posts_ledger
    import analytics
    import linkedin_metrics
    st.caption(
        "What actually landed. Sync pulls real reactions/comments from LinkedIn "
        "into the ledger; the multipliers nudge which pillars the cycle favors."
    )
    if st.button("Sync LinkedIn metrics", disabled=not has_api_key()):
        with st.spinner("Pulling engagement from LinkedIn..."):
            try:
                summary = linkedin_metrics.sync_ledger()
                st.success("Synced %d of %d posted item(s). %s"
                           % (summary.get("updated", 0), summary.get("candidates", 0),
                              summary.get("note", "")))
            except Exception as exc:  # noqa: BLE001
                st.error("Sync failed: %s" % exc)
    perf = analytics.summarize()
    mult = analytics.performance_multipliers()
    st.write("**Posts on record:** %d" % len(posts_ledger.by_status("posted")))
    if not perf:
        st.info("No posted content yet. Approve some reactions, then sync metrics.")
    else:
        rows = []
        for pillar, s in perf.items():
            rows.append({
                "Pillar": pillar,
                "Posts": s["posts"],
                "With metrics": s["with_metrics"],
                "Avg engagement": s["avg_engagement"],
                "Ranking multiplier": mult.get(pillar, 1.0),
            })
        st.dataframe(rows, width="stretch", hide_index=True)

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
                "Engagement": scores.get("engagement_score", ""),
                "Tone": scores.get("tone", ""),
                "Intent": decision.get("intent", ""),
            })
        # Coerce every cell to a string: the "Passed" column mixes booleans
        # with "" (missing), which pyarrow cannot serialize into one column and
        # would crash st.dataframe. Strings render the same and always convert.
        rows = [{k: ("" if v == "" else str(v)) for k, v in row.items()} for row in rows]
        st.dataframe(rows, width="stretch", hide_index=True)
