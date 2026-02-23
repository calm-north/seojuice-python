from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest


# ---------------------------------------------------------------------------
# Reusable API response factories
# ---------------------------------------------------------------------------


def make_paginated_response(
    results: List[Any],
    *,
    page: int = 1,
    page_size: int = 10,
    total_count: int | None = None,
    total_pages: int | None = None,
) -> Dict[str, Any]:
    """Build a standard paginated API response dict."""
    count = total_count if total_count is not None else len(results)
    pages = total_pages if total_pages is not None else 1
    return {
        "results": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": count,
            "total_pages": pages,
        },
    }


def make_error_response(
    error: str = "unknown_error",
    message: str = "An unexpected error occurred",
) -> Dict[str, Any]:
    return {"error": error, "message": message}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_key() -> str:
    return "test-api-key-12345"


@pytest.fixture()
def base_url() -> str:
    return "https://seojuice.com/api/v2"


@pytest.fixture()
def sample_website() -> Dict[str, Any]:
    return {
        "domain": "example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "last_processed_at": "2024-06-01T00:00:00Z",
        "platform": "wordpress",
        "industry": "tech",
        "scores": {"seo": 85.0},
        "seo_score": 85.0,
        "report": None,
        "kpis": {"total_links": 100, "total_pages": 50, "total_keywords": 200},
    }


@pytest.fixture()
def sample_page() -> Dict[str, Any]:
    return {
        "id": 1,
        "url": "https://example.com/page-1",
        "title": "Page 1",
        "page_type": "article",
        "seo_score": 78.0,
        "accessibility_score": 90.0,
        "meta_description": "A test page",
        "language_code": "en",
        "created_at": "2024-01-01T00:00:00Z",
        "last_processed_at": "2024-06-01T00:00:00Z",
        "readability": {
            "flesch_kincaid": 65.0,
            "automated_readability": 7.5,
            "dale_chall": 6.0,
            "coleman_liau": 10.0,
        },
        "onpage_score": 70.0,
        "conversion_score": 55.0,
        "structured_data": None,
        "has_structured_data": False,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "links": [],
    }


@pytest.fixture()
def sample_websites_list(sample_website: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "results": [
            {"domain": "example.com", "created_at": "2024-01-01T00:00:00Z"},
            {"domain": "test.com", "created_at": "2024-02-01T00:00:00Z"},
        ]
    }


@pytest.fixture()
def sample_paginated_pages(sample_page: Dict[str, Any]) -> Dict[str, Any]:
    return make_paginated_response(
        [sample_page],
        page=1,
        page_size=10,
        total_count=1,
        total_pages=1,
    )


def make_transport_handler(
    responses: Dict[str, httpx.Response] | None = None,
    default_response: httpx.Response | None = None,
) -> httpx.MockTransport:
    """Create a MockTransport that maps (method, path) to canned responses.

    ``responses`` keys should be ``"METHOD /path"`` strings, e.g.
    ``"GET /websites/"``.
    """
    _responses = responses or {}
    _default = default_response or httpx.Response(200, json={})

    def handler(request: httpx.Request) -> httpx.Response:
        key = f"{request.method} {request.url.raw_path.decode()}"
        # Also try without query string
        path_only = request.url.raw_path.decode().split("?")[0]
        key_no_qs = f"{request.method} {path_only}"
        return _responses.get(key, _responses.get(key_no_qs, _default))

    return httpx.MockTransport(handler)
