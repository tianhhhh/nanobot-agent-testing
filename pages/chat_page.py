"""Operations on nanobot's chat page."""

from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, Page, expect


class ChatPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    @property
    def composer(self) -> Locator:
        return self.page.get_by_role("textbox", name=re.compile(r"消息输入框|发送消息"))

    @property
    def message_region(self) -> Locator:
        return self.page.get_by_test_id("thread-message-region")

    @property
    def send_button(self) -> Locator:
        return self.page.get_by_role("button", name="发送消息", exact=True)

    @property
    def stop_button(self) -> Locator:
        return self.page.get_by_role("button", name="停止响应", exact=True)

    @allure.step("打开新会话")
    def open_new_chat(self) -> None:
        self.page.goto(f"{self.base_url}/#/")
        expect(self.composer).to_be_visible(timeout=20_000)
        expect(self.composer).to_be_enabled(timeout=20_000)

    def send_message(self, text: str) -> None:
        with allure.step("发送聊天消息"):
            self.composer.fill(text)
            self.composer.press("Enter")
            expect(self.message_region.get_by_text(text, exact=True).first).to_be_visible(
                timeout=15_000
            )

    @allure.step("等待回复包含：{expected_text}")
    def wait_for_reply(self, expected_text: str) -> None:
        expect(self.message_region).to_contain_text(expected_text, timeout=30_000)
        expect(self.stop_button).to_be_hidden(timeout=30_000)

    @allure.step("等待进入流式响应状态")
    def wait_until_streaming(self) -> None:
        expect(self.stop_button).to_be_visible(timeout=15_000)

    @allure.step("等待流式响应包含：{expected_text}")
    def wait_for_partial_reply(self, expected_text: str) -> None:
        """Wait until the model has emitted content while the turn is still active."""
        expect(self.message_region).to_contain_text(expected_text, timeout=15_000)
        expect(self.stop_button).to_be_visible()

    @allure.step("停止当前响应")
    def stop_response(self) -> None:
        self.stop_button.click()
        expect(self.stop_button).to_be_hidden(timeout=15_000)
        expect(self.composer).to_be_enabled()

    @allure.step("输入包含换行的消息")
    def enter_multiline_message(self, first_line: str, second_line: str) -> str:
        """Compose two lines without sending, then return the expected value."""
        expected = f"{first_line}\n{second_line}"
        self.composer.fill(first_line)
        self.composer.press("Shift+Enter")
        self.composer.type(second_line)
        expect(self.composer).to_have_value(expected)
        return expected
