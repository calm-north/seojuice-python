from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional

from seojuice.injection._fetcher import apply_suggestions, fetch_suggestions_async

Scope = Dict[str, Any]
Receive = Callable[[], Awaitable[Dict[str, Any]]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class _ResponseInterceptor:
    """Captures ASGI response messages to allow body modification."""

    def __init__(self, send: Send) -> None:
        self._send = send
        self._initial_message: Optional[Dict[str, Any]] = None
        self._body_parts: List[bytes] = []
        self._is_html = False
        self._headers: List[List[bytes]] = []

    def _check_content_type(self, headers: List[List[bytes]]) -> bool:
        for header_name, header_value in headers:
            if header_name.lower() == b"content-type":
                return b"text/html" in header_value
        return False

    async def send(self, message: Dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            raw_headers = message.get("headers", [])
            self._headers = raw_headers
            self._is_html = self._check_content_type(raw_headers)
            self._initial_message = message
            if not self._is_html:
                await self._send(message)
            return

        if message["type"] == "http.response.body":
            if not self._is_html:
                await self._send(message)
                return
            body = message.get("body", b"")
            self._body_parts.append(body)
            return

    @property
    def is_html(self) -> bool:
        return self._is_html

    @property
    def full_body(self) -> bytes:
        return b"".join(self._body_parts)

    async def flush(self, body: bytes) -> None:
        if self._initial_message is None:
            return

        new_headers: List[List[bytes]] = []
        for header_name, header_value in self._headers:
            if header_name.lower() == b"content-length":
                new_headers.append([header_name, str(len(body)).encode()])
            else:
                new_headers.append([header_name, header_value])

        self._initial_message["headers"] = new_headers
        await self._send(self._initial_message)
        await self._send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })


class SEOJuiceASGIMiddleware:
    """ASGI middleware that injects SEO suggestions into HTML responses."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        base_url: str = "",
        timeout: float = 3.0,
        enabled: bool = True,
    ) -> None:
        self._app = app
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._enabled = enabled

    def _build_page_url(self, scope: Scope) -> str:
        path = scope.get("path", "/")
        scheme = scope.get("scheme", "https")
        server = scope.get("server")
        if server:
            host, port = server
            if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
                return f"{scheme}://{host}{path}"
            return f"{scheme}://{host}:{port}{path}"
        if self._base_url:
            return f"{self._base_url}{path}"
        return path

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http" or not self._enabled:
            await self._app(scope, receive, send)
            return

        interceptor = _ResponseInterceptor(send)
        await self._app(scope, receive, interceptor.send)

        if not interceptor.is_html:
            return

        full_body = interceptor.full_body
        if not full_body:
            await interceptor.flush(full_body)
            return

        page_url = self._build_page_url(scope)
        data = await fetch_suggestions_async(page_url, timeout=self._timeout)

        html = full_body.decode("utf-8", errors="replace")
        modified = apply_suggestions(html, data)
        await interceptor.flush(modified.encode("utf-8"))
