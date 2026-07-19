# -*- coding: utf-8 -*-
"""
Metis Content Studio -- one page, both agents.

A single Streamlit entry point that puts the two Metis apps behind one sidebar
nav:

  - Insights Engine   (this repo root: essays + field notes for the website)
  - Viral Agent       (viral-agents/: LinkedIn posts + Substack notes queue)

They are two separate applications that happen to share module names
(``agents``, ``guardrails``, ``gemini_client``, ...). Rather than merge their
code -- which would collide -- this launcher runs the selected app in-process
with three isolations applied on every rerun:

  1. cwd is switched to that app's folder, so its relative paths
     (memory/, logs/, its .docx drafts, voice_reference/) resolve.
  2. any module previously imported from either app folder is dropped from
     sys.modules, so `import agents.orchestrator` loads the *right* one.
  3. sys.path is pointed at the active app's folder first.

st.set_page_config is neutralized while the sub-app runs, because it is set
once here and may only be called once per session.

Run:  python -m streamlit run dashboard.py
"""

import os
import runpy
import sys

import streamlit as st

st.set_page_config(page_title="Metis Content Studio", layout="wide")

ROOT = os.path.dirname(os.path.abspath(__file__))
INSIGHTS_DIR = ROOT
VIRAL_DIR = os.path.join(ROOT, "viral-agents")
_THIS = os.path.abspath(__file__)


def _purge_app_modules():
    """Drop every already-imported module whose file lives under this repo
    (except this launcher), so the next app's identically-named modules load
    fresh instead of returning the other app's cached copy."""
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        f = os.path.abspath(f)
        if f == _THIS:
            continue
        if f.startswith(ROOT + os.sep):
            del sys.modules[name]


def _run_app(app_dir):
    """Run <app_dir>/app.py in-process, isolated (cwd, sys.path, modules)."""
    prev_cwd = os.getcwd()
    prev_config = st.set_page_config
    # Keep only clean, non-repo entries on the path, then put the active app
    # first so its modules win over the sibling app's same-named ones.
    for p in (INSIGHTS_DIR, VIRAL_DIR):
        while p in sys.path:
            sys.path.remove(p)
    sys.path.insert(0, app_dir)

    _purge_app_modules()
    os.chdir(app_dir)
    st.set_page_config = lambda *a, **k: None  # sub-app's call becomes a no-op
    try:
        runpy.run_path(os.path.join(app_dir, "app.py"), run_name="__streamlit_app__")
    finally:
        st.set_page_config = prev_config
        os.chdir(prev_cwd)


def insights_page():
    _run_app(INSIGHTS_DIR)


def viral_page():
    _run_app(VIRAL_DIR)


nav = st.navigation([
    st.Page(insights_page, title="Insights Engine", icon=":material/edit_note:"),
    st.Page(viral_page, title="Viral Agent", icon=":material/bolt:"),
])
nav.run()
