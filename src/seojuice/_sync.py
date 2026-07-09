from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from seojuice._client import _BaseClient
from seojuice._exceptions import APIConnectionError, APITimeoutError, raise_for_response
from seojuice._resource import WebsiteResource

_VERSION = "0.1.0"
_USER_AGENT = f"seojuice-python/{_VERSION}"


class SEOJuice(_BaseClient):
    """Synchronous client for the SEOJuice Intelligence API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://seojuice.com/api/v2",
        timeout: float = 30.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
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
    # Abstract method implementations
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = self._client.request(
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

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        response = self._client.request(method, path, params=params)
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
    # Domain-scoped resource proxy
    # ------------------------------------------------------------------

    def website(self, domain: str) -> WebsiteResource:
        return WebsiteResource(client=self, domain=domain)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> SEOJuice:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
