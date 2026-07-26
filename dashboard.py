# -*- coding: utf-8 -*-
"""
Metis Content Studio -- one page, both agents.

A single Streamlit entry point that puts the two Metis apps behind one sidebar
nav (dark theme via .streamlit/config.toml):

  - Viral Content         (viral-agents/: LinkedIn posts + Substack notes queue)
  - Essays & Field Notes  (this repo root: essays + field notes for the website)

METIS_STUDIO=1 is set for the sub-apps so the viral app knows it is running
inside this studio and must not start its own st.navigation (only one
navigation is allowed per session; it falls back to a sidebar page switch).

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

# Tell the sub-apps they are running inside the studio (see module docstring).
os.environ["METIS_STUDIO"] = "1"

ROOT = os.path.dirname(os.path.abspath(__file__))
INSIGHTS_DIR = ROOT
VIRAL_DIR = os.path.join(ROOT, "viral-agents")
_THIS = os.path.abspath(__file__)


# Directory names that hold installed third-party packages. Both apps keep a
# virtualenv *inside* the repo (.venv/, venv/), so "lives under this repo" is
# not enough to identify an app module -- see _is_app_module.
_VENDOR_PARTS = (".venv", "venv", "site-packages", "dist-packages")


def _is_app_module(path):
    """True only for the apps' own source files.

    Must exclude anything from an in-repo virtualenv. Purging installed
    packages (streamlit itself, and its C extensions) and re-importing them
    mid-render gives the sub-app a second, context-less copy of Streamlit and
    segfaults the process -- that is what this guard prevents.
    """
    if not path.startswith(ROOT + os.sep):
        return False
    parts = set(path[len(ROOT) + 1:].split(os.sep))
    return not (parts & set(_VENDOR_PARTS))


def _purge_app_modules():
    """Drop every already-imported module that belongs to either app (but not
    this launcher, and never an installed package), so the next app's
    identically-named modules load fresh instead of returning the other app's
    cached copy."""
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        f = os.path.abspath(f)
        if f == _THIS:
            continue
        if _is_app_module(f):
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
    st.Page(viral_page, title="Viral Content", icon=":material/bolt:",
            default=True),
    st.Page(insights_page, title="Essays & Field Notes",
            icon=":material/edit_note:"),
])
nav.run()
