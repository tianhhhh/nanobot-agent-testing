"""Browser tests for core chat interactions."""

from uuid import uuid4

import allure
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui
MOCK_REPLY = "你好！我是 mock 回复"


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("基础对话")
@allure.title("新建会话后能够收到模型回复")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
def test_new_chat_shows_mock_reply(chat_page) -> None:
    chat_page.open_new_chat()
    message = f"MVP-普通对话-{uuid4().hex[:8]}"
    chat_page.send_message(message)
    chat_page.wait_for_reply(MOCK_REPLY)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("消息输入校验")
@allure.title("空白消息不能发送")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_blank_message_cannot_be_sent(chat_page) -> None:
    chat_page.open_new_chat()
    expect(chat_page.send_button).to_be_disabled()

    chat_page.composer.fill("   ")
    expect(chat_page.send_button).to_be_disabled()
    chat_page.composer.press("Enter")

    expect(chat_page.composer).to_have_value("   ")
    expect(chat_page.page.get_by_test_id("thread-welcome-layout")).to_be_visible()


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("消息输入校验")
@allure.title("超过 64 KiB 的消息会被拒绝并显示提示")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_text_over_64_kib_is_rejected_with_a_clear_message(chat_page) -> None:
    chat_page.open_new_chat()
    chat_page.composer.fill("a" * (64 * 1024 + 1))

    chat_page.composer.press("Enter")

    expect(chat_page.page.get_by_role("alert")).to_contain_text("消息文本过大")
    expect(chat_page.page.get_by_test_id("thread-welcome-layout")).to_be_visible()


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("基础对话")
@allure.title("Shift+Enter 换行且 Enter 发送消息")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_shift_enter_adds_newline_and_enter_sends(chat_page) -> None:
    chat_page.open_new_chat()
    first_line = f"MVP-第一行-{uuid4().hex[:8]}"
    second_line = "MVP-第二行"
    expected = chat_page.enter_multiline_message(first_line, second_line)

    expect(chat_page.page.get_by_text(first_line, exact=True)).to_have_count(0)
    chat_page.composer.press("Enter")

    expect(chat_page.message_region).to_contain_text(first_line)
    expect(chat_page.message_region).to_contain_text(second_line)
    chat_page.wait_for_reply(MOCK_REPLY)
    assert "\n" in expected


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("基础对话")
@allure.title("多轮对话中的用户消息保持发送顺序")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_multiple_turns_keep_user_messages_in_order(chat_page) -> None:
    chat_page.open_new_chat()
    first = f"MVP-第一轮-{uuid4().hex[:8]}"
    second = f"MVP-第二轮-{uuid4().hex[:8]}"

    chat_page.send_message(first)
    chat_page.wait_for_reply(MOCK_REPLY)
    chat_page.send_message(second)
    chat_page.wait_for_reply(MOCK_REPLY)

    timeline = chat_page.message_region.inner_text()
    assert timeline.index(first) < timeline.index(second)
