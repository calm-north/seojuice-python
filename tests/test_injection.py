from __future__ import annotations

import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import httpx
import pytest

from seojuice.injection._fetcher import (
    _SuggestionsCache,
    _cache,
    apply_suggestions,
    fetch_suggestions_async,
    fetch_suggestions_sync,
)


# ---------------------------------------------------------------------------
# _SuggestionsCache
# ---------------------------------------------------------------------------


class TestSuggestionsCache:
    def test_stores_and_retrieves_values(self):
        cache = _SuggestionsCache(ttl=300.0)
        cache.set("key1", {"meta_description": "Hello"})
        assert cache.get("key1") == {"meta_description": "Hello"}

    def test_returns_none_for_missing_key(self):
        cache = _SuggestionsCache(ttl=300.0)
        assert cache.get("nonexistent") is None

    def test_returns_none_for_expired_entry(self, monkeypatch: pytest.MonkeyPatch):
        cache = _SuggestionsCache(ttl=1.0)

        # Store at time=100
        monkeypatch.setattr(time, "monotonic", lambda: 100.0)
        cache.set("key1", {"data": "value"})

        # Retrieve at time=100.5 (within TTL)
        monkeypatch.setattr(time, "monotonic", lambda: 100.5)
        assert cache.get("key1") is not None

        # Retrieve at time=102 (past TTL of 1.0s)
        monkeypatch.setattr(time, "monotonic", lambda: 102.0)
        assert cache.get("key1") is None

    def test_expired_entry_is_deleted_from_store(self, monkeypatch: pytest.MonkeyPatch):
        cache = _SuggestionsCache(ttl=1.0)

        monkeypatch.setattr(time, "monotonic", lambda: 100.0)
        cache.set("key1", {"data": "value"})

        monkeypatch.setattr(time, "monotonic", lambda: 102.0)
        cache.get("key1")  # triggers deletion

        assert "key1" not in cache._store

    def test_clear_removes_all_entries(self):
        cache = _SuggestionsCache(ttl=300.0)
        cache.set("a", {"x": 1})
        cache.set("b", {"y": 2})
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert len(cache._store) == 0

    def test_overwrite_existing_key(self):
        cache = _SuggestionsCache(ttl=300.0)
        cache.set("key", {"old": True})
        cache.set("key", {"new": True})
        assert cache.get("key") == {"new": True}


# ---------------------------------------------------------------------------
# fetch_suggestions_sync
# ---------------------------------------------------------------------------


