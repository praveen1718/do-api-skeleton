# DigitalOcean IC4 Interview — MASTER PREP DOC
### Agentic AI · Senior Software Engineer II · Hiring Day ~July 4, 2026

_Everything from the 8 prep docs in one file, full content preserved. The Day-Of Playbook appears as its updated v2. Companion code (not in this doc): `do-api-skeleton/` (Python skeleton + CLAUDE.md), `go-ingest/` (Go architecture demo + goroutines notes), `rag-demo/` (working RAG pipeline)._

**Reading order if short on time: Part 7 (agentic) → Part 4 (playbook) → Part 1 §4 (senior phrases) → Part 8 (rapid Q&A).**

| Part | Content |
|---|---|
| 1 | System design concepts (senior/staff refresher) |
| 2 | Previously asked DO questions + likely prompts |
| 3 | Two worked examples (URL shortener, package dependency tracker) |
| 4 | Day-of playbook **v2** (kickoff prompt, workflow, timeline) |
| 5 | DSA brush-up |
| 6 | STAR stories worksheet |
| 7 | Agentic AI addendum (Gradient, RAG, agents, evals) |
| 8 | Rapid-fire Q&A (23 answers) |

---

# PART 1 — SYSTEM DESIGN CONCEPTS

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

**Evening 2:** Read Part 2 + the two worked examples in Part 3 → one more 35-min self-run: *"Design a rate limiter for the DO public API"* → skim section 4 phrases before bed.

---

