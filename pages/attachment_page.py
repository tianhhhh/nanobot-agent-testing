"""Operations for files attached in the chat composer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, expect


class AttachmentPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def file_input(self) -> Locator:
        return self.page.locator('input[type="file"]')

    @property
    def chips(self) -> Locator:
        return self.page.get_by_test_id("composer-chip")

    def attach_path(self, path: Path) -> None:
        self.file_input.set_input_files(str(path))
        expect(self.chips).to_have_count(1)
        # 图片会在浏览器 Worker 中编码。卡片先出现，发送按钮稍后才可用。
        expect(self.page.get_by_role("button", name="发送消息", exact=True)).to_be_enabled(
            timeout=15_000
        )

    def attach_in_memory(self, files: list[dict[str, Any]]) -> None:
        self.file_input.set_input_files(files)
        expect(self.chips).to_have_count(len(files))

    def names(self) -> list[str]:
        return [self.chips.nth(index).inner_text() for index in range(self.chips.count())]

    def drag_first_to_last(self) -> None:
        first = self.chips.first
        last = self.chips.last
        target = last.bounding_box()
        if target is None:
            raise AssertionError("无法获取最后一个附件的位置")
        first.hover()
        self.page.mouse.down()
        self.page.mouse.move(
            target["x"] + target["width"] / 2,
            target["y"] + target["height"] / 2,
            steps=10,
        )
        self.page.mouse.up()
