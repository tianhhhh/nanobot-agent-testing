"""Timeout and upstream failure tests for chat completions."""

import allure
import pytest

from mocks.mock_scenarios import HTTP_ERROR_TOKEN, STREAM_ABORT_TOKEN, TIMEOUT_TOKEN

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.resilience]


def _payload(content: str, *, stream: bool = False) -> dict:
    return {
        "stream": stream,
        "messages": [{"role": "user", "content": content}],
    }


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("异常与恢复")
@allure.title("模型请求超时后返回网关超时错误")
@allure.severity(allure.severity_level.CRITICAL)
def test_request_timeout_returns_gateway_timeout(api_client) -> None:
    response = api_client.post(
        "/v1/chat/completions",
        json=_payload(TIMEOUT_TOKEN),
        check=False,
    )

    assert response.status_code == 504
    error = response.json()["error"]
    assert "timed out" in error["message"]


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("异常与恢复")
@allure.title("模型服务异常时接口返回 5xx 错误")
@allure.severity(allure.severity_level.CRITICAL)
def test_model_service_failure_returns_a_5xx_error(api_client) -> None:
    response = api_client.post(
        "/v1/chat/completions",
        json=_payload(HTTP_ERROR_TOKEN),
        check=False,
    )

    assert 500 <= response.status_code < 600
    assert "error" in response.json()


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("异常与恢复")
@allure.title("SSE 中途异常时不得返回正常 DONE 标记")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.known_bug
@pytest.mark.xfail(strict=True, reason="BUG-004：SSE 上游异常后仍返回正常 DONE，见 BUGS.md")
def test_interrupted_sse_does_not_emit_normal_done_marker(api_client) -> None:
    lines = list(
        api_client.post_sse(
            "/v1/chat/completions",
            json=_payload(STREAM_ABORT_TOKEN, stream=True),
        )
    )

    assert "data: [DONE]" not in lines
