# Day-Of Playbook — Build Exercise (3h)

## 0. First 15 minutes, in order

1. Sign into GitHub (`gh auth login`) and Claude (`/login` in Claude Code panel or `claude` in terminal). Verify Cursor's built-in AI responds (Cmd+L).
2. `git init` the repo (or clone the one they give you). Recreate the skeleton (see kickoff prompt below).
3. Drop in `CLAUDE.md` + `.cursorrules` (same content — one file for Claude Code, one for Cursor's AI). Get it from your GitHub prep repo or retype the short version.
4. `make run` + `curl /health` — prove the walking skeleton works BEFORE writing features.
5. Start the DO deploy early (`doctl auth init`, `doctl apps create --spec .do/app.yaml`) — App Platform builds take minutes; kicking off deploy #1 at minute 30 beats discovering deploy problems at hour 2:45.

## 1. The kickoff prompt (fill the blanks from their requirements)

Paste this into Claude Code (plan mode ON) after `git init`:

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

TASK — first iteration only:
Create the full project skeleton with ALL of the above standards wired in, and
implement ONLY the single most core requirement end-to-end (one endpoint working
with tests). Leave the remaining requirements as clearly named TODO stubs.
Also write a CLAUDE.md capturing these standards and the make commands.
Show me the plan first; after I approve, generate the code, then run
`make lint && make test` and show results.
```

Why "first iteration only": see §2.

## 2. One-shot the whole repo, or iterate? — Iterate, deliberately

One-shot generation is tempting with upfront requirements, but for an *evaluated* exercise it loses on every axis that matters:

- **You must defend every line in the 40-min Architecture Review.** A 2,000-line one-shot dump means you're reverse-engineering your own repo under questioning. Iterating means you reviewed each diff as it landed — the narrative writes itself.
- **Verification collapses.** One giant change = one giant debugging session when tests fail. Small iterations = `make test` green after each step, always a working commit to fall back to (and Claude Code's rewind works per-message).
- **Requirements drift.** The model over-builds features nobody asked for in one-shots; you burn review time deleting them. (Also hurts the "quality of thought > quantity of features" criterion.)
- **Commit history is evidence.** 8–12 meaningful commits over 3 hours shows engineering process; one "initial commit" with everything shows prompt engineering.

The right compromise is a **big first bite, then loops**: skeleton + standards + ONE core endpoint end-to-end (that's the kickoff prompt), deploy it, then one requirement per prompt: implement → review diff → test → commit → next. Roughly: skeleton+deploy by 0:45, feature loops until 2:15, hardening (edge cases, README, final deploy) 2:15–2:45, buffer 15 min.

## 3. Suggested iteration prompts (after kickoff)

- "Implement requirement 2: <paste>. Follow CLAUDE.md standards. Plan first, then code + tests."
- "Review the whole repo for gaps against these evaluation criteria: production-readiness, error handling, observability, testing. List issues by severity — don't change anything yet."  ← run this at ~2:00, it's a free self-review
- "Write the README: endpoints, how to run/test/deploy, key design decisions and trade-offs, and what I'd do next at scale." ← feeds the Architecture Review directly
- "Generate a .github/workflows/ci.yml that lints, tests, and builds the Docker image."

## 4. CLAUDE.md vs Cursor — who reads what

| File | Read automatically by |
|---|---|
| `CLAUDE.md` | Claude Code (extension panel AND `claude` CLI) |
| `.cursorrules` (or `.cursor/rules/`) | Cursor's built-in AI (Cmd+L / Cmd+K / Composer) |
| `AGENTS.md` | Newer Cursor versions + several other agents; harmless to include |

Keep the content identical (copy-paste). Then it doesn't matter which assistant you're driving — both follow your standards. Committing all three costs nothing.

## 5. Getting your prep notes onto the interview laptop

You can't reach your Mac's files from their laptop, but personal logins are allowed, so:

1. **Best: private GitHub repo.** Push `SystemDesign_Prep/` + `do-api-skeleton/` to a private repo (e.g. `interview-prep`) tonight. On the day: `gh auth login` → `gh repo clone`. You get the skeleton AND the notes in one step, in the environment where you'll work. (Cloning your own reference material is within the "docs + any AI tools are fair game" rules; the skeleton is your own prior work — treat it as reference/starting structure, and be transparent if asked.)
2. **Backup: claude.ai in Chrome.** Your Claude account holds this whole conversation + the generated docs — open claude.ai on the interview laptop and search the session.
3. **Last resort: email yourself** a zip of the prep folder.

Do #1 tonight and smoke-test it: clone the repo on a fresh directory, `make install && make test && make run`.

## 6. Timeline cheat-card

| Clock | Doing |
|---|---|
| 0:00–0:15 | Logins, clone/init, skeleton, CLAUDE.md |
| 0:15–0:30 | Walking skeleton runs locally; adapt schemas to the real data shape |
| 0:30–0:45 | First deploy to DO kicked off; core endpoint #1 done with tests |
| 0:45–2:15 | Feature loops (one requirement per prompt; commit each) |
| 2:15–2:40 | Self-review prompt, fix top issues, README/decisions, final deploy |
| 2:40–3:00 | Buffer: verify deployed URL end-to-end with curl; prep 3 talking points for the review |
