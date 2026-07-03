# System Design Concepts — Senior/Staff (IC4+) Refresher

_Tailored for the DigitalOcean IC4 Design Interview (45 min, ambiguous product + system design). Sources: Hello Interview "System Design in a Hurry" (hellointerview.com), plus infra-cloud specifics relevant to DO._

---

## 0. How you'll be judged at IC4 (read this first)

At senior/staff level the bar is NOT "can you name Kafka." It is:

1. **You drive.** You proactively identify bottlenecks and lead the deep dives; the interviewer shouldn't have to drag you there.
2. **Trade-offs, always in pairs.** Never say "I'd use X." Say "X gives us A at the cost of B; the alternative Y fails here because C."
3. **Quantify.** Back-of-envelope numbers *when they change the design*, not as ritual.
4. **Requirements discipline.** You spend the first 5 minutes shrinking an ambiguous prompt into 3 functional requirements + 3 quantified non-functional ones.
5. **Production instincts.** Observability, failure modes, rollout/rollback, and cost show up in your design unprompted. (This maps 1:1 to DO's stated "operational excellence" criterion.)

---

## 1. The Delivery Framework (Hello Interview, ~45 min round)

| Step | Time | What to produce |
|---|---|---|
| 1. Functional requirements | ~3 min | "Users can..." — top 3 only. Ask clarifying Qs like you would a PM. |
| 2. Non-functional requirements | ~2 min | Quantified: "p99 read < 200ms", "99.99% availability for reads", "10M DAU / 100k writes/s". Identify the *defining challenge* of the system. |
| 3. Core entities | ~2 min | The 3–5 nouns you'll persist (User, Droplet, Event...). |
| 4. API / interface | ~5 min | REST by default. Plural resources, verbs from HTTP. Auth from token, never from request body. |
| 5. (Optional) Data flow | ~5 min | Only for pipeline-ish systems: input → transform → output sequence. |
| 6. High-level design | ~10–15 min | Boxes + arrows that satisfy the functional requirements, walked endpoint by endpoint. Keep it simple first. |
| 7. Deep dives | ~10 min | Harden against the non-functional requirements. **This is where IC4 is won.** You pick the two hardest problems and attack them. |

**Anti-patterns that fail senior candidates:** over-engineering the high-level design before it works; doing capacity math that never influences a decision; waiting to be asked about failure modes; hedging every choice without committing.

---

## 2. Core Concepts checklist

### 2.1 Networking & communication
- **HTTP/REST** — the default. Know status codes, idempotency of verbs, pagination (cursor > offset), versioning.
- **Long-polling vs SSE vs WebSockets** — the real-time ladder. Polling (simple, ~seconds latency) → SSE (server→client stream, auto-reconnect, HTTP-friendly) → WebSockets (bidirectional, stateful servers, needs L4 LB or sticky routing). Pick the *weakest* one that meets the latency need.
- **gRPC** — internal service-to-service: binary, typed contracts, streaming, ~10x faster serialization. Not for public APIs.
- **Load balancing** — L4 (TCP, connection-level, needed for WebSockets) vs L7 (HTTP-aware routing, headers/paths). Algorithms: round-robin, least-connections, consistent-hash. Health checks + connection draining. *(DO literally sells this product — be crisp here.)*
- **DNS, anycast, GSLB** — how traffic reaches a region; TTL trade-offs during failover.
- **Timeouts, retries with exponential backoff + jitter, circuit breakers** — every arrow in your diagram implicitly has these; mention once, deliberately.

### 2.2 API design
- Resource modeling, idempotency keys for unsafe retries (POST /payments with `Idempotency-Key`), rate limiting semantics (429 + Retry-After).
- Pagination, filtering, partial failure semantics for batch endpoints.

### 2.3 Data modeling & storage
- **Relational (Postgres/MySQL)** — default for product design: ACID, joins, secondary indexes. Know row-level locking, `SELECT ... FOR UPDATE`.
- **NoSQL (DynamoDB/Cassandra)** — pick for write-heavy horizontal scale or flexible schema; you design around access patterns, and lose ad-hoc joins.
- **Blob storage (S3 / DO Spaces)** — big unstructured bytes; metadata lives in a DB; **presigned URLs** so clients upload/download directly (never proxy bytes through your API servers).
- **Search (Elasticsearch/OpenSearch)** — inverted indexes for full-text; fed asynchronously via CDC/queue; eventually consistent with the source of truth.
- **Time-series (Prometheus/ClickHouse/TimescaleDB)** — metrics/monitoring designs (very DO-relevant): high write throughput, downsampling/rollups, retention tiers.
- Normalization vs denormalization; index types (B-tree default, hash for equality, GIN/inverted for text, geospatial/geohash for proximity).

### 2.4 Caching
- Cache-aside (default), write-through, write-back. TTL vs event-driven invalidation.
- **Cache stampede** protection: per-key locking, stale-while-revalidate, request coalescing.
- Hot-key problem: replicate the key, shard-local caches, or add jittered TTLs.
- CDN for static + cacheable dynamic content; edge caching semantics (cache keys, purge).

### 2.5 Scaling reads
Ladder: better indexes → read replicas (replication lag! read-your-own-writes) → cache layer → materialized views/denormalization → CDN. Cite the read:write ratio to justify each rung.

### 2.6 Scaling writes
Ladder: vertical scale → partition/shard (choose shard key = your highest-cardinality access dimension; beware cross-shard queries and hot shards) → buffer bursts with queues → batch/async where user doesn't need sync ack. **Consistent hashing** for elastic membership: only K/N keys move when a node joins/leaves; virtual nodes smooth the load.

### 2.7 Consistency, replication, consensus
- **CAP** in practice: under partition choose C or A. Default to availability; demand linearizability only where it matters (payments, inventory, quota, unique names).
- Replication: leader-follower (async = lag, sync = latency), multi-leader (conflicts), quorum (R + W > N).
- **Isolation levels** and where lost-updates sneak in; optimistic (version column, retry) vs pessimistic locking; when to reach for a **distributed lock** (Redis SET NX PX + fencing tokens; or ZooKeeper/etcd) — and why DB-level locks are usually enough.
- **Consensus (Raft/Paxos)** — one-liner competence: "etcd/ZooKeeper use Raft; I'd store cluster membership/leader election there, not build my own." *(DO runs etcd under DOKS — a nice detail to drop.)*
- Idempotency + at-least-once delivery = the practical alternative to exactly-once. Outbox pattern / CDC for atomically "write DB + publish event."

### 2.8 Queues, streams, async work
- **Queue (SQS/RabbitMQ/Kafka-as-queue)**: decouple, absorb bursts, retry with DLQ. Know visibility timeout, poison pills.
- **Stream (Kafka/Kinesis)**: replayable log, consumer groups, partitions = ordering domain = parallelism limit. Windowing (Flink) for aggregations.
- **Long-running tasks pattern**: sync API returns 202 + job id → workers consume queue → client polls or gets pushed status. Scale workers on queue depth.
- **Multi-step workflows**: sagas with compensation vs workflow engines (Temporal). Exactly-once *effects* via idempotent steps.

### 2.9 Contention & fairness
Ticketmaster-class problems: pessimistic lock vs optimistic CC vs reservation-with-TTL vs queue-per-resource. Rate limiting algorithms: token bucket (bursty-friendly, the default), sliding window counter/log; distributed enforcement via Redis + Lua (atomicity); fail-open vs fail-closed.

### 2.10 Proximity / geo
Geohash / quadtree / H3; PostGIS or Redis GEO for ≤ millions of points. Only relevant if the prompt is location-flavored.

### 2.11 Observability & operations (DO cares disproportionately)
- Metrics (RED: rate/errors/duration; USE for resources), structured logs with correlation IDs, traces.
- SLI → SLO → error budget; alert on symptoms (SLO burn) not causes.
- Deploys: blue-green, canary, feature flags; schema migrations (expand-migrate-contract).
- Failure design: blast-radius isolation (cells/AZs), graceful degradation, backpressure, load shedding.
- **Multi-tenancy** (cloud-provider bread and butter): noisy-neighbor isolation, per-tenant quotas/limits, fair scheduling, tenant-scoped encryption.

### 2.12 Security
AuthN (OAuth2/OIDC, API tokens) vs AuthZ (RBAC; team/project scoping — very DO). Secrets management, encryption in transit + at rest, presigned URL expiry, SSRF/multitenancy escape as the cloud-provider nightmare scenario.

### 2.13 Numbers to know (latency intuition)
- Memory ref ~100ns; SSD read ~100µs; intra-DC RTT 0.5–1ms; cross-region ~50–150ms.
- One modern server: ~100k+ simple QPS, ~1M concurrent idle WebSockets, RAM in the hundreds of GB — **"can this fit on one box?" is a senior question to ask out loud.**
- Postgres single node: ~tens of k writes/s, TBs of data fine with good indexes.
- Kafka partition: ~MB/s–tens of MB/s each; Redis: ~100k+ ops/s single-threaded.
- Day math: 1M requests/day ≈ 12/s; 100M/day ≈ 1.2k/s. 86,400 s/day ≈ 10^5.

---

## 3. The 8 patterns (Hello Interview) — recognize the prompt, apply the pattern

| Pattern | Trigger phrase in prompt | Default answer |
|---|---|---|
| Realtime updates | "live", "instantly see" | SSE/WebSocket + pub-sub (Redis) fan-out |
| Long-running tasks | "process", "encode", "generate report" | 202 + queue + worker pool + status endpoint |
| Contention | "limited inventory", "book/bid" | DB transactions w/ locking → distributed lock only if cross-store |
| Scaling reads | "millions view" | index → replica → cache → CDN |
| Scaling writes | "ingest", "telemetry", "events" | shard + queue buffer + batch |
| Large blobs | "upload video/images" | presigned URL + blob store + CDN + metadata DB |
| Multi-step processes | "order fulfillment", "provisioning" | saga/workflow engine, idempotent steps |
| Proximity | "nearby" | geo-index |

**DO-flavor note:** droplet/app provisioning is a *multi-step process* problem; metrics/monitoring is a *scaling writes + time-series* problem; an API rate limiter is a *contention/fairness* problem. Expect infra-flavored prompts.

---

## 4. Senior/staff differentiators to rehearse saying out loud

- "The defining challenge of this system is ___, so I'll spend my deep-dive time there."
- "I'll start with the simplest thing that satisfies the requirement, then harden it."
- "This is at-least-once delivery, so the consumer must be idempotent; here's the key."
- "I'm choosing availability over consistency here because a stale read costs us ___, but downtime costs ___."
- "At 500 writes/s this fits comfortably in one Postgres; sharding now would be premature — here's the migration path when we outgrow it."
- "How does this fail? If the queue is down we ___; if a worker dies mid-task we ___ (visibility timeout + idempotent retry)."
- "I'd instrument this with ___ and alert on ___; the SLO is ___."

---

## 5. Two-evening cram plan (interview is ~July 4)

**Evening 1:** Read this doc top to bottom → watch 1 Hello Interview premium walkthrough at 1.5x (Design Ticketmaster or Design Dropbox) → do one 35-min self-run on a whiteboard: *"Design DigitalOcean Monitoring (droplet metrics + alerts)"* using the framework, out loud.

**Evening 2:** Read `02_DigitalOcean_Questions.md` + the two worked examples in `03_Worked_Examples.md` → one more 35-min self-run: *"Design a rate limiter for the DO public API"* → skim section 4 phrases before bed.

---

_Primary sources: [Hello Interview — System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction): [Delivery Framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery), [Core Concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts), [Key Technologies](https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies), [Patterns](https://www.hellointerview.com/learn/system-design/in-a-hurry/patterns)._
