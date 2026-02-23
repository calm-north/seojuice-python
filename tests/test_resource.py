from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest

from seojuice._async import AsyncSEOJuice
from seojuice._pagination import PagedResult
from seojuice._resource import AsyncWebsiteResource, WebsiteResource
from seojuice._sync import SEOJuice

from .conftest import make_paginated_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DOMAIN = "example.com"


def _make_sync_client(
    api_key: str,
    handler,
) -> tuple[SEOJuice, httpx.Client]:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
    return SEOJuice(api_key, http_client=http_client), http_client


def _make_async_client(
    api_key: str,
    handler,
) -> tuple[AsyncSEOJuice, httpx.AsyncClient]:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(base_url="https://seojuice.com/api/v2", transport=transport)
    return AsyncSEOJuice(api_key, http_client=http_client), http_client


# ---------------------------------------------------------------------------
# WebsiteResource (sync)
# ---------------------------------------------------------------------------


class TestWebsiteResource:
    def test_domain_property(self, api_key: str):
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={}))
        http_client = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
        client = SEOJuice(api_key, http_client=http_client)
        resource = client.website(DOMAIN)
        assert resource.domain == DOMAIN
        http_client.close()

    def test_detail_delegates_to_get_website(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"domain": DOMAIN})

        client, http = _make_sync_client(api_key, handler)
        result = client.website(DOMAIN).detail()
        assert result["domain"] == DOMAIN
        assert b"/websites/example.com/" in reqs[0].url.raw_path
        http.close()

    def test_pages_delegates_to_list_pages(self, api_key: str):
        data = make_paginated_response([{"id": 1}])

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=data)

        client, http = _make_sync_client(api_key, handler)
        result = client.website(DOMAIN).pages(page=2, page_size=5)
        assert isinstance(result, PagedResult)
        http.close()

    def test_page_delegates_to_get_page(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"id": 42})

        client, http = _make_sync_client(api_key, handler)
        result = client.website(DOMAIN).page(42)
        assert result["id"] == 42
        assert b"/pages/42/" in reqs[0].url.raw_path
        http.close()

    def test_links_delegates(self, api_key: str):
        data = make_paginated_response([{"page_from": "/a"}])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).links()
        assert isinstance(result, PagedResult)
        http.close()

    def test_intelligence_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"domain": DOMAIN, "seo_score": 85.0})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).intelligence(period="7d", include_history=True)
        assert reqs[0].url.params["period"] == "7d"
        http.close()

    def test_topology_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"total_pages": 50})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).topology()
        assert b"/topology/" in reqs[0].url.raw_path
        http.close()

    def test_pagespeed_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"url": "https://example.com"})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).pagespeed("https://example.com")
        assert reqs[0].url.params["url"] == "https://example.com"
        http.close()

    def test_clusters_delegates(self, api_key: str):
        data = make_paginated_response([{"id": 1, "name": "Cluster"}])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).clusters()
        assert isinstance(result, PagedResult)
        http.close()

    def test_cluster_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"id": 5})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).cluster(5)
        assert b"/clusters/5/" in reqs[0].url.raw_path
        http.close()

    def test_content_gaps_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).content_gaps(category="seo")
        assert isinstance(result, PagedResult)
        http.close()

    def test_competitors_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).competitors(include_trends=True)
        assert isinstance(result, PagedResult)
        http.close()

    def test_aiso_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"aiso_score": 72.0})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).aiso(period="7d")
        assert reqs[0].url.params["period"] == "7d"
        http.close()

    def test_similar_pages_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"source": {}, "similar_pages": []})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).similar_pages("https://example.com/page", limit=5)
        assert reqs[0].url.params["url"] == "https://example.com/page"
        http.close()

    def test_analyze_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"analysis_id": "abc"})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).analyze("https://example.com/page")
        body = json.loads(reqs[0].content)
        assert body == {"url": "https://example.com/page"}
        http.close()

    def test_analysis_status_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"analysis_id": "abc", "status": "completed"})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).analysis_status("abc")
        assert b"/analyze/abc/" in reqs[0].url.raw_path
        http.close()

    def test_reports_delegates(self, api_key: str):
        data = make_paginated_response([{"id": 1}])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).reports()
        assert isinstance(result, PagedResult)
        http.close()

    def test_create_report_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"report_id": 42, "status": "queued"})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).create_report("last_month")
        body = json.loads(reqs[0].content)
        assert body == {"report_type": "last_month"}
        http.close()

    def test_report_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"id": 10})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).report(10)
        assert b"/reports/10/" in reqs[0].url.raw_path
        http.close()

    def test_report_pdf_delegates(self, api_key: str):
        pdf_bytes = b"%PDF-1.4"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=pdf_bytes)

        client, http = _make_sync_client(api_key, handler)
        result = client.website(DOMAIN).report_pdf(10)
        assert result == pdf_bytes
        http.close()

    def test_keywords_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).keywords(category="seo")
        assert isinstance(result, PagedResult)
        http.close()

    def test_page_keywords_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []
        data = make_paginated_response([])

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json=data)

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).page_keywords(42)
        assert b"/pages/42/keywords/" in reqs[0].url.raw_path
        http.close()

    def test_page_search_stats_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []
        data = make_paginated_response([])

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json=data)

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).page_search_stats(42, period="7d")
        assert b"/pages/42/search-stats/" in reqs[0].url.raw_path
        http.close()

    def test_page_metrics_history_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []
        data = make_paginated_response([])

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json=data)

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).page_metrics_history(42, period="90d")
        assert b"/pages/42/metrics-history/" in reqs[0].url.raw_path
        http.close()

    def test_backlinks_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).backlinks(status="active")
        assert isinstance(result, PagedResult)
        http.close()

    def test_backlink_domains_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).backlink_domains()
        assert isinstance(result, PagedResult)
        http.close()

    def test_accessibility_issues_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).accessibility_issues(severity="critical")
        assert isinstance(result, PagedResult)
        http.close()

    def test_changes_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).changes()
        assert isinstance(result, PagedResult)
        http.close()

    def test_content_decay_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).content_decay(is_active=True)
        assert isinstance(result, PagedResult)
        http.close()

    def test_gbp_locations_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"results": []})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).gbp_locations()
        assert b"/gbp/locations/" in reqs[0].url.raw_path
        http.close()

    def test_gbp_reviews_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_sync_client(api_key, lambda r: httpx.Response(200, json=data))
        result = client.website(DOMAIN).gbp_reviews(rating=5)
        assert isinstance(result, PagedResult)
        http.close()

    def test_reply_to_review_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"success": True, "review_id": 7, "reply": "Thanks!"})

        client, http = _make_sync_client(api_key, handler)
        client.website(DOMAIN).reply_to_review(7, "Thanks!")
        body = json.loads(reqs[0].content)
        assert body == {"reply": "Thanks!"}
        http.close()


