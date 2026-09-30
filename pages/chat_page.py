"""Operations on nanobot's chat page."""

from __future__ import annotations

import re

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

    def open_new_chat(self) -> None:
        self.page.goto(f"{self.base_url}/#/")
        expect(self.composer).to_be_visible(timeout=20_000)
        expect(self.composer).to_be_enabled(timeout=20_000)

    def send_message(self, text: str) -> None:
        self.composer.fill(text)
        self.composer.press("Enter")
        expect(self.message_region.get_by_text(text, exact=True).first).to_be_visible(
            timeout=15_000
        )

    def wait_for_reply(self, expected_text: str) -> None:
        expect(self.message_region).to_contain_text(expected_text, timeout=30_000)
        expect(self.page.get_by_role("button", name="停止响应", exact=True)).to_be_hidden(
            timeout=30_000
        )

