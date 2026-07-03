# Day-Of Playbook v3 — FINAL (build exercise, 3h)

_v3 changes (after joining Blitz_team10_Hyd + reading DO's RAG blueprint): the kickoff prompt's AI-step standard now carries the exact DO integration details (OpenAI-compatible endpoint, Model Access Key, cheap-model default, temperature 0); first-15-min adds the two-credentials step and team-context check; managed-vs-hand-rolled RAG guidance added; review points add the model-cost-routing observation. Supersedes v2; v1/v2 kept for history._

## 0. First 15 minutes, in order

1. Sign into GitHub (`gh auth login`) and Claude — spark icon in Cursor → browser auth; `/usage` to confirm; check model via `/`.
2. Verify Cursor's built-in AI responds (Cmd+L) — guaranteed fallback.
3. **Credentials — mind the team context.** Confirm the top-right team switcher shows **Blitz_team10_Hyd**, then create:
   - **DO API token** (API → Tokens) → `doctl auth init` (deploys land in the team, where the credits are).
   - **Model Access Key** (Serverless Inference → Create a Model Access Key) → only if the spec has an AI step. The **Model Playground** can generate a working sample request; **Analyze** shows usage.
4. `git clone` your prep repo → copy skeleton; drop in `CLAUDE.md` + `.cursorrules` + `AGENTS.md` (identical content).
5. `make run` + `curl /health` — walking skeleton BEFORE features.
6. Kick off deploy #1 early (`doctl apps create --spec .do/app.yaml`) — App Platform builds take minutes; find deploy problems at 0:30, not 2:45.

## 1. The kickoff prompt (fill blanks from their requirements)

Paste into Claude Code (plan mode ON):

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

IF THE SPEC INCLUDES AN AI/LLM STEP (classification, summarization, extraction,
Q&A, embeddings):
- Isolate it in services/ai.py behind one async function, using httpx with a
  30s timeout and retry-with-backoff. Secrets from env vars only:
  INFERENCE_URL, MODEL_ACCESS_KEY, MODEL.
- DigitalOcean Serverless Inference is OpenAI-compatible:
  POST {INFERENCE_URL}/api/v1/chat/completions with Bearer auth and a
  `messages` array; answer at choices[0].message.content.
- Default to a cheap fast model (e.g. DeepSeek Flash class) with
  temperature=0 for deterministic, testable behavior; note in the README that
  a premium model (Claude Sonnet class) is a config swap for harder inputs —
  and that the ~20-40x price spread is why routing matters.
- MOCK the model call in all tests (monkeypatch/respx) — never call a live
  model from pytest. Validate/parse any structured model output before use;
  on invalid output, retry once with the error appended, then fail cleanly.
- If retrieval over documents is required: prefer the managed Knowledge Base
  (Gradient, region tor1, indexing is ASYNC — poll before use) over
  hand-rolling; only hand-roll a minimal in-memory index if the spec forbids
  managed services or time is short. Cite sources in responses either way.

TASK — first iteration only:
Create the full project skeleton with ALL of the above standards wired in, and
implement ONLY the single most core requirement end-to-end (one endpoint working
with tests). Leave the remaining requirements as clearly named TODO stubs.
Also write a CLAUDE.md capturing these standards and the make commands.
Show me the plan first; after I approve, generate the code, then run
`make lint && make test` and show results.
```

Image-data note: pre-installed image libraries hint the payload may be images — same standard: isolate processing in a service, stream/chunk large files, tiny fixture images in tests, originals to Spaces via presigned URLs if storage is needed.

## 2. One-shot or iterate? — Iterate, deliberately

- **You defend every line in the 40-min review** — iterating means you reviewed each diff as it landed; a one-shot dump means reverse-engineering your own repo under questioning.
- **Verification collapses in one-shots** — small iterations keep `make test` green with a working commit to fall back to (plus per-message rewind).
- **Models over-build in one-shots** — "quality of thought > quantity of features."
- **Commit history is evidence** — 8–12 meaningful commits ≫ one "initial commit."

Big first bite (kickoff prompt: skeleton + standards + ONE core endpoint), deploy it, then one requirement per prompt: implement → review diff → test → commit → next.

## 3. Iteration prompts (after kickoff)

- "Implement requirement 2: <paste>. Follow CLAUDE.md standards. Plan first, then code + tests."
- "Review the whole repo for gaps against: production-readiness, error handling, observability, testing. List issues by severity — change nothing yet." ← run at ~2:00
- "Write the README: endpoints, run/test/deploy, key design decisions and trade-offs, what I'd do next at scale." ← feeds the review
- "Generate .github/workflows/ci.yml: lint, test, build the Docker image."

## 4. CLAUDE.md vs Cursor — who reads what

`CLAUDE.md` → Claude Code (panel + CLI) · `.cursorrules` → Cursor's built-in AI · `AGENTS.md` → newer Cursor + other agents. Identical content, all three committed.

## 5. Prep onto the interview laptop

Push to the private GitHub repo tonight: `SystemDesign_Prep/` (incl. `00_MASTER_Prep.md`, `09_Lunch_Card.md`, `10_RAG_Blueprint_Notes.md`), `do-api-skeleton/`, `go-ingest/`, `rag-demo/`. On the day: `gh auth login` → clone. Backup: claude.ai in Chrome (this conversation). Smoke-test the clone tonight: `make install && make test && make run`.

## 6. Architecture Review — four things ready

1. **Positioning line:** "I come from backend/distributed systems, and agentic AI is where that discipline matters most — an agent is a workflow with a probabilistic step inside, so idempotency, retries, and observability become the product."
2. **Own the AI workflow:** "Standards in CLAUDE.md up front, plan-first, every diff reviewed, tests are the contract."
3. **Scale story for YOUR build:** what breaks first (in-memory → Postgres; sync → queue + workers; single instance → horizontal + rate limiting), with rough numbers.
4. **Cost story if you used the AI step:** "I defaulted to a Flash-class model at temperature 0; the catalog shows a 20–40x price spread to Sonnet-class, so model routing is the cost architecture — easy inputs stay cheap, hard ones escalate."

## 7. Timeline cheat-card

| Clock | Doing |
|---|---|
| 0:00–0:15 | Logins, **both credentials (team context!)**, clone, skeleton, CLAUDE.md |
| 0:15–0:30 | Walking skeleton runs; adapt schemas to the real data shape |
| 0:30–0:45 | Deploy #1 kicked off; core endpoint #1 done with tests |
| 0:45–2:15 | Feature loops (one requirement per prompt; commit each) |
| 2:15–2:40 | Self-review prompt, fix top issues, README/decisions, final deploy |
| 2:40–3:00 | Buffer: curl the deployed URL end-to-end; prep review talking points |
