"""Operations for persisted chats in the WebUI sidebar."""

from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, Page, expect


class SessionPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def sidebar(self) -> Locator:
        return self.page.get_by_role("navigation", name="侧边栏导航")

    @property
    def active_row(self) -> Locator:
        return self.sidebar.locator(
            '[data-chat-row]:has(button[aria-current="page"])'
        )

    def wait_for_active_chat(self) -> None:
        expect(self.active_row).to_be_visible(timeout=20_000)

    def _open_actions(self, row: Locator) -> None:
        menu = self.page.get_by_role("menu")
        expect(menu).to_be_hidden()
        trigger = row.get_by_role("button", name=re.compile(r"话题操作$"))
        trigger.hover()
        trigger.click()
        expect(menu).to_be_visible()

    def _expand_collapsed_chats(self) -> None:
        collapsed = self.sidebar.get_by_role(
            "button", name=re.compile(r"已折叠 \d+ 个话题")
        )
        if collapsed.count() > 0 and collapsed.is_visible():
            collapsed.click()

    def handle_for_title(self, title: str) -> str:
        row_button = self.sidebar.get_by_role("button", name=re.compile(re.escape(title))).first
        expect(row_button).to_be_visible()
        label = row_button.get_attribute("aria-label") or row_button.inner_text()
        match = re.search(r"@([\w-]+)", label)
        if match is None:
            raise AssertionError(f"无法从会话标签中提取 @handle：{label}")
        return match.group(1)

    @allure.step("重命名当前会话为：{new_title}")
    def rename_active_chat(self, new_title: str) -> None:
        self.wait_for_active_chat()
        self._open_actions(self.active_row)
        self.page.get_by_role("menuitem", name="重命名", exact=True).click()

        dialog = self.page.get_by_role("dialog", name="重命名话题")
        dialog.get_by_placeholder("话题名称").fill(new_title)
        dialog.get_by_role("button", name="保存", exact=True).click()

        expect(self.active_row.get_by_text(new_title, exact=True)).to_be_visible()

    @allure.step("置顶当前会话")
    def pin_active_chat(self) -> None:
        self.wait_for_active_chat()
        self._open_actions(self.active_row)
        self.page.get_by_role("menuitem", name="置顶", exact=True).click()
        expect(self.page.get_by_role("menu")).to_be_hidden()
        expect(self.active_row.locator("[data-sidebar-pinned-indicator]")).to_have_count(1)

    @allure.step("取消置顶当前会话")
    def unpin_active_chat(self) -> None:
        self._open_actions(self.active_row)
        unpin = self.page.get_by_role("menuitem", name="取消置顶", exact=True)
        expect(unpin).to_be_visible()
        unpin.click()
        expect(self.active_row.locator("[data-sidebar-pinned-indicator]")).to_have_count(0)

    @allure.step("归档当前会话：{title}")
    def archive_active_chat(self, title: str) -> None:
        self._open_actions(self.active_row)
        self.page.get_by_role("menuitem", name="归档", exact=True).click()
        expect(self.page.get_by_role("menu")).to_be_hidden()

        show_archived = self.sidebar.get_by_role("button", name="显示归档", exact=True)
        expect(show_archived).to_be_visible()
        show_archived.click()

        expect(self.sidebar.get_by_role("button", name="隐藏归档", exact=True)).to_be_visible()
        self._expand_collapsed_chats()
        expect(self.sidebar.get_by_text(title, exact=True)).to_be_visible()

    @allure.step("恢复归档会话：{title}")
    def unarchive_chat(self, title: str) -> None:
        row = self.sidebar.locator("[data-chat-row]").filter(has_text=title)
        self._open_actions(row)
        self.page.get_by_role("menuitem", name="取消归档", exact=True).click()

        expect(self.sidebar.get_by_text(title, exact=True)).to_be_visible()
        self._open_actions(row)
        expect(self.page.get_by_role("menuitem", name="归档", exact=True)).to_be_visible()
        self.page.keyboard.press("Escape")

    @allure.step("搜索并打开会话：{title}")
    def search_and_open_chat(self, title: str) -> None:
        self.sidebar.get_by_role("button", name="搜索", exact=True).click()
        dialog = self.page.get_by_role("dialog", name="搜索")
        search_input = dialog.get_by_role("textbox", name="搜索", exact=True)
        expect(search_input).to_be_focused()
        search_input.fill(title)

        result = dialog.get_by_role("button").filter(has_text=title)
        expect(result).to_have_count(1)
        result.click()
        expect(dialog).to_be_hidden()
        expect(self.active_row.get_by_text(title, exact=True)).to_be_visible()
