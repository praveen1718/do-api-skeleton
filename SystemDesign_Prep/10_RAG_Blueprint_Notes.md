# DO RAG Blueprint + Console Recon — Build-Day Cheat Notes

_Source: [digitalocean/marketplace-blueprints/blueprints/rag-assistant](https://github.com/digitalocean/marketplace-blueprints/tree/master/blueprints/rag-assistant) + Blitz_team10_Hyd console (Jul 3)._

## The reference architecture (DO's own RAG starter kit)
Chat UI (FastAPI on App Platform) → managed Agent endpoint → guardrails (in/out) → Knowledge Base semantic search (Qwen3-0.6B embeddings by default) → serverless inference model → response with citations.

## The integration pattern (memorize)
- Agent/Inference API is **OpenAI-compatible**: `POST {deployment_url}/api/v1/chat/completions`, Bearer auth, `messages=[{role, content}]`, answer in `choices[0].message.content`.
- Their chat-ui = FastAPI: `GET /health`, `POST /api/chat` proxying with httpx, 120s timeout, 503 if agent not ready, creds as SECRET env vars (`AGENT_UUID`, `DO_API_TOKEN`). Same shape as my skeleton.

## Two credentials on the day
1. **DO API token** (API → Tokens) → for `doctl auth init` / deploys.
2. **Model Access Key** (Serverless Inference page → "Create a Model Access Key") → for inference API calls.
Playground tab can generate a working example request; Analyze tab shows usage.

## Model catalog (as seen in team console)
- DeepSeek V4 Flash: $0.11/M in, $0.22/M out (cheap tier)
- GLM-5.1: $0.97/$4.30 · GLM-5.2: $1.05/$4.40 — "Inference, Reasoning, Tool Calling"
- Anthropic Claude Sonnet 5: $2.00/$10.00 (premium tier)
→ ~20–45x cost spread = model-routing deep-dive material: "route easy queries cheap, escalate hard ones; routing IS the cost architecture." Serverless vs Dedicated availability per model.

## Agent config vocabulary (from their Terraform)
`temperature=0` (deterministic) · `k=5` retrieved chunks · `provide_citations=true` · retrieval method `SUB_QUERIES` (question decomposition before search) · guardrails with priority order: jailbreak(1) → moderation(2) → sensitive-data(3) · KB indexing is ASYNC (they poll for completion before attaching — two-plane RAG confirmed) · GenAI platform region: **tor1 only** (app can live elsewhere).

## If the exercise includes an AI step — 15-line recipe
```python
# services/ai.py — isolate the probabilistic step; mock this in tests
import httpx, os

async def complete(messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{os.environ['INFERENCE_URL']}/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['MODEL_ACCESS_KEY']}"},
            json={"model": os.environ.get("MODEL", "deepseek-4-flash"),
                  "messages": messages, "temperature": 0},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```
Retry/backoff wrapper around it; validate any structured output; never call live in pytest.
