# Turning on LinkedIn posting (Metis page)

This is a one-time setup. When you finish, the Viral and Video agents can post
to the **Metis company page** automatically. You do not need to write any code.

Posting to a **company page** is a bit more involved than posting as yourself,
because LinkedIn gates page-posting behind an app review. Plan for the review to
take anywhere from a day to about a week.

Until you finish this, the agents still work -- they just stay in **dry run**
(they draft and save posts but do not publish). That is the safe default.

---

## Step 1 - Create a LinkedIn app linked to the Metis page

1. Go to https://developer.linkedin.com/ and click **Create app**.
2. For the associated page, choose the **Metis Advisory Group** company page.
   You must be an **admin** of that page.
3. Open your app, go to the **Auth** tab. Copy the **Client ID** and
   **Client Secret** -- you will paste them into `.env` in Step 3.
4. On the **Auth** tab, under **Authorized redirect URLs**, add exactly:
   ```
   http://localhost:8000/callback
   ```
   Save.

## Step 2 - Request the permissions

On the app's **Products** tab, request:
1. **"Sign In with LinkedIn using OpenID Connect"** (instant) -- gives
   `openid` + `profile`.
2. **"Community Management API"** -- gives `w_organization_social` (posting to
   the page) and `rw_organization_admin` (so the helper can find the page's id
   for you). **This one requires LinkedIn to review your app.** Fill in their
   form describing that you will post the company's own content. Wait for
   approval before continuing to Step 4.

## Step 3 - Put your app credentials in .env

1. If you have not already, copy `.env.example` to `.env`.
2. Fill in:
   ```
   LINKEDIN_CLIENT_ID=...your client id...
   LINKEDIN_CLIENT_SECRET=...your client secret...
   LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
   ```

## Step 4 - Get your token (after the API is approved)

Run:
```
python linkedin_auth.py
```
It will:
1. Open a LinkedIn page in your browser -- click **Allow**.
2. Catch the response automatically and print lines like:
   ```
   LINKEDIN_ACCESS_TOKEN=AQV...long string...
   LINKEDIN_ACTOR_URN=urn:li:organization:12345678
   ```
   If you admin more than one page, it lists them all -- pick the Metis one.
3. Copy the token line and the correct `LINKEDIN_ACTOR_URN` line into `.env`.

## Step 5 - Test in dry run, then go live

1. Leave `LINKEDIN_DRY_RUN=true` and run:
   ```
   python -m agents.orchestrator "go viral about a topic Metis cares about"
   ```
   Check the draft. Nothing is posted yet.
2. When happy, set `LINKEDIN_DRY_RUN=false` and run again. **Watch the first
   real post** before letting it run unattended.

---

### Notes
- **Video:** by default the video agent posts your commentary with a **link**
  to the original clip -- safe and needs no extra rights. Re-uploading a clip as
  native video is deliberately blocked (`post_video`, in `linkedin_publisher.py`)
  unless you pass `approve=True`, and you should only do that for clips Metis
  owns or has licensed. Re-uploading someone else's video can get the post (or
  the page) taken down.
- The access token lasts about 60 days. Re-run `python linkedin_auth.py` to
  refresh it when posting starts failing with an auth error.
- Substack Notes are never auto-posted (no API); they are saved to
  `Metis Substack Notes.docx` for you to paste in.
- Never commit `.env` -- it holds your secret. It is already gitignored.
