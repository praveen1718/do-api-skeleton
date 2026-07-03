"""Tests for the AI module — demonstrates the mock pattern:
NEVER call a live model from pytest. We monkeypatch `complete` for service
tests, and use respx to fake the HTTP layer when testing `complete` itself.

Requires dev deps: pytest, pytest-asyncio, respx (add to requirements-dev.txt).
"""
import httpx
import pytest
import respx

from app.services import ai

pytestmark = pytest.mark.asyncio


# --- Testing complete() itself: fake the HTTP layer with respx --------------

def _ok_response(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


@respx.mock
async def test_complete_happy_path(monkeypatch):
    monkeypatch.setenv("APP_INFERENCE_URL", "https://inference.test")
    monkeypatch.setenv("APP_MODEL_ACCESS_KEY", "test-key")
    ai.get_settings.cache_clear()

    route = respx.post("https://inference.test/api/v1/chat/completions").mock(
        return_value=_ok_response("hello")
    )
    result = await ai.complete([{"role": "user", "content": "hi"}])
    assert result == "hello"
    assert route.called
    # auth header used the Model Access Key, not the doctl token
    assert route.calls[0].request.headers["authorization"] == "Bearer test-key"


@respx.mock
async def test_complete_retries_on_5xx_then_succeeds(monkeypatch):
    monkeypatch.setenv("APP_INFERENCE_URL", "https://inference.test")
    monkeypatch.setenv("APP_MODEL_ACCESS_KEY", "test-key")
    ai.get_settings.cache_clear()

    respx.post("https://inference.test/api/v1/chat/completions").mock(
        side_effect=[httpx.Response(503), _ok_response("recovered")]
    )
    assert await ai.complete([{"role": "user", "content": "hi"}]) == "recovered"


# --- Testing callers of the AI step: monkeypatch complete() -----------------

async def test_classify_validates_output(monkeypatch):
    async def fake_complete(messages, **kw):
        return "spam"

    monkeypatch.setattr(ai, "complete", fake_complete)
    assert await ai.classify("buy now!!", ["spam", "ham"]) == "spam"


async def test_classify_rejects_bad_label_after_one_retry(monkeypatch):
    async def always_wrong(messages, **kw):
        return "banana"

    monkeypatch.setattr(ai, "complete", always_wrong)
    with pytest.raises(ai.AIError):
        await ai.classify("hello", ["spam", "ham"])