_Primary sources: [Hello Interview — System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction): [Delivery Framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery), [Core Concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts), [Key Technologies](https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies), [Patterns](https://www.hellointerview.com/learn/system-design/in-a-hurry/patterns)._

---

# PART 2 — DIGITALOCEAN QUESTIONS

# Previously Asked DigitalOcean System Design Questions (+ what to expect)

## A. Verified reports from candidates

These are the design questions publicly reported by DigitalOcean candidates (Interview Query's DO guide, LeetCode Discuss, Glassdoor reports — note Glassdoor pages block scraping, so treat individual reports as directional):

1. **Design a URL shortener** — the classic, reported in DO software-engineer interviews. At senior level they push on: ID generation at scale, redirect latency (cache/CDN), analytics ingestion, and hot-link handling. *(Worked example #1 in Part 3.)*
2. **Design/implement a TCP service that tracks dependencies between software packages** — a DO signature question (reported for years, sometimes as the coding round, sometimes discussed architecturally). It's essentially a package index (think apt/npm registry): dependency graph storage, cycle handling, concurrent index/remove/query correctness. *(Worked example #2.)*
3. **Design a system to handle large datasets for AI/ML workloads** — reported recently (DO has been pushing GPU droplets/Gradient). Object storage + metadata catalog + throughput-oriented data plane.
4. General process reports confirm a **distributed-systems-flavored design round** for senior candidates, with interviewers probing Kubernetes, containers, Go-service architecture, and cloud operations knowledge.

## B. What YOUR round will likely be (from your own prep docs)

Your `instrcutions_1st.txt` describes the 45-min round as **"ambiguous, real-world problem... product design AND system architecture... empathise with user needs."** That's a *product-flavored* design interview in Hello Interview terms — expect a prompt about a feature/service a cloud customer would use, not "design Google." Also note the **Architecture Review (40 min)** is a second, separate design conversation about *your own build* — scaling the ingestion API you just wrote.

## C. High-probability DO-flavored prompts to rehearse

DigitalOcean interviewers habitually draw from their own product surface. Each of these maps to a pattern you already know:

| Prompt | Underlying pattern(s) |
|---|---|
| Design droplet provisioning (user clicks "Create" → VM runs) | Multi-step workflow, saga, idempotency, placement/scheduling |
| Design DO Monitoring: collect metrics from millions of droplets + alerting | Scaling writes, time-series storage, streaming aggregation, alert evaluation |
| Design a rate limiter for the DO public API | Contention/fairness, Redis, token bucket, multi-tenant quotas |
| Design object storage (Spaces) or just its upload path | Large blobs, presigned URLs, metadata vs data plane, erasure coding (staff-level bonus) |
| Design App Platform (git push → deployed app) | Long-running tasks, build pipeline, blue-green deploys |
| Design a status page / health dashboard for customer resources | Realtime updates (SSE), fan-out, read scaling |
| Design usage metering & billing (bill per droplet-hour, per GB) | Event ingestion, exactly-once accounting, reconciliation |
| Design managed Postgres (DBaaS): backups, failover, connection pooling | Replication, leader election, control plane vs data plane |
| Design a webhook delivery system for platform events | Queues, retries + DLQ, idempotency, per-tenant fairness |

**The control-plane / data-plane split** is the single most DO-relevant architectural idea: the control plane (API, desired state in Postgres, reconciliation loops — the Kubernetes operator mental model) is small-scale and consistency-leaning; the data plane (the droplets/bytes/packets themselves) is huge-scale and availability-leaning. Opening an infra prompt with this split is an instant senior signal.

## D. For the 45-min round specifically — product-design checklist

Because they said "empathise with user needs":
- Name 2–3 concrete user personas (solo dev, small SaaS team, agency) before drawing boxes.
- State user-facing success metrics (time-to-first-deploy, alert latency) alongside system NFRs.
- Propose an MVP scope + a v2; say what you're deliberately NOT building.
- Close the loop: "how do we know users are happy?" → instrumentation/feedback.

---

### Sources
- [Interview Query — DigitalOcean Software Engineer Interview Guide](https://www.interviewquery.com/interview-guides/digitalocean-software-engineer) (URL shortener, TCP package-dependency service, AI/ML dataset system, process overview)
- [Glassdoor — DigitalOcean Interview Questions](https://www.glassdoor.com/Interview/DigitalOcean-Interview-Questions-E823482.htm), [Senior SWE page](https://www.glassdoor.com/Interview/DigitalOcean-Senior-Software-Engineer-Interview-Questions-EI_IE823482.0,12_KO13,37.htm) (candidate reports; pages block automated reading — worth a manual skim while logged in)
- [LeetCode Discuss — DigitalOcean Staff Software Engineer](https://leetcode.com/discuss/post/6853090/) and [DigitalOcean Interview | Need Help](https://leetcode.com/discuss/interview-experience/5875038/DigitalOcean-Interview-or-Need-Help/)
- [AlgoDaily — DigitalOcean interview process & coding questions](https://algodaily.com/companies/digitalocean)
- [Prepfully — DigitalOcean SWE question bank](https://prepfully.com/interview-questions/digitalocean/software-engineer)
- [Hello Interview — System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction)

---

# PART 3 — WORKED EXAMPLES

# Worked Examples — Two Previously Asked DigitalOcean Design Questions

Both are solved with the Hello Interview delivery framework, at the depth an IC4 should narrate in ~40 minutes. Practice saying these out loud, not just reading them.

---

# Example 1 — Design a URL Shortener (reported at DO; the "can you do the basics excellently" question)

## 1. Functional requirements (~3 min)
1. Users can submit a long URL and get a short link (optionally a custom alias, optional expiry).
2. Anyone hitting the short link is redirected to the original URL.
3. (Deprioritized, say it out loud:) click analytics, auth, link management UI.

## 2. Non-functional requirements
- **Read-heavy**: assume 100M new URLs/month (~40 writes/s) vs redirects at ~10k reads/s → ~250:1 read:write. **The defining challenge is redirect latency + availability, not write scale.**
- Redirect p99 < 100ms; availability 99.99% for redirects (a broken redirect is a broken customer page).
- Short codes must be unique, never re-assigned while live; eventual consistency acceptable for analytics only.
- Scale envelope: 100M/month × 5 years ≈ 6B URLs. At ~500 bytes/row ≈ 3TB — *one Postgres can hold it, but read QPS pushes us to cache anyway.*

## 3. Core entities
`Url` (short_code PK, long_url, owner_id, created_at, expires_at), `User`, `ClickEvent` (async, analytical).

## 4. API
```
POST /urls            {long_url, custom_alias?, expiry?} → 201 {short_url}
GET  /{short_code}    → 302 Location: long_url
GET  /urls?owner=me   (list; auth from token)
```
Senior notes to voice: **302 vs 301** — 301 is cached permanently by browsers → you lose analytics and can't update the target; use 302 (or 308/307 semantics if method preservation mattered). Idempotency: same (owner, long_url) can dedupe or not — product decision, say you'd ask.

## 5. High-level design
Client → API Gateway/LB → **Write service** and **Redirect service** (separate deployables: wildly different scale/SLO — this separation is itself a senior signal) → Postgres (primary store) + Redis (redirect cache) + queue → analytics pipeline.

Write path: validate URL (syntax, blocklist/SSRF check) → generate code → insert row → return.
Read path: Redis GET short_code → hit: 302; miss: Postgres lookup → populate cache → 302. Emit ClickEvent to Kafka **after** responding (fire-and-forget; analytics must never add redirect latency).

## 6. Deep dives (where the interview is decided)

**(a) Short-code generation — the classic probe.**
- Hash long_url (MD5 → base62, take 7 chars): deterministic dedupe, but collisions need probe-and-retry, and same URL from two users collides intentionally — messy with ownership.
- **Counter + base62 encode (my pick):** a global sequence gives guaranteed-unique, 7 chars of base62 = 62^7 ≈ 3.5 trillion — enough forever. Sequential codes are guessable → if that matters, apply a bijective permutation (e.g., multiply by large prime mod 62^7) or prepend random bits.
- Distributing the counter: don't hit one Postgres sequence per write at high scale — **block allocation**: each API instance leases a range of 10k IDs from a coordination store (Postgres row with `UPDATE ... RETURNING`, or ZooKeeper/etcd). Loses at most one block on crash; no per-request coordination. (This is the answer interviewers fish for.)
- Custom aliases: separate namespace check, unique index, reserve-on-create.

**(b) Redirect latency & availability.**
- Cache hit ratio: Zipfian access → a few GB of Redis covers the hot set; ~1ms lookups. Cache-aside with TTL + explicit invalidation on URL update/delete.
- Redis down? **Fail open to Postgres** (degraded latency, not availability). Replicated Redis for HA.
- Multi-region (staff-level): redirects served from every region with a read replica or regional cache; writes home to one region — acceptable because create→first click has seconds of slack. Mention CDN/edge KV (Cloudflare Workers-style) as the endgame.

**(c) Expiry & deletion.** Lazy check at read time (`expires_at < now` → 410 Gone) + background sweeper. Never re-issue codes from expired URLs immediately (cached 301s in the wild) — tombstone period.

**(d) Abuse (the cloud-provider angle DO likes).** Rate limit creates per token (token bucket in Redis); malware/phishing URL scanning async post-create with kill switch; per-tenant quotas.

**(e) Analytics.** ClickEvents → Kafka → stream aggregation (Flink or simple consumer) → rollups in OLAP store (ClickHouse). At-least-once + idempotent upsert on (short_code, minute) is fine — counts, not money.

## What "good" sounded like
You committed to counter+base62 with block allocation, justified 302, separated read/write services, protected redirect latency from every optional feature, and volunteered failure modes (Redis down, region down) before being asked.

---

# Example 2 — Package Dependency Tracking Service (the DO signature question)

_Reported form: "implement/design a TCP service that tracks dependencies between software packages" — DO has used this as a coding exercise (the famous `INDEX|pkg|deps` protocol challenge) and as a design conversation. Below is the design-round treatment; knowing the small-scale version also preps you for the coding variant._

## 0. The small version first (60 seconds, shows you recognized it)
A TCP server accepting lines `INDEX|pkg|dep1,dep2\n`, `REMOVE|pkg|\n`, `QUERY|pkg|\n`, replying OK/FAIL/ERROR. Invariants: a package may be indexed only if all its deps are already indexed; removed only if nothing depends on it. Core: an in-memory graph `deps: pkg→set` and reverse index `rdeps: pkg→set`, guarded for concurrent clients (one big mutex is fine at this scale — say why: operations are microseconds, contention is nil; per-key locking is premature). Correctness > cleverness.

## 1. Scale it up: functional requirements (design-round version)
"Now make it a real registry service (think a package index for apt/npm-scale traffic)":
1. Publish a package version with its dependency list (validated: deps must exist).
2. Remove/yank a version only if no other package depends on it (or with a force/deprecate flow).
3. Query: direct deps, reverse deps ("what breaks if I remove X?"), full transitive closure for a resolver.

## 2. Non-functional requirements
- Reads dominate: resolvers hammer the index. ~100k reads/s vs ~10 writes/s. **Defining challenges: (1) correctness of the dependency invariant under concurrency, (2) read scaling of graph queries.**
- Writes need strong consistency (publishing against a stale view breaks the invariant). Reads can lag seconds.
- The graph is a DAG per ecosystem; cycles must be rejected (or handled per ecosystem rules — ask!).

## 3. Core entities
`Package`, `PackageVersion` (immutable once published!), `DependencyEdge` (version → constraint on package). Immutability of published versions is the key modeling insight — it makes caching trivial and removals rare.

## 4. API
```
POST   /packages/{name}/versions        {version, deps: [{name, constraint}]}
DELETE /packages/{name}/versions/{v}
GET    /packages/{name}/versions/{v}/deps?transitive=true
GET    /packages/{name}/rdeps
```

## 5. High-level design
Write path → **single writer domain**: API validates against Postgres in one transaction:
```sql
BEGIN;
  -- all deps exist?
  SELECT ... FROM package_versions WHERE (name,ver) matching constraints FOR SHARE;
  INSERT INTO package_versions ...;
  INSERT INTO dependency_edges ...;
COMMIT;
```
`FOR SHARE` on dependency rows prevents a concurrent REMOVE from deleting a dep mid-publish; the DELETE takes `FOR UPDATE` on the version row and checks `rdeps == ∅` in the same transaction. **This is the whole concurrency story: let Postgres transactions enforce the invariant — no distributed locks needed at 10 writes/s.** Saying that plainly is the senior move.

Read path: replicas + cache. Direct deps/rdeps: adjacency rows, indexed both directions ((from) and (to) indexes on edges). Because versions are immutable, cache entries never invalidate except on yank → near-100% hit ratio, CDN-able JSON.

## 6. Deep dives
**(a) Transitive closure / resolution.** Don't compute full closures server-side per request at npm scale — either (1) serve per-package metadata and let the client resolver walk (what npm/apt actually do; metadata is CDN-cached), or (2) precompute + cache closure for hot packages with bounded depth, invalidated on new publishes of anything in the closure (expensive — argue for option 1). Cycle detection at publish time: DFS from the new version over constraint-resolved edges; guaranteed acyclic thereafter by induction.

**(b) Removal semantics.** Hard delete breaks the world (left-pad!). Propose **yank** (hidden from resolution, still downloadable) as the product answer; hard delete only when rdeps=∅, checked transactionally. Interviewers love that you know the left-pad story.

**(c) Scaling writes later.** If publishes grew 1000x: partition by package name (all invariant checks are within one package's neighborhood... except dep-existence checks cross partitions → route through a validation service reading a replicated, slightly-stale view + compensating re-check, or keep writes on one strong store since even npm does ~low writes/s. Defend the boring answer with numbers.)

**(d) Ops.** Audit log of publishes (append-only, also feeds CDC → search index, cache busting, webhooks). Metrics: publish latency, invariant-violation rejects, resolver p99, cache hit ratio. Abuse: name-squatting checks, per-publisher rate limits, malware scanning pipeline.

## What "good" sounded like
You spotted the invariant ("deps exist before index; no removal while depended-upon") as the heart of the problem, enforced it with plain DB transactions instead of exotic machinery, exploited version immutability for caching, and knew the real-world precedents (npm metadata + client-side resolution, yanking).

---

## Bonus sketch — "Large datasets for AI/ML workloads" (also reported at DO, 5-line version)
Control plane: dataset catalog (Postgres: datasets, versions, schemas, lineage, ACLs). Data plane: object storage (Spaces/S3) with datasets as immutable versioned snapshots (Parquet + manifest files, Iceberg-style). Ingest: multipart presigned uploads → validation workers → commit manifest atomically. Serving: presigned range reads, colocate GPU compute with storage region, throughput via parallel range GETs; cache hot shards on local NVMe. The manifest-commit gives atomic dataset versions without ever moving bytes.

---

# PART 4 — DAY-OF PLAYBOOK (v2)

# Day-Of Playbook v2 — Build Exercise (3h)

_v2 changes (after learning the role is **Agentic AI · SSE II**): kickoff prompt now includes an optional AI-processing-step standard (mocked LLM calls in tests, isolated client wrapper); first-15-min adds Claude Code extension sign-in specifics and /usage check; notes-access now includes the go-ingest and rag-demo repos; review-prep adds your positioning line and AI-workflow ownership points. Timeline unchanged._

## 0. First 15 minutes, in order

1. Sign into GitHub (`gh auth login`) and Claude — spark icon in Cursor's editor toolbar → Sign in (browser flow), or `claude` + `/login` in the terminal. Run `/usage` once to confirm the account works; check which model is selected via `/`.
2. Verify Cursor's built-in AI responds (Cmd+L) — that's your guaranteed fallback.
3. `git init` the repo (or clone theirs). Recreate the skeleton (kickoff prompt below).
4. Drop in `CLAUDE.md` + `.cursorrules` + `AGENTS.md` (identical content — Claude Code reads the first, Cursor the second, other agents the third). Pull from your GitHub prep repo.
5. `make run` + `curl /health` — prove the walking skeleton works BEFORE features.
6. Kick off deploy #1 early (`doctl auth init`, `doctl apps create --spec .do/app.yaml`) — App Platform builds take minutes; discovering deploy problems at 0:30 beats 2:45.

## 1. The kickoff prompt (fill the blanks from their requirements)

Paste into Claude Code (plan mode ON) after `git init`:

```
You are helping me build a production-minded REST API in a 3-hour window.

REQUIREMENTS (from the exercise spec):
<paste their requirements verbatim here>

MY ASSUMPTIONS (correct me if any conflict with the requirements):
- Language: Python 3.12 + FastAPI + pytest + ruff
- Deploy target: DigitalOcean App Platform via Dockerfile and .do/app.yaml
  (adjust if the spec says Droplet/DOKS)

ENGINEERING STANDARDS (apply these even though the spec may not mention them —
they are being evaluated):
- Layered structure: thin routes / services with business logic / Pydantic
  schemas / env-var config / structured JSON logging with request IDs
- Every endpoint: input validation, correct 4xx vs 5xx errors, no leaked internals
- /health endpoint, fast and dependency-free
- API versioned under /api/v1/
- Idempotent ingestion (dedupe by record ID) if ingestion is involved
- pytest for every endpoint + service (happy path + failure cases)
- Multi-stage non-root Dockerfile; GitHub Actions CI (lint + test + build)
- Type hints, small functions, no unnecessary dependencies
- IF the spec includes an AI/LLM/embedding processing step: isolate it behind a
  service-layer interface with an httpx client wrapper (timeout, retry with
  backoff, API key from env var), and MOCK the model call in all tests —
  never call a live model from pytest. Validate/parse any structured model
  output before using it.

TASK — first iteration only:
Create the full project skeleton with ALL of the above standards wired in, and
implement ONLY the single most core requirement end-to-end (one endpoint working
with tests). Leave the remaining requirements as clearly named TODO stubs.
Also write a CLAUDE.md capturing these standards and the make commands.
Show me the plan first; after I approve, generate the code, then run
`make lint && make test` and show results.
```

Note: your instructions mention pre-installed **image processing libraries** — if the challenge involves image data, the same standard applies: isolate the processing step in a service, stream/chunk large files, test with tiny fixture images.

## 2. One-shot the whole repo, or iterate? — Iterate, deliberately

One-shot generation loses on every axis that matters in an *evaluated* exercise:

- **You must defend every line in the 40-min Architecture Review.** A 2,000-line one-shot dump means reverse-engineering your own repo under questioning. Iterating means you reviewed each diff as it landed — the narrative writes itself.
- **Verification collapses.** One giant change = one giant debugging session. Small iterations = `make test` green after each step, always a working commit to fall back to (plus Claude Code's per-message rewind).
- **Requirements drift.** Models over-build in one-shots; you burn time deleting unneeded features ("quality of thought > quantity of features").
- **Commit history is evidence.** 8–12 meaningful commits shows engineering process; one "initial commit" shows prompt engineering.

The right compromise is a **big first bite, then loops**: skeleton + standards + ONE core endpoint end-to-end (the kickoff prompt), deploy it, then one requirement per prompt: implement → review diff → test → commit → next.

## 3. Suggested iteration prompts (after kickoff)

- "Implement requirement 2: <paste>. Follow CLAUDE.md standards. Plan first, then code + tests."
- "Review the whole repo for gaps against these evaluation criteria: production-readiness, error handling, observability, testing. List issues by severity — don't change anything yet."  ← run at ~2:00, a free self-review
- "Write the README: endpoints, how to run/test/deploy, key design decisions and trade-offs, and what I'd do next at scale." ← feeds the Architecture Review directly
- "Generate a .github/workflows/ci.yml that lints, tests, and builds the Docker image."

## 4. CLAUDE.md vs Cursor — who reads what

| File | Read automatically by |
|---|---|
| `CLAUDE.md` | Claude Code (extension panel AND `claude` CLI) |
| `.cursorrules` (or `.cursor/rules/`) | Cursor's built-in AI (Cmd+L / Cmd+K / Composer) |
| `AGENTS.md` | Newer Cursor versions + several other agents |

Keep the content identical. Committing all three costs nothing.

## 5. Getting your prep onto the interview laptop

Personal logins are allowed (recruiter-confirmed), so:

1. **Best: private GitHub repo.** Push `SystemDesign_Prep/`, `do-api-skeleton/`, `go-ingest/`, and `rag-demo/` to a private repo tonight. On the day: `gh auth login` → `gh repo clone`. Skeleton + notes + both demos in one step. (Your own reference material within the "docs + any AI tools are fair game" rules; be transparent if asked.)
2. **Backup: claude.ai in Chrome** — this whole conversation is in your Claude account.
3. **Last resort: email yourself a zip.**

Smoke-test the clone tonight: fresh directory, `make install && make test && make run`.

## 6. Architecture Review — three things to have ready (new in v2)

1. **Positioning line:** "I come from backend/distributed systems, and agentic AI is where that discipline matters most — an agent is a workflow with a probabilistic step inside, so idempotency, retries, and observability become the product."
2. **Own the AI workflow:** "I set standards in CLAUDE.md up front, worked plan-first, reviewed every diff, and the tests are the contract" — agentic-AI-native engineering judgment, demonstrated live.
3. **Scale story for YOUR build:** where it breaks first (in-memory store → Postgres; sync processing → queue + workers; single instance → horizontal + rate limiting), with rough numbers.

## 7. Timeline cheat-card

| Clock | Doing |
|---|---|
| 0:00–0:15 | Logins, clone/init, skeleton, CLAUDE.md |
| 0:15–0:30 | Walking skeleton runs locally; adapt schemas to the real data shape |
| 0:30–0:45 | First deploy to DO kicked off; core endpoint #1 done with tests |
| 0:45–2:15 | Feature loops (one requirement per prompt; commit each) |
| 2:15–2:40 | Self-review prompt, fix top issues, README/decisions, final deploy |
| 2:40–3:00 | Buffer: verify deployed URL end-to-end with curl; prep 3 talking points for the review |

---

# PART 5 — DSA BRUSH-UP

# DSA Brush-Up — What Actually Comes Up on This Interview Day

**Expectation-setting:** your hiring day has no dedicated DSA round. Where data structures CAN appear: (1) inside the build ("why a dict here?", dedupe/aggregation logic), (2) the Architecture Review ("what's the complexity of your processing step? what happens at 10M records?"), (3) the design round (choosing structures for indexes/queues). DO's *earlier* screening rounds have used LeetCode-style questions (graphs, strings, arrays — see prep doc 02 sources), so a light refresh is cheap insurance. This doc is that refresh — 30 minutes, not a grind.

## 1. Complexity you should say without thinking

| Structure (Python) | Op | Cost | One-liner you might say in review |
|---|---|---|---|
| `dict` / `set` (hash table) | get/put/in | O(1) avg | "Dedupe by ID is a set lookup — O(1) per record, O(n) for the batch." |
| `list` (dynamic array) | append / index | O(1) am. / O(1) | "Append-only event buffer." |
| `list` | insert(0,·) / `x in list` | O(n) | why you DON'T scan lists for membership |
| `collections.deque` | popleft/append | O(1) | in-memory FIFO queue, sliding windows |
| `heapq` (binary heap) | push/pop | O(log n) | top-K, scheduling next-due job, rate-limiter timers |
| Sorted array / `bisect` | search | O(log n) | percentiles over a static batch |
| B-tree (DB index) | search/insert | O(log n) | "every WHERE/ORDER BY column I query is B-tree indexed" |
| Balanced BST / skiplist | ordered ops | O(log n) | Redis sorted sets (leaderboards, sliding-window rate limits) |

Sorting: O(n log n) (Timsort). Hashing a batch: O(n). String concat in a loop: O(n²) — use `''.join`.

## 2. The five structures behind system-design components (be able to name these)

1. **Hash map** → caches, dedupe, session stores, shard routing (consistent hashing = hash ring).
2. **Heap / priority queue** → top-K trending, task schedulers, timer wheels, Dijkstra-ish nearest.
3. **Log / append-only array** → Kafka partitions, WALs, LSM memtables. Sequential I/O is why writes are fast.
4. **B-tree vs LSM-tree** → B-tree: read-optimized, in-place (Postgres). LSM: write-optimized, compaction (Cassandra, RocksDB). One sentence each is staff-level signal.
5. **Graph + adjacency sets** → the DO package-dependency question: `deps: dict[str, set]` + reverse index `rdeps: dict[str, set]`; cycle check = DFS with visiting/visited states; "what breaks if I remove X" = BFS over rdeps (transitive closure).

Bonus one-liners: **Bloom filter** ("cheap probabilistic 'definitely not present' — saves disk lookups"), **HyperLogLog** ("approximate distinct counts in KBs"), **inverted index** ("word → doc list; how Elasticsearch works"), **geohash/quadtree** ("2D → sortable 1D for proximity").

## 3. Patterns likely inside a 3-hour ingestion build

- **Dedupe:** `seen: set[str]`; idempotency = same input, same result, no double effects.
- **Aggregation:** single pass with `dict[key, (count, sum, min, max)]` — O(n), constant memory per key. Percentiles: sort the batch O(n log n) or keep a heap.
- **Top-K:** `heapq.nlargest(k, items)` — O(n log k), never sort everything for K items.
- **Sliding window (rate limit / rolling stats):** deque of timestamps, evict from left.
- **Streaming a big file:** iterate line-by-line (O(1) memory), never `read()` a 2GB upload; batch DB writes every N records.
- **Graph/deps input:** build forward + reverse adjacency immediately; most questions become trivial traversals.

## 4. If a screen-style question sneaks in (their reported favorites)

Reported DO coding themes (AlgoDaily/Glassdoor): graph-is-a-tree (n-1 edges + connected + no cycle), duplicate words / frequency maps, substring search, contiguous subarray sum (prefix sums / Kadane), edit distance (2D DP), max rectangle in histogram (monotonic stack). If you have 45 spare minutes ever: re-solve *graph-is-a-tree* and *subarray sum* — the other patterns follow.

## 5. Review-proofing your build (say complexity before they ask)

For each endpoint be ready with one sentence: "POST /ingest is O(n) in batch size with O(u) memory for u unique IDs; GET /results is O(k) over aggregated keys; at 10M records/day none of this is the bottleneck — the network and the datastore are, which is why I'd add a queue before workers rather than optimize this loop."

---

# PART 6 — STAR STORIES

# Behavioral Round — 5 STAR Stories Worksheet (30-min interview)

Their own words for this round: *"how you influence without authority, navigate ambiguity, mentor others, and align your work with broader engineering goals."* So the story set below is built to cover exactly those, plus the universal "failure" question.

## DigitalOcean values to echo (their published language)

"We think big, bold, and scrappy" · "bias to action" · "growth mindset" · "customers and community are at the HEART of everything we DO" · "we act like owners" · simplicity as a product virtue. Weave 1–2 phrases per story naturally — e.g., end a story with "...which is why I default to the simplest design that works," or "I treated it as an owner problem, not a ticket."

## STAR discipline (say less, land more)

Situation ≤ 2 sentences (context, stakes, numbers). Task = your specific responsibility. Action = 60% of airtime, "I" not "we", include ONE decision you made against an easier alternative. Result = quantified + what changed permanently (process, system, person). ~2.5 minutes per story max, then stop talking — let them dig.

---

## Story 1 — Influence without authority  *(their #1 listed theme)*
**Prompt it answers:** "Tell me about driving a change you didn't have the power to mandate."
- Situation: a cross-team decision you disagreed with, or a standard/tool/architecture you wanted adopted org-wide.
- Your levers to mention: data/prototype instead of opinion, finding the real objection, giving away credit, small pilot → evidence → adoption.
- Result: adoption metric + relationship intact.
- IC4 signal: you changed the *system* (standard, template, review process), not just the one decision.

**My story:** _____________________

## Story 2 — Navigating ambiguity  *(their #2 theme; also feeds the design round)*
**Prompt:** "Tell me about a project with unclear/changing requirements."
- Situation: vague mandate ("make it scale", "improve reliability") or shifting product ground.
- Actions: how you decomposed unknowns, cheapest experiment first, explicit assumptions written down, checkpoint cadence with stakeholders.
- Result: shipped despite fog + the de-risking habit you kept.

**My story:** _____________________

## Story 3 — Mentoring / growing others  *(their #3 theme)*
**Prompt:** "How have you leveled someone up?"
- Pick ONE person, be concrete: their gap → your method (pairing, review style, delegating something scary with a safety net) → their outcome (promo, ownership, they now mentor).
- Avoid "I answer questions when asked" — show deliberate investment. Growth-mindset language fits here.

**My story:** _____________________

## Story 4 — Conflict / disagreement with data
**Prompt:** "Disagreement with a colleague/manager — how did you resolve it?"
- Best shape: you were partially wrong OR you disagreed-and-committed after a fair fight. Show you separated the technical question from the ego question, sought data, and preserved the relationship.
- Anti-pattern: a story where you were simply right and they were dumb.

**My story:** _____________________

## Story 5 — Failure / production incident you owned
**Prompt:** "Biggest technical mistake?" / "A time you failed."
- Real failure with your fingerprints on it (not "I worked too hard"). Structure: mistake → blast radius honestly stated → immediate handling → root cause → the guardrail you built so the CLASS of error is gone → "act like an owner" close.
- Bonus if the guardrail is operational (alert, runbook, CI check) — matches their operational-excellence bar.

**My story:** _____________________

---

## Also have one-liners ready for
- "Why DigitalOcean?" — tie to their customer base (developers, startups, SMBs) + simplicity ethos + your own experience with DO/cloud tooling. Be specific, not "great culture."
- "Why leave your current role?" — forward-looking, never negative.
- "Questions for us?" — ask about: how the team measures operational excellence; what separates good from great IC4s here; current scaling challenge on their product area.

## Rehearsal (fits tonight's schedule)
Fill the 5 blanks in writing (bullets, not scripts) → say each aloud once at 2.5 min → for stories 1 & 2, prepare one follow-up detail you *didn't* say (they will dig; having depth in reserve reads as authentic).

---

# PART 7 — AGENTIC AI ADDENDUM

# Agentic AI Addendum — for "Agentic AI · Senior Software Engineer II (IC4)"

The role name changes the odds on everything: expect the design round (and possibly the build's "data ingestion & processing") to be **LLM/agent-flavored**, and expect interviewers from the **Gradient AI Platform** org. This doc = the extra vocabulary + the DO-specific product context + the most likely prompts.

---

## 1. DigitalOcean's agentic AI stack (speak their language)

DO's AI product is the **Gradient AI Platform** ([docs](https://docs.digitalocean.com/products/gradient-ai-platform/)). Its pieces — worth naming *by name* in your answers:

- **Agents** — model + instructions + knowledge bases + functions + guardrails, deployed behind an API/playground endpoint.
- **Knowledge Bases (RAG)** — files stored in **Spaces**, indexed with **OpenSearch**; you pick the embedding model; sources include S3/Dropbox/web crawl.
- **Function/Tool calling** — model decides when to call external tools; integrates with **DO Functions** (serverless).
- **Agent Routing** — a router agent directs queries to specialized sub-agents.
- **Guardrails** — input/output scanning: sensitive-data, jailbreak, content moderation.
- **Agent Evaluations** — automated test runs with **19 metrics** (factual correctness, instruction adherence, tone, toxicity...); **Workspaces** batch-evaluate multiple agents.
- **Traces & observability** — per-request step timeline: tokens, latency, which KB/tools were hit.
- **Serverless Inference** — direct multi-model API (Anthropic/OpenAI/open-source) without building an agent; **prompt caching** for cost.
- Underneath: GPU Droplets / Bare metal for training & self-hosted inference.

**The meta-insight for your design round:** Gradient IS a system-design answer — "agent platform for people who don't want to run infra." If they ask you to design anything agentic, you're partly designing their product; showing you understand its shape (and its hard parts) is exactly the fit signal they want.

---

## 2. Agentic AI concepts crash course (the additions to doc 01)

### The agent loop
LLM in a while-loop: **observe → reason → act (tool call) → observe result → repeat until done**, bounded by max-iterations/budget. Patterns: ReAct (interleaved reasoning+acting), planner-executor (plan once, execute steps), reflection (self-critique pass). Multi-agent = routing (dispatcher → specialists) or orchestrator-workers. **Senior take: agents are workflows with a probabilistic step inside — all your existing distributed-systems discipline (idempotency, retries, timeouts, state machines) still applies, and matters MORE.**

### Tool / function calling
Model outputs a structured call → *your runtime* executes it → result fed back. Design concerns: JSON-schema validation of arguments; **tool execution is untrusted-input execution** (sandbox it, least-privilege creds, allowlists); timeouts + idempotent tools because the model retries; parallel tool calls; MCP (Model Context Protocol) as the emerging standard for pluggable tools.

### RAG pipeline (two planes)
- **Indexing plane (async, batch):** load docs → chunk (300–1000 tokens, overlap; structure-aware beats fixed-size) → embed → store vectors + text in a vector-capable index (OpenSearch/pgvector/dedicated DB) with metadata for filtering.
- **Query plane (sync, latency-bound):** embed query → **hybrid search** (vector + keyword/BM25) → top-k → **rerank** (cross-encoder) → stuff into prompt with citations → generate, stream via SSE.
- Deep-dive levers interviewers probe: chunking strategy, hybrid vs pure-vector (pure vector misses exact IDs/error codes), reranking cost vs quality, freshness (re-embed on doc change via CDC/queue), evaluation (retrieval recall@k separately from answer quality), multi-tenancy (per-tenant index/namespace + filter enforcement).
- **RAG vs fine-tuning vs long context:** RAG = fresh/private knowledge + citations + cheap updates; fine-tune = style/format/narrow skills, not knowledge injection; long context = simplest but costly and slower. Default: RAG.

### Memory
Short-term = conversation window (summarize/truncate as it grows). Long-term = store facts/preferences (vector or KV store) retrieved like RAG. Session state must live OUTSIDE the model (DB/Redis) — the model is stateless; this is just session management with an LLM attached.

### Serving & inference infra
- **Model gateway** pattern: one internal API over many providers/models → routing (cheap model for easy queries, big model for hard ones), fallbacks on provider outage, per-tenant rate limits + token budgets, centralized keys/audit. (DO's Serverless Inference ≈ this as a product.)
- Latency: **stream tokens (SSE)** so TTFT is the felt latency; cache aggressively — exact-match cache, **prompt caching** (shared prefix), semantic cache (careful: wrong-answer risk).
- Cost: tokens are the unit of COGS. Know rough shape: input cheaper than output; caching prefix cuts repeat cost hugely; batch offline work.
- Capacity: GPU serving = queueing + batching (continuous batching, KV-cache memory limits) — one paragraph of this is plenty at IC4.

### Reliability of probabilistic components
Non-determinism → **evals are your unit tests**: golden datasets, LLM-as-judge (with spot-checked judges), regression gates in CI before prompt/model changes (maps to Gradient's Agent Evaluations + Workspaces). Runtime: schema-validate every structured output, retry-with-feedback on invalid JSON, bounded loops, kill-switch/fallback to deterministic path or human handoff.

### Safety & security (cloud-provider lens)
**Prompt injection is the #1 agentic threat**: retrieved docs / tool results / web pages can carry instructions. Mitigations: treat all retrieved+tool content as data (delimiters, instruction hierarchy), least-privilege tools, human-in-the-loop for irreversible actions, output filtering. Plus: guardrails on input/output (jailbreak, PII, moderation — Gradient's three), tenant isolation for tool execution (Firecracker-style sandboxes), data privacy (whose data trains what — answer: nobody's, contractually).

### Observability for agents
Traces per request: each LLM call (prompt hash, model, tokens, latency, cost), each tool call (args, result, duration), retrieval hits. Metrics: TTFT, tokens/request, cost/tenant, loop-iteration histogram, eval-score trend, guardrail-trigger rate. This is Gradient's "Traces" — mention it.

---

## 3. Most-likely design prompts for THIS role (rehearse #1)

1. **"Design a customer-support agent over our docs"** (RAG + tools + escalation) — worked sketch below.
2. **"Design the agent platform itself"** (multi-tenant Gradient): control plane (agent configs, versions) vs data plane (inference, tool sandbox); per-tenant isolation, quotas, model gateway, KB pipeline, traces. Use the control/data-plane split from doc 02.
3. **"Design an inference gateway"** — multi-model routing, rate limits, caching, fallbacks, streaming.
4. **"Design agent evaluation/testing infrastructure"** — golden sets, judge models, CI gates, drift monitoring.
5. **"Design a tool-execution sandbox for agents"** — untrusted code/action execution, least privilege, audit.

### Worked sketch: support agent over DO docs (the one to know cold)
- **Requirements:** answer product questions with citations; escalate to human when unsure; ~50k queries/day (~0.6 QPS avg, plan 10x peak); p50 TTFT < 1s; hallucinated answers are the top product risk; docs update daily.
- **Entities:** Document, Chunk, Conversation, Message, ToolCall, EvalCase.
- **Indexing plane:** docs repo/webhooks → queue → workers: parse → structure-aware chunk → embed → OpenSearch (vector+BM25, per-product metadata). Re-index on change events; full rebuild = new index + alias swap (blue-green for indexes).
- **Query plane:** API GW (auth, rate limit) → input guardrails → conversation state from Redis/PG → embed query → hybrid search top-40 → rerank to top-6 → prompt (system + citations + history summary) → LLM stream via SSE → output guardrails → persist trace.
- **Tools:** account-status lookup, ticket-creation (human handoff). Tool registry with JSON schemas; execution with per-tool timeout + idempotency; escalate automatically when retrieval confidence low or user asks twice.
- **Deep dives to volunteer:** hallucination control (grounding + citation-required prompting + eval gate + "I don't know" path beats any single trick); freshness (CDC re-embed); cost (prompt caching for the static system prompt + doc-prefix, small-model router for FAQs); multi-turn context growth (summarize old turns); observability (trace every hop, eval-score dashboards, guardrail-trigger alerts).
- **Failure modes:** LLM provider down → fallback model via gateway; OpenSearch degraded → keyword-only mode (degrade, don't die); guardrail service down → fail-closed for output PII filter, fail-open for tone (say the asymmetry out loud — it's a great senior moment).

---

## 4. Ripple effects on the other rounds

- **Build:** "data ingestion & processing" may include an AI step (embed/classify/summarize records; note the pre-installed *image processing libraries* hint). Prepare: an `httpx` client wrapper with timeout/retry/backoff, the API key from env var, and **tests that mock the model call** (never call a live LLM in pytest). If an LLM step is optional, make it a clean service-layer plug-in — and say why: "the probabilistic step is isolated so everything around it stays testable."
- **Behavioral:** add one story about building WITH AI (shipped an LLM feature, built evals, fixed an AI-quality issue) and one crisp POV on "how do you use AI tools in your own workflow?" — you'll be using Claude Code in front of them, which IS the demo. "Why DO" answer upgrade: Gradient = bringing agentic AI to the same audience DO always served — developers/SMBs priced out of hyperscaler complexity; simplicity as the differentiator.
- **Architecture review:** if you used AI heavily, own the workflow: "I set standards in CLAUDE.md, worked plan-first, reviewed every diff, and the tests are the contract" — that's *agentic-AI-native engineering judgment*, precisely what an Agentic AI team wants at IC4.

---

### Sources
- [Gradient AI Platform docs](https://docs.digitalocean.com/products/gradient-ai-platform/) and [feature list](https://docs.digitalocean.com/products/gradient-ai-platform/details/features/) (agents, KBs on Spaces+OpenSearch, guardrail types, routing, 19-metric evaluations, traces, serverless inference)
- [Getting started with the Gradient platform](https://www.digitalocean.com/community/tutorials/getting-started-with-digitalocean-gradient-platform)
- [Gradient ADK on GitHub](https://github.com/digitalocean/gradient-adk) · [DO AI Platform page](https://www.digitalocean.com/products/ai-platform) · [DO on agentic AI](https://www.digitalocean.com/resources/articles/agentic-ai)
- [SiliconANGLE — DO's agentic AI push](https://siliconangle.com/2025/01/22/digitalocean-dives-agentic-ai-creation-making-accessible-every-developer/)

---

# PART 8 — RAPID-FIRE Q&A

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
