"""AI/LLM integration — the ONE place the app touches a model.

Isolating the probabilistic step behind this module keeps everything else
deterministic and testable: routes and services call `complete()` (or
`classify()`), and tests monkeypatch it — no live model calls in pytest, ever.

DigitalOcean Serverless Inference is OpenAI-compatible:
    POST {APP_INFERENCE_URL}/api/v1/chat/completions
    Authorization: Bearer <Model Access Key>   (NOT the doctl API token)

Env vars (see core/config.py): APP_INFERENCE_URL, APP_MODEL_ACCESS_KEY,
APP_MODEL (default: cheap fast tier; premium model is a config swap).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
_MAX_ATTEMPTS = 3  # 1 try + 2 retries with backoff


class AIError(RuntimeError):
    """Raised when the model call fails after retries — callers decide the
    fallback (degrade, queue for later, or surface a clean 502)."""


async def complete(messages: list[dict[str, str]], *, temperature: float = 0.0) -> str:
    """One chat completion. temperature=0 → deterministic, testable behavior.

    Retries on transport errors and 429/5xx with exponential backoff.
    """
    settings = get_settings()
    payload = {
        "model": settings.model,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {settings.model_access_key}"}
    url = f"{settings.inference_url}/api/v1/chat/completions"

    last_err: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise AIError(f"retryable status {resp.status_code}")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (httpx.TransportError, AIError) as err:
            last_err = err
            if attempt < _MAX_ATTEMPTS:
                delay = 0.5 * 2 ** (attempt - 1)  # 0.5s, 1s
                logger.warning(
                    "model call failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt, _MAX_ATTEMPTS, delay, err,
                )
                await asyncio.sleep(delay)
    raise AIError(f"model call failed after {_MAX_ATTEMPTS} attempts") from last_err


async def classify(text: str, labels: list[str]) -> str:
    """Example structured task: constrain the output, then VALIDATE it.
    On invalid output, retry once with the error appended — then fail cleanly.
    """
    prompt = (
        f"Classify the following text into exactly one label from {labels}. "
        f"Reply with ONLY the label, nothing else.\n\nText: {text}"
    )
    answer = (await complete([{"role": "user", "content": prompt}])).strip()
    if answer in labels:
        return answer
    # one corrective retry: feed the mistake back
    retry_prompt = (
        f"{prompt}\n\nYour previous reply {answer!r} was not one of {labels}. "
        f"Reply with only a valid label."
    )
    answer = (await complete([{"role": "user", "content": retry_prompt}])).strip()
    if answer in labels:
        return answer
    raise AIError(f"model returned invalid label {answer!r} twice")
