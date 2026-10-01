"""Black-box tests for the OpenAI-compatible models endpoint."""

import allure
import pytest

pytestmark = pytest.mark.api


@allure.epic("nanobot 自动化测试")
@allure.feature("API 测试")
@allure.story("模型列表")
@allure.title("模型列表返回当前配置的模型")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
def test_models_returns_configured_model(api_client) -> None:
    body = api_client.get("/v1/models").json()

    assert body["object"] == "list"
    assert body["data"][0]["id"] == "mock-model"
