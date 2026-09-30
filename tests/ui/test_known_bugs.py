"""Python versions of the two existing TypeScript regression scenarios."""

from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.known_bug]
MOCK_REPLY = "你好！我是 mock 回复"


def test_refresh_does_not_flash_new_chat_hero(chat_page, page: Page) -> None:
    chat_page.open_new_chat()
    chat_page.send_message(f"MVP-刷新场景-{uuid4().hex[:8]}")
    chat_page.wait_for_reply(MOCK_REPLY)

    hero_seen = {"value": False}
    page.expose_function("markHeroSeen", lambda: hero_seen.__setitem__("value", True))
    page.add_init_script(
        """
        () => {
          const placeholders = ['问任何问题...', 'Ask anything...'];
          const probe = () => {
            const found = Array.from(document.querySelectorAll('textarea'))
              .some((el) => placeholders.includes(el.placeholder));
            if (found) window.markHeroSeen();
          };
          const start = () => {
            probe();
            new MutationObserver(probe).observe(document.body, {
              childList: true, subtree: true, attributes: true
            });
          };
          if (document.body) start();
          else document.addEventListener('DOMContentLoaded', start, { once: true });
        }
        """
    )

    def delay_sessions(route) -> None:
        page.wait_for_timeout(1_500)
        route.continue_()

    page.route("**/api/sessions**", delay_sessions)
    page.reload()
    expect(page.get_by_test_id("thread-message-region")).to_be_visible(timeout=30_000)
    assert not hero_seen["value"], "刷新过程中闪现了新聊天欢迎页"


@pytest.mark.xfail(strict=True, reason="BUG-002：附件拖拽后顺序没有变化，见 BUGS.md")
def test_attachments_can_be_reordered_by_dragging(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()
    attachment_page.attach_in_memory(
        [
            {"name": "a.txt", "mimeType": "text/plain", "buffer": b"A"},
            {"name": "b.txt", "mimeType": "text/plain", "buffer": b"B"},
            {"name": "c.txt", "mimeType": "text/plain", "buffer": b"C"},
        ]
    )
    attachment_page.drag_first_to_last()
    assert "a.txt" in attachment_page.names()[-1]
