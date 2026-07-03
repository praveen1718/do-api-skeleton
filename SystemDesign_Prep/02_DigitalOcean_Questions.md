# Previously Asked DigitalOcean System Design Questions (+ what to expect)

## A. Verified reports from candidates

These are the design questions publicly reported by DigitalOcean candidates (Interview Query's DO guide, LeetCode Discuss, Glassdoor reports — note Glassdoor pages block scraping, so treat individual reports as directional):

1. **Design a URL shortener** — the classic, reported in DO software-engineer interviews. At senior level they push on: ID generation at scale, redirect latency (cache/CDN), analytics ingestion, and hot-link handling. *(Worked example #1 in `03_Worked_Examples.md`.)*
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
