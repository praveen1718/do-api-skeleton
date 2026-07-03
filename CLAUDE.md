# Ingestion API — Engineering Conventions

FastAPI REST service for data ingestion & processing. Deployed to DigitalOcean App Platform.

## Commands
- Install: `make install`
- Run locally: `make run` (uvicorn on :8080, reload)
- Test: `make test` (pytest) — run after every change
- Lint: `make lint` (ruff) — must pass before committing
- Docker: `make docker-build && make docker-run`
- Deploy: `doctl apps create --spec .do/app.yaml` (update: `doctl apps update <APP_ID> --spec .do/app.yaml`)

## Architecture (keep these layers separate)
- `app/api/routes.py` — thin HTTP handlers only: validate → call service → respond. No business logic in routes.
- `app/services/` — business logic, testable without a server. New features start here.
- `app/models/schemas.py` — all request/response contracts as Pydantic models.
- `app/core/config.py` — 12-factor config: env vars only, never hardcode values or secrets.
- `app/core/logging.py` — structured JSON logging with request IDs.

## Non-negotiable standards (production-readiness is being evaluated)
- Every endpoint: Pydantic input validation, meaningful error responses (correct 4xx vs 5xx, no leaked stack traces or internals).
- Every request: structured JSON log line with request ID; log errors with context.
- Ingestion must stay idempotent (duplicate record IDs are dropped, count reported).
- Every new endpoint or service function gets pytest coverage (happy path + at least one failure/edge case). Prefer table-driven tests.
- Keep `/health` fast and dependency-free (App Platform health-checks it).
- API is versioned under `/api/v1/`.
- Type hints everywhere; small functions; readable > clever. No new dependencies without a reason I can defend.
- Small, frequent git commits with clear messages as work progresses.

## Workflow with AI assistants
- Propose a plan before multi-file changes; wait for approval.
- After changes: run `make lint && make test` and report results.
- If a requirement is ambiguous, state the assumption in code comments and the README rather than guessing silently.
