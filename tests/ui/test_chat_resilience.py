"""Browser tests for streaming state, interruption, and recovery."""

from uuid import uuid4

import allure
import pytest
from playwright.sync_api import expect

from mocks.mock_scenarios import SLOW_STREAM_TOKEN, STREAM_ABORT_TOKEN

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.resilience]
MOCK_REPLY = "你好！我是 mock 回复"


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("流式交互与恢复")
@allure.title("发送过程中发送按钮切换为停止响应按钮")
@allure.severity(allure.severity_level.CRITICAL)
def test_sending_state_replaces_send_with_stop_control(chat_page) -> None:
    chat_page.open_new_chat()

    chat_page.send_message(f"{SLOW_STREAM_TOKEN}-{uuid4().hex[:8]}")

    chat_page.wait_until_streaming()
    expect(chat_page.send_button).to_be_hidden()
    expect(chat_page.composer).to_be_enabled()
    chat_page.stop_response()


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("流式交互与恢复")
@allure.title("停止慢速响应后能够继续下一轮对话")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.known_bug
@pytest.mark.xfail(strict=True, reason="BUG-005：停止响应未可靠取消后台生成，见 BUGS.md")
def test_stop_response_terminates_slow_stream_and_allows_next_turn(chat_page) -> None:
    chat_page.open_new_chat()
    chat_page.send_message(f"{SLOW_STREAM_TOKEN}-{uuid4().hex[:8]}")
    chat_page.wait_until_streaming()

    chat_page.stop_response()
    follow_up = f"停止后继续-{uuid4().hex[:8]}"
    chat_page.send_message(follow_up)

    chat_page.wait_for_reply(MOCK_REPLY, timeout=10_000)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("流式交互与恢复")
@allure.title("流式响应异常后页面仍可继续对话")
@allure.severity(allure.severity_level.CRITICAL)
def test_page_can_continue_after_streaming_failure(chat_page) -> None:
    chat_page.open_new_chat()
    chat_page.send_message(f"{STREAM_ABORT_TOKEN}-{uuid4().hex[:8]}")
    chat_page.wait_until_streaming()
    expect(chat_page.stop_button).to_be_hidden(timeout=30_000)

    follow_up = f"异常后继续-{uuid4().hex[:8]}"
    chat_page.send_message(follow_up)

    chat_page.wait_for_reply(MOCK_REPLY)
