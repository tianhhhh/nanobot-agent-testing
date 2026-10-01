"""Browser tests for session-scoped model commands."""

import allure
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.regression]


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("模型切换")
@allure.title("model 命令能够切换当前会话的模型预设")
@allure.severity(allure.severity_level.CRITICAL)
def test_model_command_switches_the_current_session_preset(chat_page) -> None:
    chat_page.open_new_chat()

    chat_page.composer.fill("/model Mock B")
    chat_page.composer.press("Enter")

    expect(chat_page.page.get_by_role("button", name="Mock B", exact=True)).to_be_visible(
        timeout=20_000
    )
