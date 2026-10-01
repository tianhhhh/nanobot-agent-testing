"""Black-box tests for the public health endpoint."""

from __future__ import annotations

import allure
import pytest

from utils.api_client import ApiClient

pytestmark = pytest.mark.api


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("健康检查")
@allure.title("健康检查接口返回服务正常状态")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
def test_health_returns_ok(api_client) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("健康检查")
@allure.title("启用 API 鉴权后健康检查仍可公开访问")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.security
def test_health_check_is_public_even_when_api_authentication_is_enabled(api_client) -> None:
    client = ApiClient(api_client.base_url)
    try:
        response = client.get("/health")
    finally:
        client.close()

    assert response.json() == {"status": "ok"}
