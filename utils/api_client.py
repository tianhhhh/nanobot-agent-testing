"""A tiny HTTP client used by the API tests."""

from __future__ import annotations

from collections.abc import Iterator

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

    def get(self, path: str) -> requests.Response:
        response = self.session.get(self._url(path), timeout=self.timeout)
        return self._check(response)

    def post(self, path: str, *, json: dict) -> requests.Response:
        response = self.session.post(self._url(path), json=json, timeout=self.timeout)
        return self._check(response)

    def post_sse(self, path: str, *, json: dict) -> Iterator[str]:
        """Yield non-empty SSE lines while keeping the connection streaming."""
        with self.session.post(
            self._url(path),
            json=json,
            timeout=self.timeout,
            stream=True,
        ) as response:
            self._check(response)
            if "text/event-stream" not in response.headers.get("Content-Type", ""):
                raise ApiError(response.status_code, "response is not text/event-stream")
            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line:
                    yield raw_line

