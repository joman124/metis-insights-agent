# -*- coding: utf-8 -*-
"""
Tests for the unified Metis Content Studio (dashboard.py).

The studio runs two separate applications in one process, which is where the
sharp edges are. These tests drive the real thing with Streamlit's AppTest
harness (no browser, no Gemini) and lock in the two failures that actually
happened:

  1. _purge_app_modules() used to drop every module living under the repo. Both
     apps keep a virtualenv *inside* the repo, so that purged installed
     packages too -- giving the sub-app a second, context-less copy of
     Streamlit and segfaulting the process. test__is_app_module_* guards it.
  2. The viral app owns an st.navigation when run standalone. Nested in the
     studio, a second navigation is illegal, so the studio sets METIS_STUDIO=1
     and the viral app falls back to a sidebar page switch.

Run:  python test_studio.py
"""

import os

import dashboard

ROOT = os.path.dirname(os.path.abspath(__file__))


def test__is_app_module_excludes_installed_packages():
    """Installed packages must never be purged (see failure 1 above)."""
    for vendored in [
        os.path.join(ROOT, ".venv", "Lib", "site-packages", "streamlit", "__init__.py"),
        os.path.join(ROOT, "viral-agents", ".venv", "Lib", "site-packages", "pyarrow", "lib.py"),
        os.path.join(ROOT, "venv", "Lib", "site-packages", "google", "genai", "__init__.py"),
    ]:
        assert dashboard._is_app_module(vendored) is False, vendored
    print("[PASS] installed packages are never purged")


def test__is_app_module_includes_app_source():
    """The apps' own modules must be purged, so the right one loads per page."""
    for app_file in [
        os.path.join(ROOT, "guardrails.py"),
        os.path.join(ROOT, "agents", "essay_writer.py"),
        os.path.join(ROOT, "viral-agents", "guardrails.py"),
        os.path.join(ROOT, "viral-agents", "agents", "viral.py"),
    ]:
        assert dashboard._is_app_module(app_file) is True, app_file
    # Files outside the repo are irrelevant either way.
    assert dashboard._is_app_module(os.path.join("C:", os.sep, "Python", "os.py")) is False
    print("[PASS] app source modules are purged")


def test_studio_renders_viral_page_by_default():
    from streamlit.testing.v1 import AppTest

    at = AppTest(script_path="dashboard.py", default_timeout=120).run()
    assert not at.exception, at.exception
    titles = [t.value for t in at.title]
    assert "Metis: Viral Content Agents" in titles, titles
    # The nested viral app must use the sidebar page switch, not a second nav.
    labels = [r.label for r in at.radio]
    assert "Viral page" in labels, labels
    assert not [e.value for e in at.error if "navigation" in e.value.lower()]
    print("[PASS] studio opens on the viral page, nested without a second nav")


def test_studio_switches_to_viral_review_page():
    from streamlit.testing.v1 import AppTest

    at = AppTest(script_path="dashboard.py", default_timeout=120).run()
    assert not at.exception, at.exception
    at.radio[0].set_value("Review").run()
    assert not at.exception, at.exception
    titles = [t.value for t in at.title]
    assert "Review Queue" in titles, titles
    # The edit-learning panel is part of the queue page, so John can see what
    # his edits have taught the writers.
    labels = [e.label for e in at.expander]
    assert any("learned from your edits" in l for l in labels), labels
    print("[PASS] switching to Review renders the queue + learning panel")


def test_studio_renders_nested_essays_page():
    """The second studio page must render the essays app in-process.

    AppTest cannot click st.navigation's callable pages, so this calls the
    studio's page function the same way st.navigation would -- exercising
    _run_app(INSIGHTS_DIR), the module purge, and the cwd switch.
    """
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_string(
        "import dashboard\ndashboard.insights_page()\n",
        default_timeout=120).run()
    assert not at.exception, at.exception
    titles = [t.value for t in at.title]
    assert "Metis Insights Agent" in titles, titles
    subheaders = [s.value for s in at.subheader]
    assert "Ask the agent" in subheaders, subheaders
    print("[PASS] studio renders the nested essays page")


def test_essays_app_renders_standalone():
    """The essays app must still run on its own (streamlit run app.py)."""
    import sys
    from streamlit.testing.v1 import AppTest

    # Running the studio above left sys.path/sys.modules pointed at whichever
    # sub-app rendered last (that is _run_app's job). Restore what a plain
    # "streamlit run app.py" would see, so this test measures the app and not
    # the previous test's leftovers.
    dashboard._purge_app_modules()
    if ROOT in sys.path:
        sys.path.remove(ROOT)
    sys.path.insert(0, ROOT)

    at = AppTest(script_path="app.py", default_timeout=120).run()
    assert not at.exception, at.exception
    titles = [t.value for t in at.title]
    assert "Metis Insights Agent" in titles, titles
    print("[PASS] essays app renders standalone")


if __name__ == "__main__":
    test__is_app_module_excludes_installed_packages()
    test__is_app_module_includes_app_source()
    test_studio_renders_viral_page_by_default()
    test_studio_switches_to_viral_review_page()
    test_studio_renders_nested_essays_page()
    test_essays_app_renders_standalone()
    print("OK")
