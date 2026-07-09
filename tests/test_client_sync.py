from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest

from seojuice._client import _clean_params
from seojuice._exceptions import (
    APIError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from seojuice._pagination import PagedResult
from seojuice._resource import WebsiteResource
from seojuice._sync import SEOJuice

from .conftest import (
    make_error_response,
    make_paginated_response,
    make_transport_handler,
)


# ---------------------------------------------------------------------------
# _clean_params
# ---------------------------------------------------------------------------


class TestCleanParams:
    def test_removes_none_values(self):
        result = _clean_params({"a": 1, "b": None, "c": "hello"})
        assert result == {"a": 1, "c": "hello"}

    def test_converts_bool_true_to_string(self):
        result = _clean_params({"flag": True})
        assert result == {"flag": "true"}

    def test_converts_bool_false_to_string(self):
        result = _clean_params({"flag": False})
        assert result == {"flag": "false"}

    def test_preserves_non_bool_non_none_values(self):
        result = _clean_params({"page": 1, "name": "test", "score": 0.5})
        assert result == {"page": 1, "name": "test", "score": 0.5}

    def test_empty_dict_returns_empty(self):
        assert _clean_params({}) == {}

    def test_all_none_returns_empty(self):
        assert _clean_params({"a": None, "b": None}) == {}

    def test_mixed_types(self):
        result = _clean_params(
            {
                "page": 1,
                "active": True,
                "deleted": False,
                "name": None,
                "query": "seo",
            }
        )
        assert result == {
            "page": 1,
            "active": "true",
            "deleted": "false",
            "query": "seo",
        }


# ---------------------------------------------------------------------------
# Client construction
# ---------------------------------------------------------------------------


class TestSEOJuiceConstruction:
    def test_creates_client_with_correct_base_url(self, api_key: str):
        client = SEOJuice(api_key)
        assert client._base_url == "https://seojuice.com/api/v2"
        client.close()

    def test_strips_trailing_slash_from_base_url(self, api_key: str):
        client = SEOJuice(api_key, base_url="https://example.com/api/")
        assert client._base_url == "https://example.com/api"
        client.close()

    def test_sets_bearer_auth_header(self, api_key: str):
        client = SEOJuice(api_key)
        assert client._client.headers["authorization"] == f"Bearer {api_key}"
        client.close()

    def test_sets_user_agent_header(self, api_key: str):
        import seojuice

        client = SEOJuice(api_key)
        assert (
            client._client.headers["user-agent"]
            == f"seojuice-python/{seojuice.__version__}"
        )
        client.close()

    def test_sets_accept_json_header(self, api_key: str):
        client = SEOJuice(api_key)
        assert client._client.headers["accept"] == "application/json"
        client.close()

    def test_custom_timeout(self, api_key: str):
        client = SEOJuice(api_key, timeout=60.0)
        assert client._client.timeout.read == 60.0
        client.close()

    def test_owns_client_when_no_http_client_provided(self, api_key: str):
        client = SEOJuice(api_key)
        assert client._owns_client is True
        client.close()

    def test_does_not_own_client_when_http_client_provided(self, api_key: str):
        custom = httpx.Client()
        client = SEOJuice(api_key, http_client=custom)
        assert client._owns_client is False
        assert client._client is custom
        client.close()
        custom.close()


class TestApiKeyValidation:
    @pytest.mark.parametrize("bad_key", [None, "", "   "])
    def test_falsy_api_key_raises_value_error(self, bad_key):
        with pytest.raises(ValueError, match="api_key is required"):
            SEOJuice(bad_key)

    def test_valid_api_key_constructs(self):
        client = SEOJuice("sk_live_123")
        assert client._api_key == "sk_live_123"
        client.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager_returns_self(self, api_key: str):
        with SEOJuice(api_key) as client:
            assert isinstance(client, SEOJuice)

    def test_context_manager_closes_owned_client(self, api_key: str):
        transport = make_transport_handler()
        http_client = httpx.Client(transport=transport)
        client = SEOJuice(api_key, http_client=http_client)
        client._owns_client = True
        with client:
            pass
        assert http_client.is_closed

    def test_context_manager_does_not_close_unowned_client(self, api_key: str):
        transport = make_transport_handler()
        http_client = httpx.Client(transport=transport)
        with SEOJuice(api_key, http_client=http_client):
            pass
        assert not http_client.is_closed
        http_client.close()


# ---------------------------------------------------------------------------
# Website resource proxy
# ---------------------------------------------------------------------------


class TestWebsiteResourceProxy:
    def test_website_returns_website_resource(self, api_key: str):
        transport = make_transport_handler()
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)
        resource = client.website("example.com")
        assert isinstance(resource, WebsiteResource)
        assert resource.domain == "example.com"
        http_client.close()


