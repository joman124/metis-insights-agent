# -*- coding: utf-8 -*-
"""
Tests for site_git.publish_files -- the step that puts an essay on the live
site, so the safety properties matter more than the happy path.

Uses real git against a local bare repo standing in for GitHub: no network, no
credentials, nothing touches metis-website.

Run:  python test_site_git.py
"""

import os
import shutil
import subprocess
import tempfile

import site_git


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True,
                   capture_output=True, text=True)


def _make_origin_and_clone():
    """A bare 'remote' plus a working clone, both in a temp dir."""
    tmp = tempfile.mkdtemp()
    origin = os.path.join(tmp, "origin.git")
    work = os.path.join(tmp, "work")
    _git(["init", "--bare", "--initial-branch=main", origin], tmp)
    _git(["clone", origin, work], tmp)
    _git(["config", "user.email", "test@example.com"], work)
    _git(["config", "user.name", "Test"], work)
    # A first commit so the branch exists on the remote.
    with open(os.path.join(work, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("<h1>site</h1>")
    _git(["add", "index.html"], work)
    _git(["commit", "-m", "initial"], work)
    _git(["push", "origin", "main"], work)
    return tmp, origin, work


def _write_published(work, slug="a-published-essay"):
    """Mimic what content_publisher writes: a data file and an article page."""
    data = os.path.join(work, "content", "insights-data.json")
    article = os.path.join(work, "insights", slug + ".html")
    os.makedirs(os.path.dirname(data), exist_ok=True)
    os.makedirs(os.path.dirname(article), exist_ok=True)
    with open(data, "w", encoding="utf-8") as fh:
        fh.write('{"featured": {"slug": "%s"}}' % slug)
    with open(article, "w", encoding="utf-8") as fh:
        fh.write("<article>%s</article>" % slug)
    return [data, article]


def _remote_files(origin):
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", "main"],
                         cwd=origin, capture_output=True, text=True, check=True)
    return set(out.stdout.split())


def test_publishes_and_pushes():
    tmp, origin, work = _make_origin_and_clone()
    try:
        paths = _write_published(work)
        res = site_git.publish_files(paths, "Publish: a published essay", work)
        assert res["ok"], res["msg"]
        assert res["pushed"] is True, res
        assert res["commit"], res
        files = _remote_files(origin)
        assert "content/insights-data.json" in files, files
        assert "insights/a-published-essay.html" in files, files
        print("[PASS] publishes and pushes to the remote")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_never_sweeps_up_unrelated_work():
    """The safety property that matters most: a half-finished edit sitting in
    the site checkout must not ride along into a public deploy."""
    tmp, origin, work = _make_origin_and_clone()
    try:
        secret = os.path.join(work, "unfinished-redesign.html")
        with open(secret, "w", encoding="utf-8") as fh:
            fh.write("<h1>DO NOT SHIP</h1>")
        # Also modify a tracked file, the other way work-in-progress shows up.
        with open(os.path.join(work, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("<h1>half-edited</h1>")

        paths = _write_published(work)
        res = site_git.publish_files(paths, "Publish: a published essay", work)
        assert res["ok"] and res["pushed"], res["msg"]

        files = _remote_files(origin)
        assert "unfinished-redesign.html" not in files, files
        pushed_index = subprocess.run(
            ["git", "show", "main:index.html"], cwd=origin,
            capture_output=True, text=True, check=True).stdout
        assert "half-edited" not in pushed_index, pushed_index
        print("[PASS] unrelated work in progress is never pushed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_retries_behind_a_newer_remote_commit():
    """Someone (or another machine) pushed first -- rebase and still land it."""
    tmp, origin, work = _make_origin_and_clone()
    try:
        other = os.path.join(tmp, "other")
        _git(["clone", origin, other], tmp)
        _git(["config", "user.email", "other@example.com"], other)
        _git(["config", "user.name", "Other"], other)
        with open(os.path.join(other, "about.html"), "w", encoding="utf-8") as fh:
            fh.write("<h1>about</h1>")
        _git(["add", "about.html"], other)
        _git(["commit", "-m", "add about"], other)
        _git(["push", "origin", "main"], other)

        paths = _write_published(work)
        res = site_git.publish_files(paths, "Publish: a published essay", work)
        assert res["ok"] and res["pushed"], res["msg"]
        files = _remote_files(origin)
        # Both the other person's work and ours survive.
        assert "about.html" in files, files
        assert "insights/a-published-essay.html" in files, files
        print("[PASS] rebases onto a newer remote commit and still publishes")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_republish_of_identical_content_is_not_an_error():
    tmp, origin, work = _make_origin_and_clone()
    try:
        paths = _write_published(work)
        site_git.publish_files(paths, "Publish: once", work)
        res = site_git.publish_files(paths, "Publish: again", work)
        assert res["ok"], res
        assert res["pushed"] is False, res
        assert "nothing to publish" in res["msg"].lower(), res["msg"]
        print("[PASS] re-publishing identical content reports cleanly")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_reports_plainly_when_not_a_repo():
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "content"))
        f = os.path.join(tmp, "content", "insights-data.json")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("{}")
        res = site_git.publish_files([f], "Publish", tmp)
        assert res["ok"] is False
        assert "not a git repository" in res["msg"], res["msg"]
        # The message must reassure that the writing still happened.
        assert "still written" in res["msg"], res["msg"]
        print("[PASS] a non-repo folder fails safely and explains itself")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_folder_fails_safely():
    res = site_git.publish_files([], "Publish", os.path.join(tempfile.gettempdir(), "no-such-site-dir"))
    assert res["ok"] is False
    assert "not found" in res["msg"].lower(), res["msg"]
    print("[PASS] a missing site folder fails safely")


if __name__ == "__main__":
    test_publishes_and_pushes()
    test_never_sweeps_up_unrelated_work()
    test_retries_behind_a_newer_remote_commit()
    test_republish_of_identical_content_is_not_an_error()
    test_reports_plainly_when_not_a_repo()
    test_missing_folder_fails_safely()
    print("OK")
