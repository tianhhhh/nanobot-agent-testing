"""High-value persisted chat scenarios selected from the XMind cases."""

import re
from uuid import uuid4

import allure
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.ui
MOCK_REPLY = "你好！我是 mock 回复"


def _create_chat(chat_page) -> str:
    message = f"MVP-会话管理-{uuid4().hex[:8]}"
    chat_page.open_new_chat()
    chat_page.send_message(message)
    chat_page.wait_for_reply(MOCK_REPLY)
    return message


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("会话管理")
@allure.title("重命名会话后刷新页面仍保留新名称")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_chat_rename_persists_after_page_reload(chat_page, session_page) -> None:
    original_message = _create_chat(chat_page)
    new_title = f"自动化会话-{uuid4().hex[:8]}"

    session_page.rename_active_chat(new_title)
    chat_page.page.reload()

    expect(session_page.sidebar.get_by_text(new_title, exact=True)).to_be_visible(
        timeout=20_000
    )
    expect(chat_page.message_region).to_contain_text(original_message, timeout=30_000)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("会话管理")
@allure.title("会话能够置顶并取消置顶")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_chat_can_be_pinned_and_unpinned(chat_page, session_page) -> None:
    _create_chat(chat_page)

    session_page.pin_active_chat()
    session_page.unpin_active_chat()


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("会话管理")
@allure.title("会话能够归档并恢复")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_chat_can_be_archived_and_restored(chat_page, session_page) -> None:
    _create_chat(chat_page)
    title = f"待归档会话-{uuid4().hex[:8]}"
    session_page.rename_active_chat(title)

    session_page.archive_active_chat(title)
    session_page.unarchive_chat(title)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("会话管理")
@allure.title("搜索结果能够打开对应会话历史")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_search_finds_a_chat_and_opens_its_history(chat_page, session_page) -> None:
    first_message = _create_chat(chat_page)
    first_title = f"搜索目标-{uuid4().hex[:8]}"
    session_page.rename_active_chat(first_title)

    _create_chat(chat_page)
    session_page.rename_active_chat(f"搜索干扰项-{uuid4().hex[:8]}")

    session_page.search_and_open_chat(first_title)

    expect(chat_page.message_region).to_contain_text(first_message, timeout=30_000)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("历史话题提及")
@allure.title("通过 @ 提及引用历史会话")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_at_mention_can_reference_a_historical_chat(chat_page, session_page) -> None:
    _create_chat(chat_page)
    title = f"历史话题-{uuid4().hex[:8]}"
    session_page.rename_active_chat(title)
    handle = session_page.handle_for_title(title)
    _create_chat(chat_page)

    chat_page.composer.fill(f"@{title}")
    option = chat_page.page.get_by_role("option", name=re.compile(title))
    expect(option).to_be_visible(timeout=20_000)
    option.click()
    chat_page.composer.type(" 请总结这个话题")
    chat_page.composer.press("Enter")

    expect(chat_page.page.get_by_test_id(f"message-session-mention-{handle}")).to_be_visible(
        timeout=20_000
    )
    chat_page.wait_for_reply(MOCK_REPLY)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("会话恢复")
@allure.title("刷新历史会话时不会闪现新聊天欢迎页")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.regression
@pytest.mark.known_bug
def test_refresh_does_not_flash_new_chat_hero(chat_page, page: Page) -> None:
    chat_page.open_new_chat()
    message = f"MVP-刷新场景-{uuid4().hex[:8]}"
    chat_page.send_message(message)
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
    expect(page.get_by_test_id("thread-message-region")).to_contain_text(
        message, timeout=30_000
    )
    assert not hero_seen["value"], "刷新过程中闪现了新聊天欢迎页"
