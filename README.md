# corydegarmo — personal site with an interview agent

A single-page parallax site for Cory DeGarmo. The centerpiece is an embedded
agent that answers hiring-manager questions in his voice, grounded strictly in
`backend/kb/KNOWLEDGE_BASE.md`.

- **Backend:** Django 5 + Django REST Framework, PostgreSQL, Anthropic Claude
  (`claude-sonnet-5`).
- **Frontend:** React 19 + TypeScript (Vite), CSS modules, `lucide-react`.
- **Deploy:** Render — one web service, one static site, one Postgres.

```
backend/
  config/          Django project (settings, urls, wsgi, asgi)
  agent/           The interview endpoint, model, throttle, tests
  kb/              KNOWLEDGE_BASE.md — the single source of truth
frontend/
  src/sections/    Hero, About, Track, Builds, Interview, Footer
  src/components/  Nav, AgentChat, ParallaxLayer
  src/content.ts   Site copy, all of it copied from the knowledge base
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
value with no working default — without it the endpoint returns 503 with an
"email Cory instead" message rather than failing silently.

## Checks

```bash
cd backend && python manage.py check     # Django system checks
cd backend && python -m pytest           # 22 tests, no network calls
cd frontend && npm run build             # tsc --strict, then vite build
```

The test suite mocks the Anthropic client; nothing in it spends money.

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
{ "answer": "...", "session_id": "uuid" }
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

`GET /healthz/` returns `{"status": "ok"}` for Render's health check.

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

When a custom domain is attached, add it to `ALLOWED_HOSTS` on the API service
and to `CORS_ALLOWED_ORIGINS` if the site is served from a different hostname
than the Render static site.
