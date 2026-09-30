"""Four black-box smoke tests for nanobot's OpenAI-compatible API."""

import json

import pytest


pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_health_returns_ok(api_client) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_models_returns_configured_model(api_client) -> None:
    body = api_client.get("/v1/models").json()
    assert body["object"] == "list"
    assert body["data"][0]["id"] == "mock-model"


def test_chat_returns_json_reply(api_client) -> None:
    response = api_client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "API 普通对话"}]},
    )
    body = response.json()
    assert body["object"] == "chat.completion"
    assert "你好！我是 mock 回复" in body["choices"][0]["message"]["content"]


def test_chat_stream_ends_with_done(api_client) -> None:
    lines = list(
        api_client.post_sse(
            "/v1/chat/completions",
            json={
                "stream": True,
                "messages": [{"role": "user", "content": "API 流式对话"}],
            },
        )
    )
    assert lines[-1] == "data: [DONE]"
    chunks = [json.loads(line.removeprefix("data: ")) for line in lines[:-1]]
    assert any(chunk.get("choices") for chunk in chunks)

