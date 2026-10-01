"""Black-box tests for text chat completions."""

import json

import allure
import pytest

pytestmark = pytest.mark.api


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("Chat Completions")
@allure.title("正常请求能够完成非流式对话")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
def test_chat_returns_json_reply(api_client) -> None:
    response = api_client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "API 普通对话"}]},
    )
    body = response.json()

    assert body["object"] == "chat.completion"
    assert "你好！我是 mock 回复" in body["choices"][0]["message"]["content"]


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("Chat Completions")
@allure.title("流式对话返回完整 SSE 并以 DONE 结束")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
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
    assert chunks
    assert {chunk["id"] for chunk in chunks} == {chunks[0]["id"]}
    assert all(chunk["object"] == "chat.completion.chunk" for chunk in chunks)
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    streamed_text = "".join(
        chunk["choices"][0]["delta"].get("content", "") for chunk in chunks
    )
    assert "你好！我是 mock 回复" in streamed_text


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("请求校验")
@allure.title("不支持的消息结构返回 400：{param_id}")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "Only a single user message is supported"),
        ({"messages": []}, "Only a single user message is supported"),
        (
            {"messages": [{"role": "system", "content": "system prompt"}]},
            "Only a single user message is supported",
        ),
        (
            {
                "messages": [
                    {"role": "user", "content": "first"},
                    {"role": "user", "content": "second"},
                ]
            },
            "Only a single user message is supported",
        ),
    ],
)
def test_chat_rejects_unsupported_message_shapes(api_client, payload: dict, message: str) -> None:
    response = api_client.post("/v1/chat/completions", json=payload, check=False)

    assert response.status_code == 400
    error = response.json()["error"]
    assert error == {
        "message": message,
        "type": "invalid_request_error",
        "code": 400,
    }


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("请求校验")
@allure.title("请求未配置的模型时返回 400")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_chat_rejects_a_model_other_than_the_configured_model(api_client) -> None:
    response = api_client.post(
        "/v1/chat/completions",
        json={
            "model": "model-that-is-not-configured",
            "messages": [{"role": "user", "content": "hello"}],
        },
        check=False,
    )

    assert response.status_code == 400
    error = response.json()["error"]
    assert "mock-model" in error["message"]
    assert error["type"] == "invalid_request_error"


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("请求校验")
@allure.title("非法 JSON 请求返回 400")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_chat_rejects_malformed_json(api_client) -> None:
    response = api_client.post_raw(
        "/v1/chat/completions",
        body=b'{"messages": [',
        content_type="application/json",
        check=False,
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Invalid JSON body"


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("请求校验")
@allure.title("错误 Content-Type 的 JSON 请求应被拒绝")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
@pytest.mark.known_bug
@pytest.mark.xfail(strict=True, reason="BUG-004：接口未拒绝错误的 Content-Type，见 BUGS.md")
def test_chat_rejects_json_sent_with_an_unsupported_content_type(api_client) -> None:
    response = api_client.post_raw(
        "/v1/chat/completions",
        body='{"messages":[{"role":"user","content":"hello"}]}',
        content_type="text/plain",
        check=False,
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Invalid JSON body"


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("请求校验")
@allure.title("不支持的 HTTP 方法返回 405：{method}")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE"])
def test_chat_rejects_unsupported_http_methods(api_client, method: str) -> None:
    response = api_client.request(method, "/v1/chat/completions", check=False)

    assert response.status_code == 405
    assert "POST" in response.headers["Allow"]
