# -*- coding: utf-8 -*-
"""
Commit and push published site files, so promoting a draft can go all the way
live from the UI instead of stopping at "files written, someone push them."

The metis-website repo deploys to metisag.com through Vercel on every push to
main, so push == publish. That makes this the most consequential thing the app
does, and the rules below exist to keep it safe:

  * Only the files we just generated are staged, by explicit path. Never
    `git add -A` -- the site checkout may hold unrelated work in progress, and
    this must never sweep that into a public deploy.
  * Never prompt. GIT_TERMINAL_PROMPT=0 plus a timeout, so a missing credential
    fails fast with a readable message instead of hanging the dashboard on an
    invisible prompt.
  * Never raise. Every failure comes back as {"ok": False, "msg": <plain
     English>} so the UI can show it and the draft stays safely on disk.
  * A rejected push (someone else pushed first) is retried once behind
    `pull --rebase`, and a rebase that conflicts is aborted rather than
    guessed at.

Returns from every public function:
    {"ok": bool, "msg": str, "pushed": bool, "commit": str, "branch": str}
"""

import os
import subprocess

# Long enough for a slow push over a bad connection, short enough that the
# dashboard never looks frozen.
GIT_TIMEOUT_SECONDS = 120


def _run(args, cwd):
    """Run a git command without ever prompting. Returns
    (ok, stdout, stderr) and swallows the exceptions subprocess can raise."""
    env = dict(os.environ)
    # No interactive credential/passphrase prompts: fail instead of hanging.
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    try:
        proc = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return False, "", "git is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return False, "", ("git took longer than %d seconds and was stopped. "
                           "This usually means it was waiting for a login."
                           % GIT_TIMEOUT_SECONDS)
    except OSError as exc:
        return False, "", "Could not run git: %s" % exc
    return proc.returncode == 0, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def _fail(msg):
    return {"ok": False, "msg": msg, "pushed": False, "commit": "", "branch": ""}


def is_repo(site_dir):
    ok, out, _ = _run(["rev-parse", "--is-inside-work-tree"], site_dir)
    return ok and out.strip() == "true"


def current_branch(site_dir):
    ok, out, _ = _run(["rev-parse", "--abbrev-ref", "HEAD"], site_dir)
    return out.strip() if ok else ""


def has_remote(site_dir, name="origin"):
    ok, out, _ = _run(["remote"], site_dir)
    return ok and name in out.split()


def _relative_paths(site_dir, paths):
    """Turn absolute paths into repo-relative ones, skipping anything that is
    not actually inside the checkout (a guard against staging stray files)."""
    root = os.path.abspath(site_dir)
    rels = []
    for p in paths:
        ap = os.path.abspath(p)
        if not ap.startswith(root + os.sep):
            continue
        rels.append(os.path.relpath(ap, root).replace(os.sep, "/"))
    return rels


def publish_files(paths, message, site_dir, remote="origin", branch=None):
    """Stage the given files, commit them, and push.

    paths    -- absolute paths to the files just written (data file + article)
    message  -- commit message
    site_dir -- the metis-website checkout

    Safe to call when nothing changed: that returns ok with "nothing to
    publish" rather than an error, since a re-publish of identical content is
    not a failure."""
    if not site_dir or not os.path.isdir(site_dir):
        return _fail("The site folder was not found: %s" % site_dir)
    if not is_repo(site_dir):
        return _fail(
            "%s is not a git repository, so there is nothing to push to. The "
            "files were still written there." % site_dir)

    branch = branch or current_branch(site_dir)
    if not branch or branch == "HEAD":
        return _fail("The site repo is not on a branch (detached HEAD). "
                     "The files were written but not pushed.")

    rels = _relative_paths(site_dir, paths)
    if not rels:
        return _fail("None of the published files are inside the site repo, "
                     "so nothing was staged.")

    ok, _, err = _run(["add", "--"] + rels, site_dir)
    if not ok:
        return _fail("Could not stage the published files: %s" % err)

    # Anything actually staged? `diff --cached --quiet` exits 0 when clean.
    clean, _, _ = _run(["diff", "--cached", "--quiet"], site_dir)
    if clean:
        return {"ok": True, "pushed": False, "commit": "", "branch": branch,
                "msg": "Nothing to publish -- the site already has this exact "
                       "content."}

    ok, _, err = _run(["commit", "-m", message], site_dir)
    if not ok:
        return _fail("Could not commit the published files: %s" % err)

    ok, out, _ = _run(["rev-parse", "--short", "HEAD"], site_dir)
    commit = out.strip() if ok else ""

    if not has_remote(site_dir, remote):
        return {"ok": True, "pushed": False, "commit": commit, "branch": branch,
                "msg": "Committed locally (%s), but there is no '%s' remote to "
                       "push to." % (commit, remote)}

    pushed, _, push_err = _run(["push", remote, branch], site_dir)
    if not pushed:
        # Most likely someone pushed first. Rebase onto them and retry once.
        lowered = push_err.lower()
        if "rejected" in lowered or "fetch first" in lowered or "non-fast-forward" in lowered:
            rebased, _, rebase_err = _run(["pull", "--rebase", remote, branch], site_dir)
            if not rebased:
                _run(["rebase", "--abort"], site_dir)
                return {
                    "ok": False, "pushed": False, "commit": commit, "branch": branch,
                    "msg": ("The site has newer changes that clash with this "
                            "publish, so it was left committed locally (%s) and "
                            "not pushed. Ask Claude to sort out the conflict. "
                            "Details: %s" % (commit, rebase_err[:200])),
                }
            pushed, _, push_err = _run(["push", remote, branch], site_dir)

        if not pushed:
            hint = ""
            if "authentication" in push_err.lower() or "could not read" in push_err.lower():
                hint = (" This looks like a sign-in problem with GitHub rather "
                        "than anything wrong with the essay.")
            return {
                "ok": False, "pushed": False, "commit": commit, "branch": branch,
                "msg": ("Committed locally (%s) but the push failed, so it is "
                        "not live yet.%s Details: %s"
                        % (commit, hint, push_err[:200])),
            }

    return {
        "ok": True, "pushed": True, "commit": commit, "branch": branch,
        "msg": ("Published and pushed (%s on %s). The site rebuilds "
                "automatically and is usually live within a couple of minutes."
                % (commit, branch)),
    }
