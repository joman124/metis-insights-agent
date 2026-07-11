# -*- coding: utf-8 -*-
"""
LinkedIn publisher for the Metis agents: posts text (and, when rights-cleared,
native video) to the Metis LinkedIn page via the official Posts API.

The Metis page is an ORGANIZATION, so the actor URN in .env is
urn:li:organization:xxxx and the token needs the Community Management API
(w_organization_social) with the app as an admin of the page. The same code
also works for a personal (urn:li:person:xxxx) actor if you ever want that.

SAFETY: this posts publicly, which cannot be undone from code. It therefore
defaults to DRY RUN (LINKEDIN_DRY_RUN=true): it builds and logs the exact
payload but sends nothing. Set LINKEDIN_DRY_RUN=false in .env only once you
have a real token and actor URN and want posts to go live.

CONTENT RIGHTS: post_text (a share with commentary + a link back to the
original) is the safe default for reacting to someone else's viral clip.
post_video uploads a NATIVE video file to the Metis page and must only be used
for clips Metis owns or has a license/permission to repost -- re-uploading
someone else's copyrighted video risks takedowns and violates platform terms.
post_video therefore requires an explicit approve=True from a human caller.

Run:  python -m linkedin_publisher "some text to post"   # honors DRY RUN
"""

import os
import sys

from dotenv import load_dotenv

from observability import log_decision

load_dotenv(override=True)

POSTS_URL = "https://api.linkedin.com/rest/posts"
VIDEO_INIT_URL = "https://api.linkedin.com/rest/videos?action=initializeUpload"


def _dry_run_default() -> bool:
    """Dry run is ON unless .env explicitly says false. Fail safe: an unset
    or malformed value means we do NOT post."""
    return os.getenv("LINKEDIN_DRY_RUN", "true").strip().lower() != "false"


def _actor_urn(dry_run: bool) -> str:
    actor_urn = os.getenv("LINKEDIN_ACTOR_URN", "").strip()
    if actor_urn:
        return actor_urn
    if dry_run:
        return "urn:li:organization:DRY_RUN_PLACEHOLDER"
    raise SystemExit(
        "\n[LINKEDIN] LINKEDIN_ACTOR_URN is not set. Add it to .env "
        "(e.g. urn:li:organization:xxxx for the Metis page) before posting "
        "for real, or keep LINKEDIN_DRY_RUN=true."
    )


