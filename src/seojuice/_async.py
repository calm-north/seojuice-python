from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from seojuice._client import _BaseClient, _clean_params
from seojuice._exceptions import APIConnectionError, APITimeoutError, raise_for_response
from seojuice._pagination import PagedResult
from seojuice._resource import AsyncWebsiteResource
from seojuice._types import PaginationMeta

_VERSION = "0.1.0"
_USER_AGENT = f"seojuice-python/{_VERSION}"


class AsyncSEOJuice(_BaseClient):
    """Asynchronous client for the SEOJuice Intelligence API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://seojuice.com/api/v2",
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": _USER_AGENT,
                    "Accept": "application/json",
                },
                timeout=timeout,
            )
            self._owns_client = True

    # ------------------------------------------------------------------
    # Sync abstract methods raise — callers must use async variants
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        raise RuntimeError(
            "Use await with AsyncSEOJuice. "
            "Call async methods or use SEOJuice for sync usage."
        )

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        raise RuntimeError(
            "Use await with AsyncSEOJuice. "
            "Call async methods or use SEOJuice for sync usage."
        )

    # ------------------------------------------------------------------
    # Async request implementations
    # ------------------------------------------------------------------

    async def _arequest(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                path,
                params=params,
                json=json,
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except httpx.TransportError as exc:
            raise APIConnectionError(str(exc)) from exc
        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:
                body = {}
            raise_for_response(
                response.status_code, body if isinstance(body, dict) else {}
            )
        return response.json()

    async def _arequest_bytes(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        response = await self._client.request(method, path, params=params)
        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:
                body = {}
            raise_for_response(
                response.status_code, body if isinstance(body, dict) else {}
            )
        return response.content

    # ------------------------------------------------------------------
    # Async convenience helpers
    # ------------------------------------------------------------------

    async def _aget(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._arequest("GET", path, params=_clean_params(params or {}))

    async def _apost(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        return await self._arequest("POST", path, json=json)

    async def _apatch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        return await self._arequest("PATCH", path, json=json)

    async def _apaginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PagedResult[Any]:
        data = await self._aget(path, params)
        pagination: PaginationMeta = data.get(
            "pagination",
            {
                "page": 1,
                "page_size": len(data.get("results", [])),
                "total_count": len(data.get("results", [])),
                "total_pages": 1,
            },
        )
        return PagedResult(results=data.get("results", []), pagination=pagination)

    # ------------------------------------------------------------------
    # Domain-scoped resource proxy
    # ------------------------------------------------------------------

    def website(self, domain: str) -> AsyncWebsiteResource:
        return AsyncWebsiteResource(client=self, domain=domain)

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def close(self) -> None:  # type: ignore[override]
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncSEOJuice:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
