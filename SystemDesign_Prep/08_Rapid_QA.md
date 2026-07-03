# Rapid-Fire Q&A — Last-Minute Sheet

## 1. WebSockets, sticky routing, L4
A WebSocket is one long-lived TCP connection upgraded from HTTP. Because the connection is stateful, the load balancer must keep it pinned to one backend — an **L4 (TCP) load balancer** does this naturally since it balances *connections*, not requests. "Sticky routing" matters at L7: if you must route repeat requests/reconnects to the same server (where session state lives), use cookies/hash-based affinity. Better design: keep servers stateless and put session state in Redis, then stickiness is only a reconnect optimization, not a correctness need.

## 2. Go service architecture (typical shape)
`cmd/` (main, wiring) → `internal/handler` (HTTP, thin) → `internal/service` (business logic) → `internal/store` (DB). Interfaces at layer boundaries for testability; `context.Context` through every call for timeouts/cancellation; goroutines + channels for concurrency (worker pools); errors returned not thrown, wrapped with `fmt.Errorf("%w")`; config from env; structured logs (slog/zap). Same layering philosophy as your FastAPI skeleton.

## 3. SQL vs NoSQL — when
Default **SQL** (Postgres): relational data, joins, transactions/ACID, ad-hoc queries, < ~tens of TB. Choose **NoSQL** when: write throughput/horizontal scale beyond one node (Cassandra/Dynamo), simple key-based access patterns known upfront, flexible/sparse schema, or global low-latency KV. Rule to say: "start with Postgres; move the specific table that outgrows it, not the whole system."

## 4. Distributed systems — properties/disciplines
The network is unreliable and slow; partial failure is the normal case. Disciplines: **timeouts + retries with backoff+jitter, idempotency everywhere** (retries duplicate work), at-least-once delivery (exactly-once is achieved via idempotent consumers), replication for availability (accept lag), consensus only where you must (leader election, config), backpressure/load shedding, observability built-in. CAP: under partition, choose consistency or availability per operation.

## 5. Kubernetes / containers / pods
Container = process isolated by namespaces/cgroups with its filesystem image (Docker). **Pod** = smallest K8s unit: one or more containers sharing network/volumes. Deployment manages ReplicaSets → desired count of pods; Service gives them a stable virtual IP; Ingress routes HTTP in; HPA autoscales on metrics. K8s is a **reconciliation loop**: you declare desired state, controllers converge actual → desired (same mental model as any control plane). DOKS = DO's managed K8s (they run the control plane/etcd).

## 6. Basic cloud operations
Provision via IaC (Terraform)/CLI (doctl); VPC + firewalls; TLS certs; DNS; secrets in a manager not code; backups + tested restores; monitoring/alerts on SLOs; deploys via CI/CD with rollback (blue-green/canary); cost tagging. For the exercise: `doctl auth init`, create app/droplet, check logs (`doctl apps logs`), health checks.

## 7. App Platform vs Droplet
**App Platform** = PaaS: give it a Dockerfile/repo, it builds, deploys, TLS, scaling, health checks, zero server management — fastest path in a 3h exercise. **Droplet** = raw VM: full control, you manage OS/runtime/updates/systemd — more ops burden, more flexibility/cheaper at steady scale. Say: "App Platform for speed and managed ops today; Droplet/DOKS when I need custom networking, daemons, or GPU/custom runtimes."

## 8. Prometheus vs Grafana vs Datadog vs Kibana
- **Prometheus**: open-source metrics DB — pull/scrape model, PromQL, alerting rules. Stores numbers.
- **Grafana**: visualization/dashboards on top of Prometheus (and many sources). Draws numbers.
- **Kibana**: visualization for Elasticsearch/OpenSearch — primarily **logs** search/dashboards (ELK stack).
- **Datadog**: commercial all-in-one SaaS (metrics+logs+traces+APM) — pay instead of operate.
Typical OSS stack: Prometheus (metrics) + Grafana (dashboards) + Loki/ELK (logs) + Tempo/Jaeger (traces).

