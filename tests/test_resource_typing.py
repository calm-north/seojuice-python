from __future__ import annotations

import inspect

import httpx
import pytest

from seojuice._resource import WebsiteResource
from seojuice._sync import SEOJuice

from .conftest import make_transport_handler


def _resource(api_key: str) -> tuple[WebsiteResource, httpx.Client]:
    http = httpx.Client(
        base_url="https://seojuice.com/api/v2", transport=make_transport_handler()
    )
    client = SEOJuice(api_key, http_client=http)
    return client.website("example.com"), http


class TestBulkChangeActionSignature:
    def test_rejects_change_ids_kwarg(self, api_key: str):
        site, http = _resource(api_key)
        with pytest.raises(TypeError):
            site.bulk_change_action(action="approve", change_ids=[1, 2, 3])
        http.close()

    def test_accepts_action_and_ids(self, api_key: str):
        site, http = _resource(api_key)
        sig = inspect.signature(site.bulk_change_action)
        assert "action" in sig.parameters
        assert "ids" in sig.parameters
        assert "kwargs" not in sig.parameters
        http.close()


class TestUpdateActionItemSignature:
    def test_rejects_status_kwarg(self, api_key: str):
        site, http = _resource(api_key)
        with pytest.raises(TypeError):
            site.update_action_item(99, status="completed")
        http.close()

    def test_accepts_action_kwarg(self, api_key: str):
        site, http = _resource(api_key)
        sig = inspect.signature(site.update_action_item)
        assert "action" in sig.parameters
        assert "status" not in sig.parameters
        http.close()


class TestVariadicMethodStaysOpen:
    def test_update_change_settings_still_variadic(self, api_key: str):
        site, http = _resource(api_key)
        sig = inspect.signature(site.update_change_settings)
        assert any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        ), "update_change_settings must stay **settings variadic"
        http.close()
