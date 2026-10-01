"""A tiny HTTP client used by the API tests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, BinaryIO

import allure
import requests


class ApiError(RuntimeError):
    """Raised when nanobot returns a non-success HTTP response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")


class ApiClient:
    """Keep URL, authentication, and timeout handling out of test cases."""

    def __init__(self, base_url: str, token: str = "", timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def close(self) -> None:
        self.session.close()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _check(response: requests.Response) -> requests.Response:
        if response.ok:
            return response
        raise ApiError(response.status_code, response.text)

    @staticmethod
    def _attach_response(method: str, path: str, response: requests.Response) -> None:
        """Attach a bounded response summary without leaking request credentials or payloads."""
        content_type = response.headers.get("Content-Type", "")
        attachment_type = (
            allure.attachment_type.JSON
            if "application/json" in content_type
            else allure.attachment_type.TEXT
        )
        body = response.text[:20_000]
        allure.attach(
            body,
            name=f"{method.upper()} {path} response (HTTP {response.status_code})",
            attachment_type=attachment_type,
        )

    def get(self, path: str, *, check: bool = True) -> requests.Response:
        with allure.step(f"发送 GET 请求：{path}"):
            response = self.session.get(self._url(path), timeout=self.timeout)
            self._attach_response("GET", path, response)
            return self._check(response) if check else response

    def request(
        self,
        method: str,
        path: str,
        *,
        check: bool = True,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send a low-level request for protocol and negative test cases."""
        with allure.step(f"发送 {method.upper()} 请求：{path}"):
            response = self.session.request(
                method,
                self._url(path),
                timeout=self.timeout if timeout is None else timeout,
                **kwargs,
            )
            self._attach_response(method, path, response)
            return self._check(response) if check else response

    def post(self, path: str, *, json: dict, check: bool = True) -> requests.Response:
        with allure.step(f"发送 POST JSON 请求：{path}"):
            response = self.session.post(self._url(path), json=json, timeout=self.timeout)
            self._attach_response("POST", path, response)
            return self._check(response) if check else response

    def post_raw(
        self,
        path: str,
        *,
        body: bytes | str,
        content_type: str,
        check: bool = True,
    ) -> requests.Response:
        """Post caller-controlled bytes and Content-Type without JSON normalization."""
        return self.request(
            "POST",
            path,
            data=body,
            headers={"Content-Type": content_type},
            check=check,
        )

    def post_multipart(
        self,
        path: str,
        *,
        data: dict[str, str],
        files: list[tuple[str, tuple[str, bytes | BinaryIO, str]]],
        check: bool = True,
    ) -> requests.Response:
        """Post repeated multipart file fields using requests' native encoder."""
        with allure.step(f"发送 multipart 请求：{path}"):
            response = self.session.post(
                self._url(path),
                data=data,
                files=files,
                timeout=self.timeout,
            )
            self._attach_response("POST", path, response)
            return self._check(response) if check else response

    def post_sse(self, path: str, *, json: dict) -> Iterator[str]:
        """Yield non-empty SSE lines while keeping the connection streaming."""
        with allure.step(f"发送 SSE 请求：{path}"):
            with self.session.post(
                self._url(path),
                json=json,
                timeout=self.timeout,
                stream=True,
            ) as response:
                self._check(response)
                if "text/event-stream" not in response.headers.get("Content-Type", ""):
                    raise ApiError(response.status_code, "response is not text/event-stream")
                lines: list[str] = []
                for raw_line in response.iter_lines(decode_unicode=True):
                    if raw_line:
                        lines.append(raw_line)
                        yield raw_line
                allure.attach(
                    "\n".join(lines)[:20_000],
                    name=f"POST {path} SSE response",
                    attachment_type=allure.attachment_type.TEXT,
                )
