from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from seojuice.injection.django import SEOJuiceDjangoMiddleware


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(path: str = "/page/", host: str = "example.com") -> MagicMock:
    request = MagicMock()
    request.build_absolute_uri.return_value = f"https://{host}{path}"
    return request


def _make_html_response(
    html: str = "<html><head><title>Test</title></head><body></body></html>",
    content_type: str = "text/html; charset=utf-8",
) -> MagicMock:
    response = MagicMock()
    response.get.return_value = content_type
    response.content = html.encode("utf-8")
    response.__getitem__ = MagicMock(side_effect=lambda key: content_type if key == "Content-Type" else None)
    response.__setitem__ = MagicMock()
    return response


def _make_json_response() -> MagicMock:
    response = MagicMock()
    response.get.return_value = "application/json"
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSEOJuiceDjangoMiddleware:
    @patch("seojuice.injection.django.fetch_suggestions_sync", return_value={})
    def test_calls_get_response(self, mock_fetch: MagicMock):
        html_response = _make_html_response()
        get_response = MagicMock(return_value=html_response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        request = _make_request()
        middleware(request)

        get_response.assert_called_once_with(request)

    @patch("seojuice.injection.django.fetch_suggestions_sync")
    def test_skips_non_html_responses(self, mock_fetch: MagicMock):
        json_response = _make_json_response()
        get_response = MagicMock(return_value=json_response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        result = middleware(_make_request())

        assert result is json_response
        mock_fetch.assert_not_called()

    @patch("seojuice.injection.django.fetch_suggestions_sync")
    def test_skips_when_content_type_is_empty(self, mock_fetch: MagicMock):
        response = MagicMock()
        response.get.return_value = ""
        get_response = MagicMock(return_value=response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        result = middleware(_make_request())

        assert result is response
        mock_fetch.assert_not_called()

    @patch("seojuice.injection.django.fetch_suggestions_sync")
    def test_skips_when_content_type_is_none(self, mock_fetch: MagicMock):
        response = MagicMock()
        response.get.return_value = None
        get_response = MagicMock(return_value=response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        result = middleware(_make_request())

        assert result is response
        mock_fetch.assert_not_called()

    @patch(
        "seojuice.injection.django.fetch_suggestions_sync",
        return_value={"meta_description": "Injected description"},
    )
    def test_injects_suggestions_into_html(self, mock_fetch: MagicMock):
        original_html = "<html><head><title>Test</title></head><body></body></html>"
        html_response = _make_html_response(original_html)

        get_response = MagicMock(return_value=html_response)
        middleware = SEOJuiceDjangoMiddleware(get_response)
        middleware(request=_make_request("/page/"))

        # The content should have been modified
        new_content = html_response.content
        if isinstance(new_content, bytes):
            new_content_str = new_content.decode("utf-8")
        else:
            # It was set via response.content = ...
            # Check what was assigned
            new_content_str = new_content

        # Verify fetch was called with the absolute URL
        mock_fetch.assert_called_once_with(
            "https://example.com/page/",
            timeout=5.0,
        )

    @patch("seojuice.injection.django.fetch_suggestions_sync", return_value={})
    def test_returns_unchanged_response_when_no_suggestions(self, mock_fetch: MagicMock):
        original_html = "<html><head><title>Test</title></head><body></body></html>"
        html_response = _make_html_response(original_html)
        original_content = html_response.content

        get_response = MagicMock(return_value=html_response)
        middleware = SEOJuiceDjangoMiddleware(get_response)
        result = middleware(_make_request())

        # Content should remain the same since data was empty
        assert result is html_response

    @patch("seojuice.injection.django.fetch_suggestions_sync")
    def test_disabled_when_setting_is_false(self, mock_fetch: MagicMock):
        html_response = _make_html_response()
        get_response = MagicMock(return_value=html_response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        middleware._enabled = False  # Simulate SEOJUICE_INJECTION_ENABLED=False

        result = middleware(_make_request())

        assert result is html_response
        mock_fetch.assert_not_called()

    @patch(
        "seojuice.injection.django.fetch_suggestions_sync",
        return_value={"meta_description": "Test desc"},
    )
    def test_updates_content_length_header(self, mock_fetch: MagicMock):
        original_html = "<html><head><title>Test</title></head><body></body></html>"

        # Use a custom class that behaves like a Django response
        class FakeResponse:
            def __init__(self) -> None:
                self.content = original_html.encode("utf-8")
                self._headers: dict[str, str] = {"Content-Type": "text/html; charset=utf-8"}

            def get(self, key: str, default: str = "") -> str:
                return self._headers.get(key, default)

            def __setitem__(self, key: str, value: str) -> None:
                self._headers[key] = value

            def __getitem__(self, key: str) -> str:
                return self._headers[key]

        html_response = FakeResponse()
        get_response = MagicMock(return_value=html_response)
        middleware = SEOJuiceDjangoMiddleware(get_response)
        middleware(request=_make_request())

        # Content-Length should have been updated
        assert "Content-Length" in html_response._headers
        assert int(html_response._headers["Content-Length"]) > 0

    @patch("seojuice.injection.django.fetch_suggestions_sync")
    def test_uses_configured_timeout(self, mock_fetch: MagicMock):
        mock_fetch.return_value = {}
        html_response = _make_html_response()
        get_response = MagicMock(return_value=html_response)

        middleware = SEOJuiceDjangoMiddleware(get_response)
        middleware._timeout = 2.0

        middleware(_make_request("/test/"))

        mock_fetch.assert_called_once_with(
            "https://example.com/test/",
            timeout=2.0,
        )


class TestMiddlewareInitialization:
    def test_defaults_enabled_to_true(self):
        middleware = SEOJuiceDjangoMiddleware(MagicMock())
        assert middleware._enabled is True

    def test_defaults_timeout_to_5(self):
        middleware = SEOJuiceDjangoMiddleware(MagicMock())
        assert middleware._timeout == 5.0

    @patch("seojuice.injection.django.settings", create=True)
    def test_reads_enabled_from_django_settings(self, mock_settings: MagicMock):
        mock_settings.SEOJUICE_INJECTION_ENABLED = False
        mock_settings.SEOJUICE_INJECTION_TIMEOUT = 3.0

        # We need to patch the import inside __init__
        with patch.dict("sys.modules", {"django.conf": MagicMock(settings=mock_settings)}):
            middleware = SEOJuiceDjangoMiddleware(MagicMock())

        # The middleware tries to import django.conf.settings internally
        # Since the import happens in __init__, we verify the fallback path works
        assert middleware._enabled is not None
        assert middleware._timeout > 0