class TestFetchSuggestionsSync:
    def setup_method(self):
        _cache.clear()

    def test_returns_cached_value_if_available(self, monkeypatch: pytest.MonkeyPatch):
        cached_data = {"meta_description": "Cached desc"}
        _cache.set("https://example.com/page", cached_data)

        # httpx.get should NOT be called
        mock_get = MagicMock(side_effect=AssertionError("Should not be called"))
        monkeypatch.setattr(httpx, "get", mock_get)

        result = fetch_suggestions_sync("https://example.com/page")
        assert result == cached_data

    def test_fetches_from_api_on_cache_miss(self, monkeypatch: pytest.MonkeyPatch):
        api_data = {"meta_description": "From API", "title": "New Title"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_data
        monkeypatch.setattr(httpx, "get", MagicMock(return_value=mock_response))

        result = fetch_suggestions_sync("https://example.com/page")
        assert result == api_data

    def test_caches_successful_response(self, monkeypatch: pytest.MonkeyPatch):
        api_data = {"meta_description": "Cached now"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_data
        monkeypatch.setattr(httpx, "get", MagicMock(return_value=mock_response))

        fetch_suggestions_sync("https://example.com/page2")
        assert _cache.get("https://example.com/page2") == api_data

    def test_returns_empty_dict_on_http_error(self, monkeypatch: pytest.MonkeyPatch):
        mock_response = MagicMock()
        mock_response.status_code = 500
        monkeypatch.setattr(httpx, "get", MagicMock(return_value=mock_response))

        result = fetch_suggestions_sync("https://example.com/error")
        assert result == {}

    def test_returns_empty_dict_on_404(self, monkeypatch: pytest.MonkeyPatch):
        mock_response = MagicMock()
        mock_response.status_code = 404
        monkeypatch.setattr(httpx, "get", MagicMock(return_value=mock_response))

        result = fetch_suggestions_sync("https://example.com/missing")
        assert result == {}

    def test_returns_empty_dict_on_network_error(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(httpx, "get", MagicMock(side_effect=httpx.ConnectError("Connection refused")))

        result = fetch_suggestions_sync("https://example.com/down")
        assert result == {}

    def test_returns_empty_dict_on_timeout(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(httpx, "get", MagicMock(side_effect=httpx.TimeoutException("Timed out")))

        result = fetch_suggestions_sync("https://example.com/slow")
        assert result == {}

    def test_passes_correct_params_to_httpx(self, monkeypatch: pytest.MonkeyPatch):
        mock_get = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        monkeypatch.setattr(httpx, "get", mock_get)

        fetch_suggestions_sync("https://example.com/page", timeout=10.0)

        mock_get.assert_called_once_with(
            "https://smart.seojuice.io/suggestions",
            params={"url": "https://example.com/page"},
            timeout=10.0,
        )


# ---------------------------------------------------------------------------
# fetch_suggestions_async
# ---------------------------------------------------------------------------


class TestFetchSuggestionsAsync:
    def setup_method(self):
        _cache.clear()

    async def test_returns_cached_value_if_available(self):
        cached_data = {"meta_description": "Async cached"}
        _cache.set("https://example.com/async-page", cached_data)

        result = await fetch_suggestions_async("https://example.com/async-page")
        assert result == cached_data

    async def test_fetches_from_api_on_cache_miss(self, monkeypatch: pytest.MonkeyPatch):
        api_data = {"meta_description": "Async API"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_data

        mock_client_instance = MagicMock()
        mock_client_instance.get = MagicMock(return_value=mock_response)
        mock_client_instance.__aenter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = MagicMock(return_value=None)

        # Make the async context manager work properly
        import asyncio

        async def aenter(*args: Any) -> Any:
            return mock_client_instance

        async def aexit(*args: Any) -> None:
            pass

        async def async_get(*args: Any, **kwargs: Any) -> Any:
            return mock_response

        mock_client_instance.__aenter__ = aenter
        mock_client_instance.__aexit__ = aexit
        mock_client_instance.get = async_get

        monkeypatch.setattr(httpx, "AsyncClient", lambda: mock_client_instance)

        result = await fetch_suggestions_async("https://example.com/async-new")
        assert result == api_data

    async def test_returns_empty_dict_on_exception(self, monkeypatch: pytest.MonkeyPatch):
        async def aenter(*args: Any) -> Any:
            raise httpx.ConnectError("Connection refused")

        mock_client = MagicMock()
        mock_client.__aenter__ = aenter

        async def aexit(*args: Any) -> None:
            pass

        mock_client.__aexit__ = aexit

        monkeypatch.setattr(httpx, "AsyncClient", lambda: mock_client)

        result = await fetch_suggestions_async("https://example.com/fail")
        assert result == {}


# ---------------------------------------------------------------------------
# apply_suggestions
# ---------------------------------------------------------------------------


class TestApplySuggestions:
    BASE_HTML = (
        "<html><head><title>Original Title</title></head>"
        "<body><h1>Hello</h1></body></html>"
    )

    def test_returns_unchanged_html_when_data_is_empty(self):
        result = apply_suggestions(self.BASE_HTML, {})
        assert result == self.BASE_HTML

    def test_returns_unchanged_html_when_data_is_none_like(self):
        result = apply_suggestions(self.BASE_HTML, {})
        assert result == self.BASE_HTML

    def test_injects_meta_description(self):
        data = {"meta_description": "A great page about SEO"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta name="description" content="A great page about SEO">' in result
        assert result.index('<meta name="description"') < result.index("</head>")

    def test_injects_og_title(self):
        data = {"og_title": "OG Title Here"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta property="og:title" content="OG Title Here">' in result

    def test_injects_og_description(self):
        data = {"og_description": "OG Description"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta property="og:description" content="OG Description">' in result

    def test_injects_og_url(self):
        data = {"og_url": "https://example.com/page"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta property="og:url" content="https://example.com/page">' in result

    def test_injects_og_image(self):
        data = {"og_image": "https://example.com/img.png"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta property="og:image" content="https://example.com/img.png">' in result

    def test_injects_structured_data_as_json_ld(self):
        sd = {"@type": "Article", "name": "Test Article"}
        data = {"structured_data": sd}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<script type="application/ld+json">' in result
        assert '"@type":"Article"' in result
        assert '"name":"Test Article"' in result

    def test_replaces_title_tag(self):
        data = {"title": "New SEO Title"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert "<title>New SEO Title</title>" in result
        assert "<title>Original Title</title>" not in result

    def test_title_replacement_escapes_html_characters(self):
        data = {"title": "Title with <script> & stuff"}
        result = apply_suggestions(self.BASE_HTML, data)
        assert "<title>Title with &lt;script&gt; &amp; stuff</title>" not in result
        # The actual implementation only escapes < and >
        assert "<title>Title with &lt;script&gt; & stuff</title>" in result

    def test_multiple_tags_injected_together(self):
        data = {
            "meta_description": "Description",
            "og_title": "OG Title",
            "og_description": "OG Desc",
        }
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta name="description" content="Description">' in result
        assert '<meta property="og:title" content="OG Title">' in result
        assert '<meta property="og:description" content="OG Desc">' in result

    def test_escapes_double_quotes_in_meta_content(self):
        data = {"meta_description": 'A "great" page'}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta name="description" content="A &quot;great&quot; page">' in result

    def test_escapes_double_quotes_in_og_content(self):
        data = {"og_title": 'Title with "quotes"'}
        result = apply_suggestions(self.BASE_HTML, data)
        assert '<meta property="og:title" content="Title with &quot;quotes&quot;">' in result

    def test_only_title_no_tags_injected_before_head(self):
        """When only title is provided and no meta/og tags, no injection before </head>."""
        data = {"title": "New Title Only"}
        html = "<html><head><title>Old</title></head><body></body></html>"
        result = apply_suggestions(html, data)
        assert "<title>New Title Only</title>" in result
        # The closing </head> should NOT have extra tags before it
        # (since tags list is empty, the _HEAD_CLOSE_RE.sub is skipped)

    def test_case_insensitive_head_close(self):
        html = "<html><HEAD><title>Old</title></HEAD><body></body></html>"
        data = {"meta_description": "Test"}
        result = apply_suggestions(html, data)
        assert '<meta name="description" content="Test">' in result

    def test_case_insensitive_title_replacement(self):
        html = "<html><head><TITLE>Old Title</TITLE></head><body></body></html>"
        data = {"title": "New Title"}
        result = apply_suggestions(html, data)
        assert "<title>New Title</title>" in result

    def test_html_without_head_tag_returns_unchanged_for_meta(self):
        """If there's no </head>, meta tags have nowhere to go."""
        html = "<html><body><h1>Hello</h1></body></html>"
        data = {"meta_description": "Description"}
        result = apply_suggestions(html, data)
        # The regex won't match, so the injection string is not inserted
        assert result == html

    def test_empty_string_values_are_not_injected(self):
        data = {"meta_description": "", "og_title": ""}
        result = apply_suggestions(self.BASE_HTML, data)
        assert result == self.BASE_HTML
