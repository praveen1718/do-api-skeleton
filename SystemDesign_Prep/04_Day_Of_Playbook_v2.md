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
