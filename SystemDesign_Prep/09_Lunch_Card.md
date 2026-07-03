# LUNCH CARD — the only thing to read in the last 10 minutes

_(Everything here is from Parts 1, 6, 7 — pre-triaged. Do NOT open the master doc at lunch.)_

## 1. The 45-min design round skeleton (~1 min)

Functional reqs (top 3, ask like a PM) → NFRs (quantified; name **the defining challenge**) → entities → API → high-level design (simple first, walk each endpoint) → **deep dives on the 2 hardest problems — you drive**.

Product flavor: name 2–3 user personas first · MVP vs v2 · say what you're NOT building · "how do we know users are happy?"

## 2. Phrases to say out loud (~2 min)

- "The defining challenge of this system is ___, so I'll spend my deep-dive time there."
- "Simplest thing that satisfies the requirement first; then harden it."
- "At-least-once delivery, so consumers are idempotent — here's the key."
- "Availability over consistency here, because a stale read costs ___, downtime costs ___."
- "This fits in one Postgres at 500 writes/s; sharding now is premature — here's the migration path."
- "How does this fail? Queue down → ___; worker dies mid-task → visibility timeout + idempotent retry."
- **Positioning line:** "An agent is a workflow with a probabilistic step inside — idempotency, retries, sandboxing, observability stop being nice-to-haves and become the product."

## 3. RAG support-agent sketch — the likely prompt (~4 min)

**Two planes.** Indexing (async): docs → queue → chunk (structure-aware, overlap) → embed → OpenSearch (vector + BM25, per-tenant metadata); re-embed on change; alias-swap for rebuilds.
**Query (sync):** gateway (auth/rate limit) → input guardrails → embed query → hybrid search top-40 → rerank to top-6 → prompt with citations + summarized history → **stream via SSE** → output guardrails → trace everything.

**Deep dives to volunteer:** hallucination = grounding rule ("answer only from context, cite, else say I-don't-know") + relevance floor + refusal/escalation path + eval gate. Cost = prompt caching + small-model router. Failure asymmetry: PII filter **fail-closed**, tone filter **fail-open** — say it.
**Gradient names to drop:** Knowledge Bases (Spaces + OpenSearch), Serverless Inference, Guardrails (sensitive-data / jailbreak / moderation), Agent Routing, Evaluations (19 metrics), Traces.
**Your hands-on story:** "I built a tiny RAG pipeline this week — off-topic questions confidently matched on stopwords until I added a relevance floor and a refusal path. Tiny-scale proof that retrieval quality and refusal thresholds ARE the design."

## 4. Behavioral — story names only (~1 min)

1. Influence without authority: ______  2. Ambiguity: ______  3. Mentoring: ______
4. Disagreement + data: ______  5. Failure I owned + guardrail I built: ______
(+ AI story: LangChain schema-diff / repo-review at Grab — "LLM for the fuzzy middle, determinism and validation around it.")

STAR discipline: Situation ≤2 sentences · Action = 60%, say "I" · one decision against the easy alternative · quantified result · **stop talking at 2.5 min**.

Why DO: Gradient brings agentic AI to the developers/SMBs the hyperscalers overcomplicate — simplicity is the moat. Questions for them: how do you measure operational excellence · what separates good from great IC4 here · current scaling challenge on your product.

## 5. Then close the doc, breathe, and go.
