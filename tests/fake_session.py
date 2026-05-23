"""A minimal aiohttp ClientSession fake for unit testing Foobar2k.

Records every request and returns scripted responses. No real network.
"""
from __future__ import annotations

from typing import Any, Callable


class FakeResponse:
    def __init__(self, *, status: int = 200, body: str = "") -> None:
        self.status = status
        self._body = body

    async def text(self) -> str:
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeRequestCtx:
    """Context manager returned by session.get / .post that exposes a response."""

    def __init__(self, response: FakeResponse | Exception) -> None:
        self._response = response

    async def __aenter__(self):
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    """Captures requests and returns pre-scripted responses.

    Usage:
        session = FakeSession()
        session.queue_get("/api/player", FakeResponse(body=json.dumps({...})))
        session.queue_post("/api/player/play", FakeResponse(status=204))
    """

    def __init__(self) -> None:
        self.closed = False
        self.requests: list[dict[str, Any]] = []
        self._handlers: dict[tuple[str, str], list[Callable[[dict], FakeResponse | Exception]]] = {}
        self._default_response: FakeResponse | Exception = FakeResponse(status=200, body="")

    # --- scripting ----------------------------------------------------------
    def queue(self, method: str, path: str, response: FakeResponse | Exception) -> None:
        key = (method.upper(), path)
        self._handlers.setdefault(key, []).append(lambda _req: response)

    def queue_get(self, path: str, response: FakeResponse | Exception) -> None:
        self.queue("GET", path, response)

    def queue_post(self, path: str, response: FakeResponse | Exception) -> None:
        self.queue("POST", path, response)

    def set_default(self, response: FakeResponse | Exception) -> None:
        self._default_response = response

    # --- aiohttp surface ----------------------------------------------------
    def _dispatch(self, method: str, url: str, **kwargs) -> FakeRequestCtx:
        # url is "http://host:port/api/...". Strip the scheme+netloc.
        path = url.split("/", 3)[-1] if "//" in url else url
        path = "/" + path if not path.startswith("/") else path
        self.requests.append({"method": method, "url": url, "path": path, "kwargs": kwargs})

        key = (method.upper(), path)
        handlers = self._handlers.get(key, [])
        if handlers:
            response = handlers.pop(0)({"path": path, "kwargs": kwargs})
        else:
            response = self._default_response
        return FakeRequestCtx(response)

    def get(self, url: str, **kwargs) -> FakeRequestCtx:
        return self._dispatch("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> FakeRequestCtx:
        return self._dispatch("POST", url, **kwargs)

    async def close(self) -> None:
        self.closed = True