# ---------------------------------------------------------------------------
# Endpoint methods - GET requests
# ---------------------------------------------------------------------------


class TestListWebsites:
    def test_calls_get_websites(
        self, api_key: str, sample_websites_list: Dict[str, Any]
    ):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=sample_websites_list)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.list_websites()

        assert len(requests_made) == 1
        assert requests_made[0].method == "GET"
        assert requests_made[0].url.raw_path == b"/api/v2/websites/"
        assert result == sample_websites_list
        http_client.close()


class TestGetWebsite:
    def test_calls_get_website_with_domain(
        self, api_key: str, sample_website: Dict[str, Any]
    ):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=sample_website)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.get_website("example.com")

        assert requests_made[0].url.raw_path == b"/api/v2/websites/example.com/"
        assert result["domain"] == "example.com"
        http_client.close()


class TestListPages:
    def test_calls_get_pages_with_pagination_params(
        self,
        api_key: str,
        sample_paginated_pages: Dict[str, Any],
    ):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=sample_paginated_pages)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.list_pages("example.com", page=2, page_size=25)

        assert isinstance(result, PagedResult)
        url = requests_made[0].url
        assert b"/api/v2/websites/example.com/pages/" in url.raw_path
        assert url.params["page"] == "2"
        assert url.params["page_size"] == "25"
        http_client.close()


class TestGetIntelligence:
    def test_passes_query_params(self, api_key: str):
        intelligence_data = {
            "domain": "example.com",
            "seo_score": 85.0,
            "aiso_score": 72.0,
            "total_pages": 50,
            "total_clusters": 5,
            "total_internal_links": 200,
            "orphan_pages": 3,
            "content_gaps": 10,
            "last_crawled_at": None,
        }
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=intelligence_data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        client.get_intelligence(
            "example.com",
            period="7d",
            include_history=True,
            include_trends=True,
        )

        url = requests_made[0].url
        assert url.params["period"] == "7d"
        assert url.params["include_history"] == "true"
        assert url.params["include_trends"] == "true"
        http_client.close()

    def test_boolean_false_converted_to_string(self, api_key: str):
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json={"domain": "example.com"})

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        client.get_intelligence(
            "example.com", include_history=False, include_trends=False
        )

        url = requests_made[0].url
        assert url.params["include_history"] == "false"
        assert url.params["include_trends"] == "false"
        http_client.close()


# ---------------------------------------------------------------------------
# Endpoint methods - POST requests
# ---------------------------------------------------------------------------