## 9. Time-series storage
Optimized for (timestamp, labels, value) appends: high write throughput, compression (delta-of-delta, Gorilla), range queries, downsampling/rollups, retention tiers (raw 15d → 5-min rollups 1y). Examples: Prometheus TSDB, ClickHouse, TimescaleDB, InfluxDB. Key design idea for "monitor millions of droplets": ingest via agents → queue → TSDB shards by series; cardinality (unique label combos) is the real scaling enemy.

## 10. Kafka vs RabbitMQ (bit of detail)
- **Kafka** = distributed **append-only log**. Producers write to topic **partitions**; consumers *pull* and track their own **offsets**; messages are retained (days) regardless of consumption → replay, multiple independent consumer groups, event sourcing, streams. Ordering per partition; parallelism = partition count. Throughput monster (sequential disk I/O, batching).
- **RabbitMQ** = **smart broker queue** (AMQP). Broker *pushes* to consumers, message is gone once acked; rich routing (exchanges: direct/topic/fanout), per-message ack, priorities, TTL, dead-letter exchanges. Great for task/work queues and complex routing; weaker at replay/scale-out streaming.
- Choose: Kafka for event streams, analytics pipelines, many readers of the same data, replay. RabbitMQ (or SQS) for classic job queues with routing. In an interview either works for "buffer the burst" — justify with retention/replay (Kafka) vs simplicity/routing (Rabbit).

## 11. API Gateway vs Load Balancer
LB distributes traffic across identical backends (L4/L7) for scale + health. API Gateway is an **application-layer front door**: authN/Z, rate limiting, routing to *different* services, request transforms, logging. Gateway usually sits in front and is itself behind/combined with an LB. One-liner: "LB = many copies of one thing; Gateway = one door to many things + policy."