# ---------------------------------------------------------------------------
# AsyncWebsiteResource
# ---------------------------------------------------------------------------


class TestAsyncWebsiteResource:
    def test_domain_property(self, api_key: str):
        client = AsyncSEOJuice(api_key)
        resource = client.website(DOMAIN)
        assert resource.domain == DOMAIN

    async def test_detail_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"domain": DOMAIN})

        client, http = _make_async_client(api_key, handler)
        result = await client.website(DOMAIN).detail()
        assert result["domain"] == DOMAIN
        await http.aclose()

    async def test_pages_delegates(self, api_key: str):
        data = make_paginated_response([{"id": 1}])
        client, http = _make_async_client(api_key, lambda r: httpx.Response(200, json=data))
        result = await client.website(DOMAIN).pages(page=1, page_size=10)
        assert isinstance(result, PagedResult)
        await http.aclose()

    async def test_page_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"id": 42})

        client, http = _make_async_client(api_key, handler)
        result = await client.website(DOMAIN).page(42)
        assert result["id"] == 42
        await http.aclose()

    async def test_links_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_async_client(api_key, lambda r: httpx.Response(200, json=data))
        result = await client.website(DOMAIN).links()
        assert isinstance(result, PagedResult)
        await http.aclose()

    async def test_intelligence_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"domain": DOMAIN})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).intelligence(period="7d", include_history=True)
        assert reqs[0].url.params["period"] == "7d"
        assert reqs[0].url.params["include_history"] == "true"
        await http.aclose()

    async def test_topology_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"total_pages": 50})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).topology()
        assert b"/topology/" in reqs[0].url.raw_path
        await http.aclose()

    async def test_analyze_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"analysis_id": "abc"})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).analyze("https://example.com/page")
        body = json.loads(reqs[0].content)
        assert body == {"url": "https://example.com/page"}
        await http.aclose()

    async def test_report_pdf_delegates(self, api_key: str):
        pdf_bytes = b"%PDF-1.4"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=pdf_bytes)

        client, http = _make_async_client(api_key, handler)
        result = await client.website(DOMAIN).report_pdf(10)
        assert result == pdf_bytes
        await http.aclose()

    async def test_create_report_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"report_id": 42})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).create_report("last_month")
        body = json.loads(reqs[0].content)
        assert body == {"report_type": "last_month"}
        await http.aclose()

    async def test_keywords_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_async_client(api_key, lambda r: httpx.Response(200, json=data))
        result = await client.website(DOMAIN).keywords(category="seo")
        assert isinstance(result, PagedResult)
        await http.aclose()

    async def test_backlinks_delegates(self, api_key: str):
        data = make_paginated_response([])
        client, http = _make_async_client(api_key, lambda r: httpx.Response(200, json=data))
        result = await client.website(DOMAIN).backlinks(status="active", dofollow=True)
        assert isinstance(result, PagedResult)
        await http.aclose()

    async def test_gbp_locations_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"results": []})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).gbp_locations()
        assert b"/gbp/locations/" in reqs[0].url.raw_path
        await http.aclose()

    async def test_reply_to_review_delegates(self, api_key: str):
        reqs: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            reqs.append(request)
            return httpx.Response(200, json={"success": True, "review_id": 7, "reply": "Thanks!"})

        client, http = _make_async_client(api_key, handler)
        await client.website(DOMAIN).reply_to_review(7, "Thanks!")
        body = json.loads(reqs[0].content)
        assert body == {"reply": "Thanks!"}
        await http.aclose()