class TestAnalyzePage:
    def test_sends_post_with_url_in_body(self, api_key: str):
        requests_made: List[httpx.Request] = []
        response_data = {
            "analysis_id": "abc-123",
            "url": "https://example.com/page",
            "status": "queued",
            "status_url": "/api/v2/websites/example.com/analyze/abc-123/",
            "estimated_time_seconds": 30,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=response_data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.analyze_page("example.com", "https://example.com/page")

        assert requests_made[0].method == "POST"
        body = json.loads(requests_made[0].content)
        assert body == {"url": "https://example.com/page"}
        assert result["analysis_id"] == "abc-123"
        http_client.close()


class TestCreateReport:
    def test_sends_post_with_report_type(self, api_key: str):
        requests_made: List[httpx.Request] = []
        response_data = {
            "report_id": 42,
            "status": "queued",
            "status_url": "/api/v2/websites/example.com/reports/42/",
            "task_id": "task-xyz",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=response_data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.create_report("example.com", "last_month")

        body = json.loads(requests_made[0].content)
        assert body == {"type": "last_month"}
        assert result["report_id"] == 42
        http_client.close()


# ---------------------------------------------------------------------------
# Binary download
# ---------------------------------------------------------------------------


class TestDownloadReportPdf:
    def test_returns_bytes(self, api_key: str):
        pdf_bytes = b"%PDF-1.4 fake pdf content"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=pdf_bytes)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.download_report_pdf("example.com", 42)
        assert result == pdf_bytes
        http_client.close()

    def test_raises_on_error_status(self, api_key: str):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404,
                json=make_error_response("not_found", "Report not found"),
            )

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        with pytest.raises(NotFoundError):
            client.download_report_pdf("example.com", 999)
        http_client.close()


# ---------------------------------------------------------------------------
# Paginated methods return PagedResult
# ---------------------------------------------------------------------------


class TestPaginatedEndpoints:
    def _make_client(
        self,
        api_key: str,
        response_data: Dict[str, Any],
    ) -> tuple[SEOJuice, httpx.Client]:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=response_data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        return SEOJuice(api_key, http_client=http_client), http_client

    def test_list_links_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"page_from": "/a", "page_to": "/b"}])
        client, http = self._make_client(api_key, data)
        result = client.list_links("example.com")
        assert isinstance(result, PagedResult)
        assert len(result) == 1
        http.close()

    def test_list_clusters_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "name": "Cluster A"}])
        client, http = self._make_client(api_key, data)
        result = client.list_clusters("example.com")
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_content_gaps_passes_optional_filters(self, api_key: str):
        requests_made: List[httpx.Request] = []
        data = make_paginated_response([])

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        client.list_content_gaps("example.com", category="seo", intent="informational")

        url = requests_made[0].url
        assert url.params["category"] == "seo"
        assert url.params["intent"] == "informational"
        http_client.close()

    def test_list_content_gaps_omits_none_filters(self, api_key: str):
        requests_made: List[httpx.Request] = []
        data = make_paginated_response([])

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        client.list_content_gaps("example.com")

        url = requests_made[0].url
        assert "category" not in url.params
        assert "intent" not in url.params
        http_client.close()

    def test_list_competitors_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "domain": "rival.com"}])
        client, http = self._make_client(api_key, data)
        result = client.list_competitors("example.com", include_trends=True)
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_reports_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "type": "this_month"}])
        client, http = self._make_client(api_key, data)
        result = client.list_reports("example.com")
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_keywords_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "name": "seo tools"}])
        client, http = self._make_client(api_key, data)
        result = client.list_keywords("example.com")
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_backlinks_returns_paged_result(self, api_key: str):
        data = make_paginated_response(
            [{"id": 1, "source_url": "https://blog.com/link"}]
        )
        client, http = self._make_client(api_key, data)
        result = client.list_backlinks("example.com", status="active", dofollow=True)
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_accessibility_issues_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "category": "contrast"}])
        client, http = self._make_client(api_key, data)
        result = client.list_accessibility_issues("example.com", severity="critical")
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_changes_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "change_type": "title"}])
        client, http = self._make_client(api_key, data)
        result = client.list_changes("example.com")
        assert isinstance(result, PagedResult)
        http.close()

    def test_list_content_decay_returns_paged_result(self, api_key: str):
        data = make_paginated_response([{"id": 1, "severity": "high"}])
        client, http = self._make_client(api_key, data)
        result = client.list_content_decay("example.com", is_active=True)
        assert isinstance(result, PagedResult)
        http.close()


# ---------------------------------------------------------------------------
# Non-paginated GET endpoints
# ---------------------------------------------------------------------------


