"""Two core browser smoke tests."""

from uuid import uuid4

import pytest

pytestmark = [pytest.mark.ui, pytest.mark.smoke]
MOCK_REPLY = "你好！我是 mock 回复"


def test_new_chat_shows_mock_reply(chat_page) -> None:
    chat_page.open_new_chat()
    message = f"MVP-普通对话-{uuid4().hex[:8]}"
    chat_page.send_message(message)
    chat_page.wait_for_reply(MOCK_REPLY)


def test_single_attachment_can_be_sent(chat_page, attachment_page, tiny_png) -> None:
    chat_page.open_new_chat()
    attachment_page.attach_path(tiny_png)
    assert "tiny.png" in attachment_page.names()[0]
    message = f"MVP-附件对话-{uuid4().hex[:8]}"
    chat_page.send_message(message)
    chat_page.wait_for_reply(MOCK_REPLY)
