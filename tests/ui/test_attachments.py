"""Browser tests for attachment sending, validation, and ordering."""

import json
from uuid import uuid4

import allure
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui
MOCK_REPLY = "你好！我是 mock 回复"


def _memory_file(name: str, mime_type: str, content: bytes = b"content") -> dict:
    return {"name": name, "mimeType": mime_type, "buffer": content}


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件交互")
@allure.title("单个附件能够随消息正常发送")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.smoke
def test_single_attachment_can_be_sent(chat_page, attachment_page, tiny_png) -> None:
    chat_page.open_new_chat()
    attachment_page.attach_path(tiny_png)
    assert "tiny.png" in attachment_page.names()[0]
    message = f"MVP-附件对话-{uuid4().hex[:8]}"
    chat_page.send_message(message)
    chat_page.wait_for_reply(MOCK_REPLY)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件交互")
@allure.title("多个附件能够随消息正常发送")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_multiple_attachments_can_be_sent(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()
    files = [
        _memory_file("first.txt", "text/plain", b"first"),
        _memory_file("second.csv", "text/csv", b"name,value\nsecond,2\n"),
        _memory_file("third.md", "text/markdown", b"# third"),
    ]
    attachment_page.attach_in_memory(files)

    message = f"MVP-多附件-{uuid4().hex[:8]}"
    chat_page.send_message(message)

    chat_page.wait_for_reply(MOCK_REPLY)


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件交互")
@allure.title("发送前能够移除已选择的附件")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_attachment_can_be_removed_before_sending(
    chat_page, attachment_page, tiny_png
) -> None:
    chat_page.open_new_chat()
    attachment_page.attach_path(tiny_png)

    attachment_page.remove_first()

    expect(chat_page.send_button).to_be_disabled()


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件边界校验")
@allure.title("每条消息最多接受四个附件")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_only_four_attachments_are_accepted_per_message(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()
    files = [_memory_file(f"file-{index}.txt", "text/plain") for index in range(5)]

    attachment_page.select_in_memory(files)

    expect(attachment_page.chips).to_have_count(4)
    expect(chat_page.page.get_by_role("alert")).to_have_text("每条消息最多 4 个附件")


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件边界校验")
@allure.title("不支持的文件类型会被拒绝")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_unsupported_file_type_is_rejected(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()

    attachment_page.select_in_memory(
        [_memory_file("archive.zip", "application/zip")]
    )

    expect(attachment_page.chips).to_have_count(0)
    expect(chat_page.page.get_by_role("alert")).to_have_text("不支持的文件类型")


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件边界校验")
@allure.title("空文件会被拒绝")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_empty_file_is_rejected(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()

    attachment_page.select_in_memory([_memory_file("empty.csv", "text/csv", b"")])

    expect(attachment_page.chips).to_have_count(0)
    expect(chat_page.page.get_by_role("alert")).to_have_text("不能附加空文件")


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件边界校验")
@allure.title("单文件超过 6 MiB 时会被拒绝")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_file_over_6_mib_is_rejected(chat_page, attachment_page) -> None:
    chat_page.open_new_chat()

    attachment_page.select_in_memory(
        [_memory_file("too-large.txt", "text/plain", b"x" * (6 * 1024 * 1024 + 1))]
    )

    expect(attachment_page.chips).to_have_count(0)
    expect(chat_page.page.get_by_role("alert")).to_have_text("文件太大，请换一个小一点的")


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件边界校验")
@allure.title("附件总大小超过 24 MiB 时会被拒绝")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_total_attachment_size_over_24_mib_is_rejected(
    chat_page, attachment_page
) -> None:
    def allow_five_files(route) -> None:
        response = route.fetch()
        body = response.json()
        body["limits"]["attachments"]["max_count"] = 5
        route.fulfill(
            status=response.status,
            headers=response.headers,
            body=json.dumps(body, ensure_ascii=False),
        )

    chat_page.page.route("**/webui/bootstrap**", allow_five_files)
    chat_page.open_new_chat()
    files = [
        _memory_file(f"part-{index}.txt", "text/plain", b"x" * (5 * 1024 * 1024))
        for index in range(5)
    ]

    attachment_page.select_in_memory(files)

    expect(attachment_page.chips).to_have_count(4)
    expect(chat_page.page.get_by_role("alert")).to_have_text(
        "附件总大小过大，请移除部分文件或使用更小的文件"
    )


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件交互")
@allure.title("通过 {interaction} 操作添加图片附件")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
@pytest.mark.parametrize("interaction", ["paste", "drop"])
def test_image_can_be_added_by_paste_or_drop(
    chat_page, attachment_page, tiny_png, interaction: str
) -> None:
    chat_page.open_new_chat()
    if interaction == "paste":
        attachment_page.paste_path(chat_page.composer, tiny_png, "image/png")
    else:
        form = chat_page.composer.locator("xpath=ancestor::form")
        attachment_page.drop_path(form, tiny_png, "image/png")

    expect(attachment_page.chips).to_contain_text("tiny.png")


@allure.epic("nanobot 自动化测试")
@allure.feature("UI 测试")
@allure.story("附件交互")
@allure.title("拖拽能够调整附件顺序")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.regression
@pytest.mark.known_bug
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