## 12. HTTP codes
- **201 Created** (POST success; include Location header) · **202 Accepted** (async job started)
- **302 Found** (temporary redirect; 301 permanent — browsers cache it)
- **410 Gone** (existed, deliberately removed — vs 404 never/unknown)
- **422 Unprocessable Entity** (syntactically fine, semantically invalid — FastAPI validation errors)
- **419** — NOT a standard code (Laravel uses it for expired CSRF page). Don't use; say 401/403/440-ish semantics belong to auth.
- **429 Too Many Requests** (rate limited; send `Retry-After`)
Also ready: 200/204, 400 vs 422, 401 (who are you) vs 403 (you can't), 500 vs 502/503/504 (yours vs upstream/unavailable/timeout).

## 13. 12-factor config
Config = everything that varies between environments (DB URLs, keys, ports) lives in **env vars**, never in code or the image. One build artifact promoted through dev→staging→prod; secrets injected at runtime (secret manager); sane defaults + fail fast on missing required vars. (Your skeleton's `config.py` does exactly this — say so.)

## 14. Token bucket rate limiter (bit of detail)
Each client has a bucket with **capacity B** tokens; tokens refill at **rate r/sec**; a request takes 1 token; empty bucket → 429. Allows bursts up to B while enforcing average rate r — that burst-friendliness is why it beats fixed windows (which double-spend at window edges). Implementation: don't run a timer — store `(tokens, last_refill_ts)` and lazily compute `tokens = min(B, tokens + (now-last)*r)` on each request. Distributed: keep the state in Redis, do check-and-update atomically with a small **Lua script**; per-tenant keys give multi-tenant quotas. Decide fail-open (allow if Redis down — availability) vs fail-closed (block — protect the backend): protect-the-platform usually means fail-open for reads, closed for expensive ops.

## 15. "Jsonify" / JSON serialization
Flask: `jsonify(dict)` builds a JSON Response with correct content-type. FastAPI: return Pydantic models/dicts — auto-serialized (`model.model_dump()` / `jsonable_encoder` for tricky types). Python stdlib: `json.dumps/loads` (custom `default=` for datetime/Decimal). Go: `encoding/json` `json.Marshal` with struct tags. Node: `JSON.stringify/parse`, `res.json()` in Express.

## 16. Node.js WebSocket libraries (for the Jio experience story)
The standard ones: **ws** (bare, fast, most used), **socket.io** (rooms, auto-reconnect, fallbacks to polling, its own protocol — not pure WS), **uWebSockets.js** (C++ core, highest throughput), plus SockJS (legacy fallback). Talking points from a Jio-scale deployment: sticky/L4 routing, horizontal fan-out via Redis pub/sub adapter, heartbeats/ping-pong to reap dead connections, backpressure on slow clients, ~connection-per-memory budgeting.

## 17. REST API libraries to name
- **Python**: FastAPI (+ Uvicorn, Pydantic) — modern default; Flask (micro), Django REST Framework (batteries), httpx/requests (clients), SQLAlchemy (ORM), pytest.
- **Node**: Express (classic), Fastify (faster, schema-validated), NestJS (structured/enterprise), zod (validation), Prisma (ORM), axios/undici (clients).
- **Go**: net/http + chi or gorilla/mux (routers), Gin/Echo (frameworks), sqlx/GORM, validator; stdlib-first culture is a legit answer.

## 18. Your AI workflow stories (Grab) — how to tell them
- **DB schema comparison with LangChain:** frame = "used an LLM where deterministic diffing breaks down (semantic equivalence: renamed columns, type widening, index intent), with guardrails: deterministic pre-diff first, LLM classifies/explains only the ambiguous remainder, structured JSON output validated before use, human review on high-risk changes." Mention limits you hit (hallucinated matches → added few-shot examples/eval set). That arc — LLM for the fuzzy middle, determinism around it — is exactly the addendum's philosophy.
- **Repo-review workflow (partial):** frame = "agentic pipeline: diff → chunk by file → LLM review per chunk with repo conventions in the prompt → dedupe/rank findings → post as comments; learned that false positives kill trust, so we tuned toward high-precision few findings + eval on a golden PR set." "Partially implemented" is fine — say what shipped, what you'd do next (evals in CI, feedback loop from accepted/rejected comments).

## 19. SSE token streaming & TTFT (very brief)
LLMs generate token-by-token; **SSE** (Server-Sent Events, one-way HTTP stream) pushes tokens to the client as they're produced. **TTFT = time to first token** — the latency users actually feel; streaming makes a 10s generation feel like a 0.5s response. (TPS/inter-token latency governs the rest.)

## 20. "Pipeline vs OpenSearch"
They're different layers: the **indexing pipeline** is the *process* (load → chunk → embed → write), typically queue + workers; **OpenSearch** is the *store* it writes to — the searchable index (open-source Elasticsearch fork; DO's Knowledge Bases use it, holding both keyword/BM25 and vector indexes). Pipeline = movement, OpenSearch = destination + query engine.

## 21. Fail-closed vs fail-open
When a dependency (auth service, rate limiter, guardrail) is down: **fail-open** = let traffic through (choose availability; risk: unprotected). **fail-closed** = block everything (choose safety; risk: outage). Pick per component and say it out loud: auth/PII filter → fail-closed; rate limiter/moderation-of-tone → often fail-open. Volunteering this asymmetry is a senior signal.

## 22. False positive / false negative
FP = flagged but actually fine (alarm on nothing — erodes trust, pages at 3am, blocks good users). FN = missed real case (silent failure — breach/outage undetected). Tuning any detector (alerts, guardrails, fraud, code review bots) is trading FP↔FN; state which is costlier for the use case: for paging, FPs burn the team; for security, FNs are catastrophic.

## 23. SMB
**Small and Medium-sized Businesses** — companies roughly < 500 employees. DO's core market: individual developers, startups, and SMBs who want cloud + AI capability without hyperscaler complexity/pricing. (Their filings literally describe customers as "developers, startups, and SMBs.")

---
Good luck. Say less, decide more, narrate trade-offs.