class TestSimpleGetEndpoints:
    def _make_client(
        self,
        api_key: str,
        response_data: Dict[str, Any],
    ) -> tuple[SEOJuice, httpx.Client, List[httpx.Request]]:
        requests_made: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_made.append(request)
            return httpx.Response(200, json=response_data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        return SEOJuice(api_key, http_client=http_client), http_client, requests_made

    def test_get_page(self, api_key: str, sample_page: Dict[str, Any]):
        client, http, reqs = self._make_client(api_key, sample_page)
        result = client.get_page("example.com", 1)
        assert b"/api/v2/websites/example.com/pages/1/" in reqs[0].url.raw_path
        assert result["id"] == 1
        http.close()

    def test_get_topology(self, api_key: str):
        data = {"total_pages": 50, "total_internal_links": 200}
        client, http, reqs = self._make_client(api_key, data)
        result = client.get_topology("example.com")
        assert b"/api/v2/websites/example.com/topology/" in reqs[0].url.raw_path
        http.close()

    def test_get_pagespeed(self, api_key: str):
        data = {"url": "https://example.com", "loading_time": 1.5}
        client, http, reqs = self._make_client(api_key, data)
        result = client.get_pagespeed("example.com", "https://example.com")
        assert reqs[0].url.params["url"] == "https://example.com"
        http.close()

    def test_get_cluster(self, api_key: str):
        data = {"id": 5, "name": "Tech Cluster"}
        client, http, reqs = self._make_client(api_key, data)
        client.get_cluster("example.com", 5)
        assert b"/api/v2/websites/example.com/clusters/5/" in reqs[0].url.raw_path
        http.close()

    def test_get_aiso(self, api_key: str):
        data = {"aiso_score": 72.0}
        client, http, reqs = self._make_client(api_key, data)
        client.get_aiso("example.com", period="7d", include_history=True)
        assert reqs[0].url.params["period"] == "7d"
        assert reqs[0].url.params["include_history"] == "true"
        http.close()

    def test_get_similar_pages(self, api_key: str):
        data = {"source": {"url": "/page", "title": "Page"}, "similar_pages": []}
        client, http, reqs = self._make_client(api_key, data)
        client.get_similar_pages("example.com", "https://example.com/page", limit=5)
        assert reqs[0].url.params["url"] == "https://example.com/page"
        assert reqs[0].url.params["limit"] == "5"
        http.close()

    def test_get_analysis_status(self, api_key: str):
        data = {
            "analysis_id": "abc-123",
            "status": "completed",
            "url": "https://example.com",
        }
        client, http, reqs = self._make_client(api_key, data)
        client.get_analysis_status("example.com", "abc-123")
        assert b"/api/v2/websites/example.com/analyze/abc-123/" in reqs[0].url.raw_path
        http.close()

    def test_get_report(self, api_key: str):
        data = {"id": 10, "type": "this_month", "status": "completed"}
        client, http, reqs = self._make_client(api_key, data)
        client.get_report("example.com", 10)
        assert b"/api/v2/websites/example.com/reports/10/" in reqs[0].url.raw_path
        http.close()

    def test_list_gbp_locations(self, api_key: str):
        data = {"results": [{"id": 1, "name": "Main Office"}]}
        client, http, reqs = self._make_client(api_key, data)
        client.list_gbp_locations("example.com")
        assert b"/api/v2/websites/example.com/gbp/locations/" in reqs[0].url.raw_path
        http.close()

    def test_reply_to_gbp_review(self, api_key: str):
        data = {"success": True, "review_id": 7, "reply": "Thanks!"}
        client, http, reqs = self._make_client(api_key, data)
        client.reply_to_gbp_review("example.com", 7, "Thanks!")
        body = json.loads(reqs[0].content)
        assert body == {"reply_text": "Thanks!"}
        assert reqs[0].method == "POST"
        http.close()


# ---------------------------------------------------------------------------
# Error response handling
# ---------------------------------------------------------------------------


class TestErrorResponses:
    @pytest.mark.parametrize(
        "status,error_cls",
        [
            (401, AuthError),
            (403, ForbiddenError),
            (404, NotFoundError),
            (429, RateLimitError),
            (500, ServerError),
            (400, APIError),
        ],
    )
    def test_request_raises_correct_exception(
        self,
        api_key: str,
        status: int,
        error_cls: type,
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status,
                json=make_error_response("test_error", "Test message"),
            )

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        with pytest.raises(error_cls):
            client.list_websites()
        http_client.close()


# ---------------------------------------------------------------------------
# Paginated result with fallback pagination
# ---------------------------------------------------------------------------


class TestPaginationFallback:
    def test_missing_pagination_key_uses_defaults(self, api_key: str):
        """When the API response has no 'pagination' key, _paginate falls back."""
        data = {"results": [{"id": 1}, {"id": 2}]}

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=data)

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://seojuice.com/api/v2", transport=transport
        )
        client = SEOJuice(api_key, http_client=http_client)

        result = client.list_pages("example.com")
        assert isinstance(result, PagedResult)
        assert len(result) == 2
        assert result.pagination["page"] == 1
        assert result.pagination["total_pages"] == 1
        assert result.pagination["total_count"] == 2
        http_client.close()


