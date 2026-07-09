from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest

from seojuice._async import AsyncSEOJuice
from seojuice._exceptions import AuthError, NotFoundError, RateLimitError, ServerError
from seojuice._pagination import PagedResult
from seojuice._resource import AsyncWebsiteResource

from .conftest import make_error_response, make_paginated_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_async_transport(
    handler_fn,
) -> httpx.MockTransport:
    return httpx.MockTransport(handler_fn)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestAsyncSEOJuiceConstruction:
    def test_creates_async_client_with_correct_base_url(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        assert client._base_url == "https://seojuice.com/api/v2"

    def test_sets_bearer_auth_header(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        assert client._client.headers["authorization"] == f"Bearer {api_key}"

    def test_sets_user_agent_header(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        assert "seojuice-python/" in client._client.headers["user-agent"]

    def test_sets_accept_json_header(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        assert client._client.headers["accept"] == "application/json"

    def test_owns_client_when_no_http_client_provided(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        assert client._owns_client is True

    def test_does_not_own_client_when_http_client_provided(self, api_key: str):
        custom = httpx.AsyncClient()
        client = AsyncSEOJuice(api_key, http_client=custom)
        assert client._owns_client is False
        assert client._client is custom


# ---------------------------------------------------------------------------
# Sync methods raise RuntimeError
# ---------------------------------------------------------------------------


class TestSyncMethodsRaise:
    def test_sync_request_raises_runtime_error(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        with pytest.raises(RuntimeError, match="Use await"):
            client._request("GET", "/websites/")

    def test_sync_request_bytes_raises_runtime_error(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        with pytest.raises(RuntimeError, match="Use await"):
            client._request_bytes("GET", "/websites/example.com/reports/1/pdf/")


# ---------------------------------------------------------------------------
# Async context manager
# ---------------------------------------------------------------------------


class TestAsyncContextManager:
    async def test_async_context_manager_returns_self(self, api_key: str):
        async with AsyncSEOJuice(api_key) as client:
            assert isinstance(client, AsyncSEOJuice)

    async def test_async_context_manager_closes_owned_client(self, api_key: str):
        transport = _make_async_transport(lambda req: httpx.Response(200, json={}))
        http_client = httpx.AsyncClient(transport=transport)
        client = AsyncSEOJuice(api_key, http_client=http_client)
        client._owns_client = True
        async with client:
            pass
        assert http_client.is_closed

    async def test_async_context_manager_does_not_close_unowned_client(self, api_key: str):
        transport = _make_async_transport(lambda req: httpx.Response(200, json={}))
        http_client = httpx.AsyncClient(transport=transport)
        async with AsyncSEOJuice(api_key, http_client=http_client):
            pass
        assert not http_client.is_closed
        await http_client.aclose()


# ---------------------------------------------------------------------------
# Async request methods
# ---------------------------------------------------------------------------


class TestArequest:
    async def test_aget_calls_correct_endpoint(self, api_key: str):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json={"results": [{"domain": "example.com"}]})

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        result = await client._aget("/websites/")

        assert len(requests_made) == 1
        assert requests_made[0].method == "GET"
        assert requests_made[0].url.raw_path == b"/api/v2/websites/"
        await http_client.aclose()

    async def test_apost_calls_correct_endpoint(self, api_key: str):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json={"analysis_id": "abc-123", "status": "queued"})

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        result = await client._apost("/websites/example.com/analyze/", {"url": "https://example.com/page"})

        assert requests_made[0].method == "POST"
        body = json.loads(requests_made[0].content)
        assert body == {"url": "https://example.com/page"}
        await http_client.aclose()

    async def test_apaginate_returns_paged_result(self, api_key: str):
        data = make_paginated_response(
            [{"id": 1}, {"id": 2}],
            page=1,
            total_count=2,
            total_pages=1,
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=data)

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        result = await client._apaginate("/websites/example.com/pages/")

        assert isinstance(result, PagedResult)
        assert len(result) == 2
        assert result.pagination["total_count"] == 2
        await http_client.aclose()

    async def test_apaginate_falls_back_when_no_pagination_key(self, api_key: str):
        data = {"results": [{"id": 1}]}

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=data)

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        result = await client._apaginate("/websites/example.com/pages/")

        assert isinstance(result, PagedResult)
        assert result.pagination["page"] == 1
        assert result.pagination["total_pages"] == 1
        assert result.pagination["total_count"] == 1
        await http_client.aclose()


# ---------------------------------------------------------------------------
# Async error handling
# ---------------------------------------------------------------------------


class TestAsyncErrorHandling:
    async def test_arequest_raises_auth_error(self, api_key: str):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json=make_error_response("unauthorized", "Bad token"))

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        with pytest.raises(AuthError) as exc_info:
            await client._aget("/websites/")
        assert exc_info.value.status_code == 401
        await http_client.aclose()

    async def test_arequest_bytes_raises_not_found(self, api_key: str):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json=make_error_response("not_found", "Not found"))

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        with pytest.raises(NotFoundError):
            await client._arequest_bytes("GET", "/websites/example.com/reports/99/pdf/")
        await http_client.aclose()

    async def test_arequest_bytes_handles_non_json_error_body(self, api_key: str):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, content=b"Internal Server Error")

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        with pytest.raises(ServerError):
            await client._arequest_bytes("GET", "/websites/example.com/reports/1/pdf/")
        await http_client.aclose()

    async def test_arequest_bytes_returns_content_on_success(self, api_key: str):
        pdf_bytes = b"%PDF-1.4 content"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=pdf_bytes)

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        result = await client._arequest_bytes("GET", "/websites/example.com/reports/1/pdf/")
        assert result == pdf_bytes
        await http_client.aclose()