def _headers() -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "\n[LINKEDIN] LINKEDIN_ACCESS_TOKEN is not set but "
            "LINKEDIN_DRY_RUN=false. Add a real token to .env or set "
            "LINKEDIN_DRY_RUN=true."
        )
    api_version = os.getenv("LINKEDIN_API_VERSION", "202405").strip()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": api_version,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _text_payload(commentary: str, actor_urn: str, video_urn: str = None) -> dict:
    payload = {
        "author": actor_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if video_urn:
        payload["content"] = {"media": {"id": video_urn}}
    return payload


def post_text(commentary: str, dry_run: bool = None) -> dict:
    """Post plain text (optionally with links in the body) to the Metis page.
    This is the safe default for reacting to a third-party clip: link to the
    original in the commentary and credit the creator. Returns
    {"posted", "dry_run", "post_id", "actor"}."""
    if dry_run is None:
        dry_run = _dry_run_default()
    actor_urn = _actor_urn(dry_run)
    payload = _text_payload(commentary, actor_urn)

    if dry_run:
        log_decision(agent="linkedin_publisher", action="post_text",
                     inputs={"actor": actor_urn, "chars": len(commentary)},
                     decision={"dry_run": True, "payload_preview": commentary[:200]})
        print("[LINKEDIN] DRY RUN -- nothing was posted. Payload:")
        print(f"  author: {actor_urn}")
        print(f"  commentary ({len(commentary)} chars):\n{commentary}\n")
        return {"posted": False, "dry_run": True,
                "post_id": "dry-run-simulated", "actor": actor_urn}

    import requests
    try:
        resp = requests.post(POSTS_URL, headers=_headers(), json=payload, timeout=30)
    except requests.RequestException as exc:
        raise SystemExit(f"\n[LINKEDIN] Network error posting to LinkedIn: {exc}")
    return _finish(resp, actor_urn, len(commentary), "post_text")


def post_video(video_file: str, commentary: str, approve: bool = False,
               dry_run: bool = None) -> dict:
    """Upload a NATIVE video to the Metis page and post it with commentary.

    RIGHTS GATE: only for clips Metis owns or is licensed to repost. Requires
    approve=True from a human caller; without it this refuses, because
    re-uploading someone else's copyrighted video risks takedowns and breaks
    platform terms. For reacting to a third-party viral clip, use post_text
    with a link back to the original instead."""
    if not approve:
        raise SystemExit(
            "\n[LINKEDIN] post_video is gated. Native re-upload is only for "
            "clips Metis owns or is licensed to repost. Pass approve=True to "
            "confirm you have the rights, or use post_text with a link to the "
            "original creator to react safely."
        )
    if dry_run is None:
        dry_run = _dry_run_default()
    actor_urn = _actor_urn(dry_run)

    if dry_run:
        log_decision(agent="linkedin_publisher", action="post_video",
                     inputs={"actor": actor_urn, "video_file": video_file,
                             "chars": len(commentary)},
                     decision={"dry_run": True, "approved": True})
        print("[LINKEDIN] DRY RUN -- no video uploaded. Would upload:")
        print(f"  author: {actor_urn}\n  file: {video_file}\n"
              f"  commentary:\n{commentary}\n")
        return {"posted": False, "dry_run": True,
                "post_id": "dry-run-simulated", "actor": actor_urn}

    if not os.path.exists(video_file):
        raise SystemExit(f"\n[LINKEDIN] Video file not found: {video_file}")

    import requests
    headers = _headers()
    # 1) initialize the upload to get a video URN + upload URL
    init_body = {"initializeUploadRequest": {
        "owner": actor_urn,
        "fileSizeBytes": os.path.getsize(video_file),
        "uploadCaptions": False,
        "uploadThumbnail": False,
    }}
    try:
        init = requests.post(VIDEO_INIT_URL, headers=headers, json=init_body, timeout=30)
    except requests.RequestException as exc:
        raise SystemExit(f"\n[LINKEDIN] Network error initializing video upload: {exc}")
    if init.status_code not in (200, 201):
        raise SystemExit(
            f"\n[LINKEDIN] Video init failed HTTP {init.status_code}: {init.text[:300]}"
        )
    value = init.json().get("value", {})
    video_urn = value.get("video")
    instructions = value.get("uploadInstructions", [])
    if not video_urn or not instructions:
        raise SystemExit("\n[LINKEDIN] Video init response missing upload details.")

    # 2) PUT the bytes to each returned upload URL (single-part for small files)
    with open(video_file, "rb") as fh:
        data = fh.read()
    try:
        put = requests.put(instructions[0]["uploadUrl"], data=data, timeout=120)
    except requests.RequestException as exc:
        raise SystemExit(f"\n[LINKEDIN] Network error uploading video bytes: {exc}")
    if put.status_code not in (200, 201):
        raise SystemExit(
            f"\n[LINKEDIN] Video upload failed HTTP {put.status_code}: {put.text[:300]}"
        )

    # 3) create the post referencing the video URN
    payload = _text_payload(commentary, actor_urn, video_urn=video_urn)
    try:
        resp = requests.post(POSTS_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        raise SystemExit(f"\n[LINKEDIN] Network error creating video post: {exc}")
    return _finish(resp, actor_urn, len(commentary), "post_video")


def _finish(resp, actor_urn: str, chars: int, action: str) -> dict:
    """Shared response handling for the create-post call."""
    if resp.status_code in (401, 403):
        raise SystemExit(
            "\n[LINKEDIN] LinkedIn rejected the request (auth/scope). Check that "
            "your token is valid and has w_organization_social (for the page) "
            "with the app as a page admin, and that the actor URN matches. "
            f"HTTP {resp.status_code}: {resp.text[:300]}"
        )
    if resp.status_code not in (200, 201):
        raise SystemExit(
            f"\n[LINKEDIN] Unexpected response HTTP {resp.status_code}: {resp.text[:300]}"
        )
    post_id = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")
    log_decision(agent="linkedin_publisher", action=action,
                 inputs={"actor": actor_urn, "chars": chars},
                 decision={"dry_run": False, "post_id": post_id})
    return {"posted": True, "dry_run": False, "post_id": post_id, "actor": actor_urn}


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "Test post from the Metis viral agent."
    result = post_text(text)
    print(f"\n[LINKEDIN] {result}")
