# corydegarmo — personal site with an interview agent

A single-page parallax site for Cory DeGarmo. The centerpiece is an embedded
agent that answers hiring-manager questions in his voice, grounded strictly in
`backend/kb/KNOWLEDGE_BASE.md`.

- **Backend:** Django 5 + Django REST Framework, PostgreSQL, Anthropic Claude
  (`claude-sonnet-5`).
- **Frontend:** React 19 + TypeScript (Vite), a design system ported from a
  Claude Design export, self-hosted webfonts.
- **Deploy:** Render — one web service, one static site, one Postgres.

```
backend/
  config/          Django project (settings, urls, wsgi, asgi)
  agent/           The interview endpoint, model, throttle, tests
  kb/              KNOWLEDGE_BASE.md — the single source of truth
frontend/
  src/ds/          The design system, ported to TSX (core, site, chat, Icon)
  src/styles/      tokens.css + fonts.css, generated from the design export
  src/components/  InterviewAgent - the one stateful piece
  src/content.ts   Site copy, all of it copied from the knowledge base
design/            The Claude Design export and its extractor
render.yaml        Blueprint for both services and the database
```

## The knowledge base is the source of truth

`backend/kb/KNOWLEDGE_BASE.md` grounds the agent, and `frontend/src/content.ts`
copies its facts into the static sections. **When one changes, change the other
in the same commit** — otherwise the page and the agent will contradict each
other, which is the one failure mode that matters here.

The backend reads the file once at startup and holds it in memory. A missing or
empty file stops the process rather than letting the agent answer ungrounded.

## Running it locally

Two terminals. Postgres must be running.

**Terminal 1 — API on :8000**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
createdb secondchair          # if it doesn't exist yet
cd backend
python manage.py migrate
python manage.py runserver 8000
```

**Terminal 2 — site on :5173**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend calls `VITE_API_BASE_URL`, which
defaults to `http://localhost:8000`; override it in `frontend/.env.local`.

To see the admin and the questions people have asked:

```bash
cd backend && python manage.py createsuperuser
# then http://localhost:8000/admin/
```

### Environment

All backend variables are read from a single `.env` at the repository root.
`.env.example` documents every one of them. `ANTHROPIC_API_KEY` is the only
value with no working default — without it the endpoint returns 503 pointing
the visitor at the contact email rather than failing silently.

Create that key **inside a workspace** in the Anthropic Console. An
account-level key authenticates but is rejected by `/v1/messages`:

```
400 invalid_request_error - This API key is not scoped to a workspace, so this
request must include the anthropic-workspace-id header
```

If you must use an account-level key, set `ANTHROPIC_WORKSPACE_ID` as well and
the client sends that header. The id is in the Console URL while viewing the
workspace: `.../settings/workspaces/wrkspc_XXXXXXXX`.

The dev server runs with `--noreload`, so it does not pick up `.env` changes on
its own. Restart it after editing a credential.

## Checks

```bash
cd backend && python manage.py check     # Django system checks
cd backend && python -m pytest           # 33 tests, no network calls
cd frontend && npm run build             # tsc --strict, then vite build
```

The test suite mocks both the Anthropic client and ElevenLabs; nothing in
it spends money or touches the network.

## The API

`POST /api/interview/`

```json
{
  "question": "What have you actually shipped with AI?",
  "history": [{ "role": "user", "content": "..." }],
  "session_id": "optional-uuid-from-a-previous-response"
}
```

```json
{
  "answer": "...",
  "session_id": "uuid",
  "log_id": 42,
  "speech_available": true
}
```

- Questions over 500 characters return `400`.
- History is capped at the last 12 turns server-side, and any leading
  assistant turns are dropped so the payload is valid for the Messages API.
- 20 requests per IP per hour. The 21st returns `429` with a message naming
  Cory's email. Counts live in the database cache so every gunicorn worker
  shares one tally.
- If Claude is unreachable or declines, the endpoint returns `503` with the
  same "email Cory" message. It never returns a 500 to a visitor.
- Every successful answer is written to `InterviewLog` with a salted SHA-256
  hash of the caller's IP. Raw addresses are never stored.

`GET /api/interview/<log_id>/speech/` returns `audio/mpeg` of an answer the
agent already gave.

- It takes an **answer id, not text**. An endpoint that speaks arbitrary
  strings is a free text-to-speech service billed to Cory; this one can only
  voice sentences the agent itself produced.
- 60 plays per IP per hour, and audio is cached for a week, so replaying an
  answer never bills twice.
