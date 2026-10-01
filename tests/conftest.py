"""Shared environment and browser fixtures for the MVP test project."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page

from pages.attachment_page import AttachmentPage
from pages.chat_page import ChatPage
from pages.session_page import SessionPage
from utils.api_client import ApiClient

WEBUI_PORT = 8765
API_PORT = 8900
MOCK_PORT = 9999
GATEWAY_PORT = 18790
API_KEY = "nanobot-mvp-test-key"
WEBUI_URL = f"http://127.0.0.1:{WEBUI_PORT}"
API_URL = f"http://127.0.0.1:{API_PORT}"
MOCK_URL = f"http://127.0.0.1:{MOCK_PORT}"


@dataclass
class TestEnvironment:
    root: Path
    workspace: Path
    config: Path
    logs: Path


def _assert_ports_are_free() -> None:
    occupied: list[int] = []
    for port in (WEBUI_PORT, API_PORT, MOCK_PORT, GATEWAY_PORT):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                occupied.append(port)
    if occupied:
        pytest.fail(
            f"测试需要的端口已被占用：{occupied}。请先关闭对应程序再运行测试。",
            pytrace=False,
        )


def _wait_for(url: str, name: str, process: subprocess.Popen, log_path: Path) -> None:
    deadline = time.monotonic() + 45
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(
                f"{name} 启动失败，进程退出码为 {process.returncode}。日志：{log_path}",
                pytrace=False,
            )
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001 - retain the last readiness error
            last_error = exc
        time.sleep(0.25)
    pytest.fail(f"等待 {name} 超时：{last_error}。日志：{log_path}", pytrace=False)


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@pytest.fixture(scope="session")
def test_environment(tmp_path_factory: pytest.TempPathFactory) -> TestEnvironment:
    root = tmp_path_factory.mktemp("nanobot-mvp")
    workspace = root / "workspace"
    logs = root / "logs"
    workspace.mkdir()
    logs.mkdir()
    config = root / "config.json"
    config.write_text(
        json.dumps(
            {
                "providers": {
                    "custom": {"apiKey": None, "apiBase": f"{MOCK_URL}/v1"}
                },
                "modelPresets": {
                    "Mock A": {"provider": "custom", "model": "mock-model"},
                    "Mock B": {"provider": "custom", "model": "mock-model-b"},
                },
                "agents": {
                    "defaults": {"modelPreset": "Mock A", "workspace": str(workspace)}
                },
                "channels": {
                    "websocket": {
                        "enabled": True,
                        "host": "127.0.0.1",
                        "port": WEBUI_PORT,
                        "allowFrom": ["*"],
                        "streaming": True,
                        "websocketRequiresToken": False,
                    }
                },
                "gateway": {"host": "127.0.0.1", "port": GATEWAY_PORT},
                "api": {
                    "host": "127.0.0.1",
                    "port": API_PORT,
                    "apiKey": API_KEY,
                    "timeout": 6,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return TestEnvironment(root=root, workspace=workspace, config=config, logs=logs)


@pytest.fixture(scope="session", autouse=True)
def services(test_environment: TestEnvironment) -> Iterator[None]:
    _assert_ports_are_free()
    project_root = Path(__file__).resolve().parents[1]
    commands = [
        (
            "Mock 服务",
            [sys.executable, str(project_root / "mocks" / "mock_chat_server.py")],
            f"{MOCK_URL}/health",
            "mock.log",
        ),
        (
            "nanobot Gateway",
            [
                sys.executable,
                "-m",
                "nanobot",
                "gateway",
                "--foreground",
                "--config",
                str(test_environment.config),
                "--workspace",
                str(test_environment.workspace),
            ],
            WEBUI_URL,
            "gateway.log",
        ),
        (
            "nanobot API",
            [
                sys.executable,
                "-m",
                "nanobot",
                "serve",
                "--config",
                str(test_environment.config),
                "--workspace",
                str(test_environment.workspace),
            ],
            f"{API_URL}/health",
            "api.log",
        ),
    ]
    processes: list[tuple[subprocess.Popen, object]] = []
    try:
        for name, command, health_url, log_name in commands:
            log_path = test_environment.logs / log_name
            log_file = log_path.open("w", encoding="utf-8")
            process = subprocess.Popen(
                command,
                cwd=project_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=os.environ.copy(),
            )
            processes.append((process, log_file))
            _wait_for(health_url, name, process, log_path)
        yield
    finally:
        for process, _ in reversed(processes):
            _stop(process)
        for _, log_file in processes:
            log_file.close()
        report_logs = Path(os.getenv("SERVICE_LOG_DIR", "reports/logs"))
        report_logs.mkdir(parents=True, exist_ok=True)
        for log in test_environment.logs.glob("*.log"):
            (report_logs / log.name).write_bytes(log.read_bytes())


@pytest.fixture(scope="session")
def api_client(services: None) -> Iterator[ApiClient]:
    client = ApiClient(API_URL, token=API_KEY)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def chat_page(page: Page, services: None) -> ChatPage:
    page.add_init_script("localStorage.setItem('nanobot.locale', 'zh-CN')")
    return ChatPage(page, WEBUI_URL)


@pytest.fixture
def attachment_page(page: Page, services: None) -> AttachmentPage:
    return AttachmentPage(page)


@pytest.fixture
def session_page(page: Page, services: None) -> SessionPage:
    return SessionPage(page)


@pytest.fixture(scope="session", autouse=True)
def allure_environment_metadata(request: pytest.FixtureRequest) -> None:
    """Write execution context next to the raw Allure result files."""
    configured_results = request.config.getoption("allure_report_dir")
    if not configured_results:
        return
    results = Path(configured_results)
    results.mkdir(parents=True, exist_ok=True)
    (results / "environment.properties").write_text(
        "tested.system=nanobot\n"
        f"python.version={sys.version.split()[0]}\n"
        "browser=Chromium\n"
        "model.backend=deterministic local mock\n",
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Attach a browser screenshot to Allure when a UI test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is not None and not page.is_closed():
        allure.attach(
            page.screenshot(full_page=True),
            name="failure-screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
    environment = item.funcargs.get("test_environment")
    if environment is not None:
        for log_path in environment.logs.glob("*.log"):
            allure.attach.file(
                log_path,
                name=f"service-log-{log_path.stem}",
                attachment_type=allure.attachment_type.TEXT,
            )


@pytest.fixture(scope="session")
def tiny_png(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("assets") / "tiny.png"
    path.write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
            "0000000c49444154789c63f8cfc0000003010100c9fe92ef0000000049454e44ae426082"
        )
    )
    return path
