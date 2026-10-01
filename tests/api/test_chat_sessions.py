"""Conversation isolation and concurrency tests for chat completions."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import allure
import pytest

from mocks.mock_scenarios import CONTEXT_TOKEN
from utils.api_client import ApiClient

pytestmark = pytest.mark.api


def _chat(client: ApiClient, session_id: str, content: str) -> str:
    response = client.post(
        "/v1/chat/completions",
        json={
            "session_id": session_id,
            "messages": [{"role": "user", "content": content}],
        },
    )
    return response.json()["choices"][0]["message"]["content"]


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("会话隔离与并发")
@allure.title("session_id 能够隔离不同会话的历史上下文")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_session_id_keeps_conversation_history_isolated(api_client) -> None:
    session_a = f"isolation-a-{uuid4().hex}"
    session_b = f"isolation-b-{uuid4().hex}"
    secret_a = f"secret-a-{uuid4().hex}"
    secret_b = f"secret-b-{uuid4().hex}"

    _chat(api_client, session_a, secret_a)
    _chat(api_client, session_b, secret_b)
    context_a = _chat(api_client, session_a, CONTEXT_TOKEN)
    context_b = _chat(api_client, session_b, CONTEXT_TOKEN)

    assert secret_a in context_a
    assert secret_b not in context_a
    assert secret_b in context_b
    assert secret_a not in context_b


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("会话隔离与并发")
@allure.title("多个并发会话之间不会泄露上下文")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.concurrency
def test_concurrent_sessions_do_not_leak_context(api_client) -> None:
    cases = [
        (f"parallel-{index}-{uuid4().hex}", f"private-{index}-{uuid4().hex}")
        for index in range(4)
    ]

    def exercise(case: tuple[str, str]) -> tuple[str, str]:
        session_id, secret = case
        client = ApiClient(api_client.base_url, token="nanobot-mvp-test-key")
        try:
            _chat(client, session_id, secret)
            return secret, _chat(client, session_id, CONTEXT_TOKEN)
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = list(executor.map(exercise, cases))

    all_secrets = {secret for secret, _ in results}
    for own_secret, context in results:
        assert own_secret in context
        assert all(secret not in context for secret in all_secrets - {own_secret})