- Returns `503` when `ELEVENLABS_API_KEY` or `ELEVENLABS_VOICE_ID` is unset.
  The frontend reads `speech_available` from the interview response and hides
  the play button entirely rather than offering a control that fails.

`GET /healthz/` returns `{"status": "ok"}` for Render's health check.

## Voice

Visitors can ask by voice and hear answers back. The two halves work
differently on purpose.

**Asking** uses the browser's own Web Speech API. No key, no cost, nothing
sent to our server: Chrome and Edge transcribe through Google, Safari through
Apple. Firefox has no implementation, so the microphone button does not
appear there and the textarea works as usual. The transcript lands in the box
for review rather than sending itself, because recognition makes mistakes and
a garbled question wastes a model call.

**Answering aloud** uses ElevenLabs through the endpoint above, one answer at
a time, only when the visitor presses Listen. To turn it on:

```bash
cd backend
python manage.py list_voices          # needs ELEVENLABS_API_KEY set
# put the chosen id in .env as ELEVENLABS_VOICE_ID, then restart
```

Both variables are optional. With neither set, the site behaves exactly as it
did before voice existed.

## Design

The visual system comes from a Claude Design export, kept in `design/` as the
source of truth. `design/extract.py` unpacks it:

```bash
python3 design/extract.py "design/Cory DeGarmo.dc.html"
```

That regenerates `frontend/src/styles/tokens.css` and `frontend/src/styles/fonts.css`
and writes the woff2 files into `frontend/public/fonts/`. Neither CSS file is
edited by hand — site-specific overrides go in `global.css` so a regenerated
export keeps diffing cleanly.

Two things are deliberate departures from the export:

- **Fonts are real files, not base64.** The export inlines all three families
  into one 504 KB stylesheet. That is a render-blocking download before first
  paint. Extracted to eight woff2 files (latin + latin-ext, upright only), the
  stylesheet is 11 KB and the browser fetches only the faces a page actually
  uses, gated by `unicode-range`.
- **`--text-faint` is lightened** from #6c7480 to #7b838f. The original fails
  WCAG AA on all three dark surfaces it is used on (3.97–4.24:1 against a 4.5:1
  floor). The override is documented in `global.css`; the fix belongs upstream
  in the design file.

The components in `src/ds/` are hand-ported from the export's compiled bundle,
which targets React 18 UMD and a global namespace. After a regenerate, diff
`design/_unpacked/_ds_bundle.js` against `src/ds/` to see what moved.

The export's light theme is fully tokenised and works via
`<html data-theme="light">`, but the page template ships no toggle, so neither
does this site.

## Deploying

`render.yaml` is a Blueprint covering all three resources. It lives at the
repository root because that is the only place Render reads it from.

1. Push to GitHub, then in Render: **New > Blueprint**, point it at the repo.
2. Set `ANTHROPIC_API_KEY` on the `cd-site-api` service. It is the only secret
   Render cannot generate or wire itself.
3. Deploy. `SECRET_KEY` is generated, `DATABASE_URL` comes from the database,
   `CORS_ALLOWED_ORIGINS` is wired from the static site's URL, and
   `VITE_API_BASE_URL` is wired from the API's URL.

Migrations run through `preDeployCommand`, so a deploy needs no manual step.

### Custom domain

`corydegarmo.com` is declared on the static site in `render.yaml`, with the
apex as primary and `www` redirecting to it. `SITE_ORIGINS` on the API service
carries the same two names into `CORS_ALLOWED_ORIGINS`, merged with the wired
`onrender.com` hostname so both keep working.

DNS lives at Network Solutions. Two records, and nothing else:

| Type  | Host / Refers to | Points to               |
| ----- | ---------------- | ----------------------- |
| A     | `@`              | Render's apex IP        |
| CNAME | `www`            | `cd-site-web.onrender.com.` |

Take the apex IP from the Render dashboard rather than from here - it is shown
on the service's Settings > Custom Domains panel, and it is the authoritative
value.

Notes that cost an afternoon if missed:

- Network Solutions cannot CNAME an apex, which is why the apex uses an A
  record. That is a DNS constraint, not a Render one.
- Delete any parking or forwarding records Network Solutions added at `@` and
  `www` first. They silently win over the records above.
- The API stays on its `onrender.com` hostname. It does not need a domain: the
  browser calls it cross-origin, which CORS already allows.
- Certificates are issued by Render once DNS resolves, and can take up to an
  hour. Until then the site answers on `onrender.com`.
