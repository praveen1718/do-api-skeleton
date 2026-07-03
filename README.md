# Ingestion API — Interview Skeleton

A small, production-minded **REST API for data ingestion & processing**, built with
FastAPI and ready to deploy to **DigitalOcean App Platform**. This is a *starting
skeleton* for the DigitalOcean IC4 build exercise — swap the placeholder data shape
and processing logic for whatever the real challenge specifies.

## Why it's structured this way

The layers are deliberately separated so each decision is easy to defend in the
Architecture Review:

| Layer | File | Responsibility |
|---|---|---|
| Entrypoint | `app/main.py` | App wiring, middleware, error handling, logging |
| HTTP | `app/api/routes.py` | Thin route handlers: validate → call service → respond |
| Business logic | `app/services/ingestion.py` | Ingestion + processing, testable without a server |
| Contracts | `app/models/schemas.py` | Pydantic request/response validation |
| Config | `app/core/config.py` | 12-factor env-var config, no hardcoded secrets |
| Logging | `app/core/logging.py` | Structured JSON logs with per-request IDs |

Production-readiness touches already in place: **input validation** (Pydantic → 422s),
**meaningful error handling** (no leaked stack traces, clean 500s), **structured JSON
logging** with request-ID tracing, a **/health** probe, **idempotent** ingestion
(duplicate IDs dropped), a **non-root multi-stage Docker image**, **CI** (lint + tests +
image build), and a **DO App Platform spec**.

## Endpoints

- `GET  /health` — liveness/readiness probe
- `POST /api/v1/ingest` — accept a batch of records
- `GET  /api/v1/results` — return an aggregation over ingested data
- `GET  /docs` — auto-generated Swagger UI (FastAPI)

Example:

```bash
curl -X POST localhost:8080/api/v1/ingest \
  -H 'content-type: application/json' \
  -d '{"records":[{"id":"1","source":"sensor-a","timestamp":"2026-07-04T10:00:00Z","value":21.5,"metadata":{}}]}'

curl localhost:8080/api/v1/results
```

## Run locally

```bash
make install          # pip install -r requirements-dev.txt
make run              # uvicorn on :8080 with reload
make test             # pytest
make lint             # ruff
```

Or via Docker:

```bash
make docker-build
make docker-run       # serves on :8080
```

## Deploy to DigitalOcean (on the day)

```bash
doctl auth init                          # paste the token DO gives you
doctl apps create --spec .do/app.yaml    # App Platform builds the Dockerfile
# ...later:
doctl apps update <APP_ID> --spec .do/app.yaml
```

App Platform builds the `Dockerfile`, injects `$PORT`, and health-checks `/health`.
Alternative if they want a Droplet instead: `scp` the repo up, `docker build`,
`docker run -p 80:8080` — the same image works either way.

## What to adapt on the day (don't over-build in advance)

1. **The data shape** in `schemas.py` — match the challenge's real payload.
2. **The processing logic** in `ingestion.py::process` — currently a trivial aggregate.
3. **The datastore** — the in-memory `_store` is a placeholder; wire a real DB,
   queue, or DO Spaces (object storage) if the spec calls for persistence/scale.
4. **Deploy target** — spec assumes App Platform; adjust if they want DOKS/Droplet.

## Talking points for the Architecture Review

- Why FastAPI: async, built-in validation, auto OpenAPI docs — fast to a correct API.
- Why the service/HTTP split: testability and swappable persistence.
- Trade-offs consciously deferred: in-memory store (would use Postgres/Spaces at
  scale), single instance (would scale horizontally behind App Platform / add a queue
  for backpressure on high-volume ingestion).
- How I'd evolve it: batching to a queue, idempotency keys persisted, rate limiting,
  metrics endpoint (Prometheus), structured retries on downstream writes.