# ---------------------------------------------------------------------------
# Error responses with non-JSON bodies (item 1)
# ---------------------------------------------------------------------------


class TestNonJsonErrorBodies:
    def _client(
        self, api_key: str, response: httpx.Response
    ) -> tuple[SEOJuice, httpx.Client]:
        def handler(request: httpx.Request) -> httpx.Response:
            return response

        transport = httpx.MockTransport(handler)
        http = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
        return SEOJuice(api_key, http_client=http), http

    def test_html_502_raises_server_error_not_jsondecode(self, api_key: str):
        resp = httpx.Response(
            502,
            headers={"content-type": "text/html"},
            content=b"<html>502 Bad Gateway</html>",
        )
        client, http = self._client(api_key, resp)
        with pytest.raises(ServerError) as exc_info:
            client.list_websites()
        assert exc_info.value.status_code == 502
        http.close()

    def test_empty_body_503_raises_server_error(self, api_key: str):
        resp = httpx.Response(503, content=b"")
        client, http = self._client(api_key, resp)
        with pytest.raises(ServerError):
            client.list_websites()
        http.close()

    def test_non_json_429_raises_rate_limit_error(self, api_key: str):
        resp = httpx.Response(
            429, headers={"content-type": "text/plain"}, content=b"Too Many Requests"
        )
        client, http = self._client(api_key, resp)
        with pytest.raises(RateLimitError):
            client.list_websites()
        http.close()

    def test_non_json_error_is_seojuice_error_subclass(self, api_key: str):
        from seojuice._exceptions import SEOJuiceError

        resp = httpx.Response(500, content=b"boom")
        client, http = self._client(api_key, resp)
        with pytest.raises(SEOJuiceError):
            client.list_websites()
        http.close()


# ---------------------------------------------------------------------------
# Transport errors wrapped into the typed hierarchy (item 4a)
# ---------------------------------------------------------------------------


class TestTransportErrorWrapping:
    def test_connect_timeout_raises_api_timeout_error(self, api_key: str):
        from seojuice._exceptions import APITimeoutError

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("connect timed out", request=request)

        transport = httpx.MockTransport(handler)
        http = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
        client = SEOJuice(api_key, http_client=http)
        with pytest.raises(APITimeoutError):
            client.list_websites()
        http.close()

    def test_connect_error_raises_api_connection_error(self, api_key: str):
        from seojuice._exceptions import APIConnectionError

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        transport = httpx.MockTransport(handler)
        http = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
        client = SEOJuice(api_key, http_client=http)
        with pytest.raises(APIConnectionError):
            client.list_websites()
        http.close()

    def test_timeout_is_catchable_as_seojuice_error(self, api_key: str):
        from seojuice._exceptions import SEOJuiceError

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timed out", request=request)

        transport = httpx.MockTransport(handler)
        http = httpx.Client(base_url="https://seojuice.com/api/v2", transport=transport)
        client = SEOJuice(api_key, http_client=http)
        with pytest.raises(SEOJuiceError):
            client.list_websites()
        http.close()