# ---------------------------------------------------------------------------
# Domain-scoped resource proxy
# ---------------------------------------------------------------------------


class TestAsyncWebsiteResourceProxy:
    def test_website_returns_async_website_resource(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        resource = client.website("example.com")
        assert isinstance(resource, AsyncWebsiteResource)
        assert resource.domain == "example.com"


# ---------------------------------------------------------------------------
# Verify _aget passes clean params
# ---------------------------------------------------------------------------


class TestAgetCleanParams:
    async def test_aget_removes_none_and_converts_bools(self, api_key: str):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json={"result": "ok"})

        transport = _make_async_transport(handler)
        http_client = httpx.AsyncClient(
            base_url="https://seojuice.com/api/v2",
            transport=transport,
        )
        client = AsyncSEOJuice(api_key, http_client=http_client)

        await client._aget(
            "/websites/example.com/intelligence/",
            {"period": "7d", "include_history": True, "optional": None},
        )

        url = requests_made[0].url
        assert url.params["period"] == "7d"
        assert url.params["include_history"] == "true"
        assert "optional" not in url.params
        await http_client.aclose()


# ---------------------------------------------------------------------------
# Async error responses with non-JSON bodies (item 1)
# ---------------------------------------------------------------------------


class TestAsyncNonJsonErrorBodies:
    async def _client(self, api_key: str, response: httpx.Response) -> tuple[AsyncSEOJuice, httpx.AsyncClient]:
        transport = _make_async_transport(lambda req: response)
        http = httpx.AsyncClient(base_url="https://seojuice.com/api/v2", transport=transport)
        return AsyncSEOJuice(api_key, http_client=http), http

    async def test_html_502_raises_server_error_not_jsondecode(self, api_key: str):
        resp = httpx.Response(502, headers={"content-type": "text/html"}, content=b"<html>502</html>")
        client, http = await self._client(api_key, resp)
        with pytest.raises(ServerError) as exc_info:
            await client._aget("/websites/")
        assert exc_info.value.status_code == 502
        await http.aclose()

    async def test_empty_body_503_raises_server_error(self, api_key: str):
        resp = httpx.Response(503, content=b"")
        client, http = await self._client(api_key, resp)
        with pytest.raises(ServerError):
            await client._aget("/websites/")
        await http.aclose()

    async def test_non_json_429_raises_rate_limit_error(self, api_key: str):
        resp = httpx.Response(429, headers={"content-type": "text/plain"}, content=b"Too Many Requests")
        client, http = await self._client(api_key, resp)
        with pytest.raises(RateLimitError):
            await client._aget("/websites/")
        await http.aclose()
