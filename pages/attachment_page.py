"""Operations for files attached in the chat composer."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import allure
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
        with allure.step(f"选择附件：{path.name}"):
            self.file_input.set_input_files(str(path))
            expect(self.chips).to_have_count(1)
            # 图片会在浏览器 Worker 中编码。卡片先出现，发送按钮稍后才可用。
            expect(self.page.get_by_role("button", name="发送消息", exact=True)).to_be_enabled(
                timeout=15_000
            )

    def attach_in_memory(self, files: list[dict[str, Any]]) -> None:
        with allure.step(f"选择 {len(files)} 个内存附件"):
            self.select_in_memory(files)
            expect(self.chips).to_have_count(len(files))

    def paste_path(self, target: Locator, path: Path, mime_type: str) -> None:
        with allure.step(f"粘贴附件：{path.name}"):
            self._dispatch_file_event(target, path, mime_type, "paste")

    def drop_path(self, target: Locator, path: Path, mime_type: str) -> None:
        with allure.step(f"拖放附件：{path.name}"):
            self._dispatch_file_event(target, path, mime_type, "drop")

    def _dispatch_file_event(
        self, target: Locator, path: Path, mime_type: str, event_name: str
    ) -> None:
        payload = {
            "name": path.name,
            "mimeType": mime_type,
            "base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            "eventName": event_name,
        }
        target.evaluate(
            """
            (element, payload) => {
              const binary = atob(payload.base64);
              const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
              const file = new File([bytes], payload.name, { type: payload.mimeType });
              const transfer = new DataTransfer();
              transfer.items.add(file);
              const event = payload.eventName === 'paste'
                ? new ClipboardEvent('paste', {
                    bubbles: true,
                    cancelable: true,
                    clipboardData: transfer,
                  })
                : new DragEvent('drop', {
                    bubbles: true,
                    cancelable: true,
                    dataTransfer: transfer,
                  });
              element.dispatchEvent(event);
            }
            """,
            payload,
        )
        expect(self.chips).to_have_count(1)

    def select_in_memory(self, files: list[dict[str, Any]]) -> None:
        """Select synthetic files without assuming how many will be accepted."""
        with allure.step(f"提交 {len(files)} 个附件并等待前端校验"):
            self.file_input.set_input_files(files)

    def names(self) -> list[str]:
        return [self.chips.nth(index).inner_text() for index in range(self.chips.count())]

    @allure.step("移除第一个附件")
    def remove_first(self) -> None:
        self.chips.first.get_by_role("button", name="移除附件", exact=True).click()
        expect(self.chips).to_have_count(0)

    @allure.step("将第一个附件拖到末尾")
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
