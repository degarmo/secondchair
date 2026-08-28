# second chair

A candidate-side agent. It interviews you to build a structured record of
your background, then answers recruiter questions about you — with every
claim pointing back at the words it came from.

Working demo, not a product.

## The four rules, and where they are enforced

| Rule | Enforced by |
|---|---|
| Every knowledge record traces to a Source | `Claim.source` is non-nullable and `on_delete=PROTECT` — a source cannot be deleted while anything cites it |
| The agent declines when it lacks data | `llm/answer.py` drops any citation outside the visible set, and an answer left with no citations is downgraded to a decline before it leaves the server |
| Extraction proposes; the human approves | Extraction only ever writes `status=PROPOSED`, and `visible_to()` filters to `APPROVED` |
| Visibility is enforced at query time | `Claim.objects.visible_to(audience)` — the only supported read path. Unknown audiences get an empty queryset |

There is a fifth check that isn't in the brief but follows from it: the
extractor must quote the candidate verbatim, and `llm/extract.py` verifies
that the quote actually occurs in the answer before the claim reaches the
review queue. A claim it can't quote never gets proposed.

## Layout

```
kb/         Source, Entity, Claim + the review API
interview/  The candidate-facing loop
ask/        The recruiter-facing endpoint
llm/        Claude: interviewer, extractor, answerer
frontend/   React single page
```

`Entity` groups `Claim`s (a job, a project, a degree) so answers get
chronology without a table per type. It holds no assertions of its own —
anything arguable lives in a Claim, where it can be sourced.

## Running it

Needs Postgres and Node.

```bash
createdb secondchair
uv sync
cp .env.example .env          # add ANTHROPIC_API_KEY
uv run python manage.py migrate
uv run python manage.py seed  # demo record, so the UI has something to show
uv run python manage.py runserver

cd frontend && npm install && npm run dev   # http://localhost:5173
```

The review queue, browsing, and the seeded record work without an API key.
The interview, extraction, and answering endpoints need one and return 503
with a readable message without it.

```bash
uv run python manage.py test
```

## Deploying

`render.yaml` provisions the web service and a Postgres instance. Set
`ANTHROPIC_API_KEY` in the Render dashboard; the rest is wired up. `build.sh`
installs both toolchains, builds the frontend, collects static, and migrates.

## Deliberately not here

Vector search (the corpus is one person and fits in context), voice, auth,
multi-tenancy, Celery.

The audience is a request parameter on `/api/ask/` rather than a session
identity, because there is no auth. That is the one place the demo is
pretending — the filter it drives is real.
