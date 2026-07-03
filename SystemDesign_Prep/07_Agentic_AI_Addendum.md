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
