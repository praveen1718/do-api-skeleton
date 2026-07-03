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
