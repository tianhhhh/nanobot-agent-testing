"""Authentication tests for protected API routes."""

from __future__ import annotations

import allure
import pytest

from utils.api_client import ApiClient

pytestmark = pytest.mark.api


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("接口鉴权")
@allure.title("缺少或错误的 API Key 被拒绝：{param_id}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.security
@pytest.mark.parametrize("token", ["", "wrong-api-key"])
def test_protected_route_rejects_missing_or_wrong_api_key(api_client, token: str) -> None:
    client = ApiClient(api_client.base_url, token=token)
    try:
        response = client.get("/v1/models", check=False)
    finally:
        client.close()

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["type"] == "invalid_request_error"
    assert error["code"] == 401
