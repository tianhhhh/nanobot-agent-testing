"""Black-box attachment tests for chat completions."""

from __future__ import annotations

import base64
from pathlib import Path

import allure
import pytest

pytestmark = pytest.mark.api
API_FILE_LIMIT_BYTES = 10 * 1024 * 1024


def _media_files(test_environment) -> set[Path]:
    media_dir = test_environment.root / "media" / "api"
    return set(media_dir.glob("*")) if media_dir.exists() else set()


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("对话附件")
@allure.title("Base64 图片能够随 JSON 对话请求上传并保存")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_json_base64_image_is_accepted_and_saved(
    api_client, test_environment, tiny_png
) -> None:
    before = _media_files(test_environment)
    encoded = base64.b64encode(tiny_png.read_bytes()).decode("ascii")

    response = api_client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "分析这张图片"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded}"},
                        },
                    ],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert "你好！我是 mock 回复" in response.json()["choices"][0]["message"]["content"]
    created = _media_files(test_environment) - before
    assert len(created) == 1
    assert next(iter(created)).suffix == ".png"


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("对话附件")
@allure.title("单个 multipart 图片能够上传并保存")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_multipart_image_is_accepted_and_saved(
    api_client, test_environment, tiny_png
) -> None:
    before = _media_files(test_environment)

    response = api_client.post_multipart(
        "/v1/chat/completions",
        data={"message": "分析 multipart 图片", "session_id": "attachment-case"},
        files=[
            ("files", (tiny_png.name, tiny_png.read_bytes(), "image/png")),
        ],
    )

    assert response.status_code == 200
    assert response.json()["object"] == "chat.completion"
    created = _media_files(test_environment) - before
    assert len(created) == 1
    assert next(iter(created)).name.endswith("_tiny.png")


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("对话附件")
@allure.title("multipart 请求能够同时上传多个文件")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_multiple_multipart_files_are_accepted_and_saved(
    api_client, test_environment
) -> None:
    before = _media_files(test_environment)
    uploads = [
        ("files", ("alpha.txt", b"alpha", "text/plain")),
        ("files", ("beta.csv", b"name,value\nbeta,2\n", "text/csv")),
        ("files", ("gamma.md", b"# gamma", "text/markdown")),
    ]

    response = api_client.post_multipart(
        "/v1/chat/completions",
        data={"message": "分析多个附件", "session_id": "multi-attachment-case"},
        files=uploads,
    )

    assert response.status_code == 200
    created = _media_files(test_environment) - before
    assert len(created) == len(uploads)
    assert {path.name.split("_", 1)[1] for path in created} == {
        "alpha.txt",
        "beta.csv",
        "gamma.md",
    }


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("附件边界校验")
@allure.title("multipart 单文件超过 10 MiB 时拒绝且不落盘")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_multipart_file_over_10_mib_is_rejected_without_saving(
    api_client, test_environment
) -> None:
    before = _media_files(test_environment)

    response = api_client.post_multipart(
        "/v1/chat/completions",
        data={"message": "oversized attachment"},
        files=[
            (
                "files",
                ("oversized.txt", b"x" * (API_FILE_LIMIT_BYTES + 1), "text/plain"),
            )
        ],
        check=False,
    )

    assert response.status_code == 413
    error = response.json()["error"]
    assert "exceeds 10MB limit" in error["message"]
    assert error["type"] == "invalid_request_error"
    assert _media_files(test_environment) == before


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("附件安全")
@allure.title("远程图片 URL 被拒绝且服务端不代为下载")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.security
def test_remote_image_url_is_rejected_without_server_side_download(
    api_client, test_environment
) -> None:
    before = _media_files(test_environment)

    response = api_client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "分析远程图片"},
                        {
                            "type": "image_url",
                            "image_url": {"url": "https://example.invalid/image.png"},
                        },
                    ],
                }
            ]
        },
        check=False,
    )

    assert response.status_code == 400
    error = response.json()["error"]
    assert "Remote image URLs are not supported" in error["message"]
    assert error["type"] == "invalid_request_error"
    assert _media_files(test_environment) == before


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("附件边界校验")
@allure.title("损坏的 Base64 图片应被拒绝且不落盘")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
@pytest.mark.known_bug
@pytest.mark.xfail(strict=True, reason="BUG-003：损坏的 Base64 图片被静默忽略，见 BUGS.md")
def test_corrupted_base64_image_is_rejected_without_saving(
    api_client, test_environment
) -> None:
    before = _media_files(test_environment)

    response = api_client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "损坏的图片"},
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/png;base64,not-valid!!!"},
                        },
                    ],
                }
            ]
        },
        check=False,
    )

    assert response.status_code == 400
    assert "Invalid base64 data" in response.json()["error"]["message"]
    assert _media_files(test_environment) == before


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("附件边界校验")
@allure.title("Base64 图片超过 10 MiB 时拒绝且不落盘")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.regression
def test_base64_image_over_10_mib_is_rejected_without_saving(
    api_client, test_environment
) -> None:
    before = _media_files(test_environment)
    encoded = base64.b64encode(b"x" * (API_FILE_LIMIT_BYTES + 1)).decode("ascii")

    response = api_client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded}"},
                        }
                    ],
                }
            ]
        },
        check=False,
    )

    assert response.status_code == 413
    assert "exceeds 10MB limit" in response.json()["error"]["message"]
    assert _media_files(test_environment) == before
