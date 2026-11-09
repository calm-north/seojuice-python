"""SDK vs real server responses (tests/fixtures/api-fixtures).

Each fixture is a real v2 response body recorded with its request. The test
sends the SDK call through a strict transport (an unrouted request fails the
test), answers with the fixture, then checks the SDK return value against the
fixture and the TypedDict keys against the fixture body.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, get_args, get_origin

import httpx
import pytest
import typing_extensions as te

import seojuice._types as T
from seojuice import AsyncSEOJuice, SEOJuice
from seojuice._exceptions import (
    APIError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    PaymentRequiredError,
)
from seojuice._pagination import PagedResult

FIX = Path(__file__).parent / "fixtures"
API = FIX / "api-fixtures"
DOM = "fixtures.example"

INDEX = json.loads((API / "_index.json").read_text())
FIXTURES: Dict[str, Dict[str, Any]] = {
    n: json.loads((API / f"{n}.json").read_text()) for n in INDEX["fixtures"]
}


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def _listed(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for line in (FIX / "MANIFEST.sha256").read_text().splitlines():
            if line.strip():
                digest, rel = line.split(None, 1)
                out[rel.strip()] = digest
        return out

    def test_every_listed_file_matches_its_hash(self):
        listed = self._listed()
        assert listed
        for rel, digest in listed.items():
            actual = hashlib.sha256((FIX / rel).read_bytes()).hexdigest()
            assert actual == digest, rel

    def test_no_unlisted_fixture_file(self):
        on_disk = {
            str(p.relative_to(FIX))
            for p in FIX.rglob("*")
            if p.is_file() and p.name != "MANIFEST.sha256"
        }
        assert on_disk == set(self._listed())

    def test_index_lists_every_api_fixture(self):
        files = {p.stem for p in API.glob("*.json") if p.name != "_index.json"}
        assert files == set(INDEX["fixtures"])
        for name, status in INDEX["fixtures"].items():
            assert FIXTURES[name]["response"]["status"] == status


# ---------------------------------------------------------------------------
# Strict transport
# ---------------------------------------------------------------------------


class Served:
    def __init__(self, name: str, *, check_body: bool = True) -> None:
        self.fx = FIXTURES[name]
        self.check_body = check_body
        self.requests: List[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        req = self.fx["request"]
        pp = {k: str(v) for k, v in req["path_params"].items()}
        path = INDEX["api_base"] + req["path"].format(domain=DOM, **pp)
        assert (request.method, request.url.path) == (req["method"], path), (
            f"unrouted request {request.method} {request.url.path}"
        )
        got = dict(request.url.params)
        for k, v in (req["query"] or {}).items():
            assert got.get(k) == str(v), (k, got)
        if self.check_body:
            want = req["body"]
            sent = json.loads(request.content) if request.content else None
            if want:
                assert sent == want
            else:
                assert not sent
        resp = self.fx["response"]
        if resp.get("body_base64"):
            return httpx.Response(
                resp["status"],
                content=base64.b64decode(resp["body_base64"]),
                headers={"content-type": resp["content_type"]},
            )
        return httpx.Response(resp["status"], json=resp["body"])


def _sync(served: Served) -> SEOJuice:
    http = httpx.Client(transport=httpx.MockTransport(served), base_url="https://seojuice.com/api/v2")
    return SEOJuice("k", http_client=http)


def _async(served: Served) -> AsyncSEOJuice:
    http = httpx.AsyncClient(transport=httpx.MockTransport(served), base_url="https://seojuice.com/api/v2")
    return AsyncSEOJuice("k", http_client=http)


# ---------------------------------------------------------------------------
# Operation -> SDK call
# ---------------------------------------------------------------------------

G = "https://fixtures.example/guide/"

# Operations (success fixtures) -> call. `c` is SEOJuice or AsyncSEOJuice.
OK_CALLS: Dict[str, Callable[[Any], Any]] = {
    "list_websites": lambda c: c.list_websites(),
    "get_website": lambda c: c.get_website(DOM),
    "get_website_unlocked_on_single_plan": lambda c: c.get_website(DOM),
    "list_pages": lambda c: c.list_pages(DOM),
    "list_pages_paginated": lambda c: c.list_pages(DOM, page=2, page_size=1),
    "get_page": lambda c: c.get_page(DOM, 1),
    "list_links": lambda c: c.list_links(DOM),
    "get_intelligence": lambda c: c.get_intelligence(DOM),
    "get_intelligence_with_history": lambda c: c.get_intelligence(DOM, include_history=True, include_trends=True),
    "get_topology": lambda c: c.get_topology(DOM),
    "get_pagespeed": lambda c: c.get_pagespeed(DOM, G),
    "list_clusters": lambda c: c.list_clusters(DOM),
    "get_cluster": lambda c: c.get_cluster(DOM, 1),
    "list_content_gaps": lambda c: c.list_content_gaps(DOM),
    "list_competitors": lambda c: c.list_competitors(DOM),
    "list_competitors_with_trends": lambda c: c.list_competitors(DOM, include_trends=True),
    "get_aiso": lambda c: c.get_aiso(DOM),
    "analyze_page": lambda c: c.analyze_page(DOM, "https://fixtures.example/new-page/"),
    "get_analysis_status": lambda c: c.get_analysis_status(DOM, "analysis-done"),
    "list_reports": lambda c: c.list_reports(DOM),
    "create_report": lambda c: c.create_report(DOM, "last_week"),
    "get_report": lambda c: c.get_report(DOM, 1),
    "get_report_pdf": lambda c: c.download_report_pdf(DOM, 1),
    "list_keywords": lambda c: c.list_keywords(DOM),
    "list_keywords_with_serp": lambda c: c.list_keywords(DOM, include_serp=True),
    "list_page_keywords": lambda c: c.list_page_keywords(DOM, 1),
    "get_page_search_stats": lambda c: c.get_page_search_stats(DOM, 1),
    "get_page_metrics_history": lambda c: c.get_page_metrics_history(DOM, 1),
    "list_backlinks": lambda c: c.list_backlinks(DOM),
    "list_backlink_domains": lambda c: c.list_backlink_domains(DOM),
    "list_accessibility_issues": lambda c: c.list_accessibility_issues(DOM),
    "list_changes": lambda c: c.list_changes(DOM),
    "list_changes_filtered": lambda c: c.list_changes(DOM, status="pending", change_type="meta_description"),
    "get_change": lambda c: c.get_change(DOM, 1),
    "get_change_live": lambda c: c.get_change(DOM, 1),
    "get_change_stats": lambda c: c.get_change_stats(DOM),
    "get_change_settings": lambda c: c.get_change_settings(DOM),
    "update_change_settings": lambda c: c.update_change_settings(DOM, **FIXTURES["update_change_settings"]["request"]["body"]),
    "approve_change": lambda c: c.approve_change(DOM, 1),
    "approve_heading_confirmed": lambda c: c.approve_change(DOM, 1, confirm_heading=True),
    "reject_change": lambda c: c.reject_change(DOM, 1, reason="Does not match our tone"),
    "revert_change": lambda c: c.revert_change(DOM, 1, reason="Wrong title"),
    "pull_change": lambda c: c.pull_change(DOM, 1, integration="wordpress"),
    "verify_change": lambda c: c.verify_change(DOM, 1, integration="wordpress"),
    "bulk_approve_changes": lambda c: c.bulk_change_action(DOM, action="approve", ids=[1, 2, 3]),
    "list_content_decay": lambda c: c.list_content_decay(DOM),
    "list_gbp_locations": lambda c: c.list_gbp_locations(DOM),
    "list_gbp_reviews": lambda c: c.list_gbp_reviews(DOM),
    "list_gbp_reviews_needs_attention": lambda c: c.list_gbp_reviews(DOM, needs_attention=True),
    "reply_to_gbp_review": lambda c: c.reply_to_gbp_review(DOM, 1, "Sorry about that. Please call us."),
    "list_action_items": lambda c: c.list_action_items(DOM),
    "get_action_item": lambda c: c.get_action_item(DOM, 1),
    "create_action_item": lambda c: c.create_action_item(DOM, **{k: v for k, v in FIXTURES["create_action_item"]["request"]["body"].items()}),
    "update_action_item_done": lambda c: c.update_action_item(DOM, 1, action="done"),
    "get_action_item_groups": lambda c: c.get_action_item_groups(DOM),
    "get_action_item_summary": lambda c: c.get_action_item_summary(DOM),
    "get_domain_health": lambda c: c.get_domain_health(DOM),
    "get_serp_landscape": lambda c: c.get_serp_landscape(DOM),
    "get_benchmarks": lambda c: c.get_benchmarks(DOM),
    "get_page_content_quality": lambda c: c.get_content_quality(DOM, 1),
    "get_page_geo_readiness": lambda c: c.get_geo_readiness(DOM, 1),
    "get_page_content": lambda c: c.get_page_content(DOM, 1),
    "submit_urls": lambda c: c.submit_urls(DOM, urls=FIXTURES["submit_urls"]["request"]["body"]["urls"]),
    "get_url_status": lambda c: c.get_url_status(DOM, url="https://fixtures.example/pushed/"),
}

# Endpoints with no SDK method yet (out of scope this round).
NO_SDK_METHOD = {
    "create_website", "find_page", "get_link_analytics", "get_link_analytics_stats",
    "get_traffic_analytics", "get_report_summary", "get_search_performance",
    "get_search_performance_compare", "list_ai_blind_spots", "list_ai_citations",
    "list_ai_prompts", "list_keyword_movers", "list_content_pieces", "get_content_piece",
}

# Error fixtures -> call. Value (call, check_body). check_body False where the
# fixture request cannot be produced by the SDK (invalid JSON, missing field).
def _raw_post(path: str, body: Any = None):
    return lambda c: c._post(path, body)


def _raw_patch(path: str, body: Any = None):
    return lambda c: c._patch(path, body)


ERR_CALLS: Dict[str, Any] = {
    "analyze_page_missing_url": (_raw_post(f"/websites/{DOM}/analyze/"), True),
    "approve_change_not_proposed": (lambda c: c.approve_change(DOM, 1), True),
    "approve_heading_without_confirmation": (lambda c: c.approve_change(DOM, 1), True),
    "bulk_changes_invalid_action": (lambda c: c.bulk_change_action(DOM, action="explode", ids=[1]), True),
    "create_action_item_missing_title": (_raw_post(f"/websites/{DOM}/action-items/", {"category": "seo"}), True),
    "create_report_invalid_type": (lambda c: c.create_report(DOM, "yearly"), True),
    "create_website_already_exists": (_raw_post("/websites/", {"domain": "taken-client.com"}), True),
    "create_website_missing_domain": (_raw_post("/websites/"), True),
    "create_website_plan_limit": (_raw_post("/websites/", {"domain": "third-client.com"}), True),
    "error_400_invalid_json": (_raw_post(f"/websites/{DOM}/analyze/"), False),
    "error_400_invalid_pagination": (lambda c: c.list_pages(DOM, page=0), True),
    "error_400_missing_parameter": (lambda c: c._get(f"/websites/{DOM}/pagespeed/"), True),
    "error_401_empty_token": (lambda c: c.list_websites(), True),
    "error_401_invalid_token": (lambda c: c.list_websites(), True),
    "error_401_missing_token": (lambda c: c.list_websites(), True),
    "error_402_trial_required": (lambda c: c.get_website(DOM), True),
    "error_402_website_locked": (lambda c: c.get_website(DOM), True),
    "error_403_reports_not_in_plan": (lambda c: c.list_reports(DOM), True),
    "error_404_change_not_found": (lambda c: c.get_change(DOM, 1), True),
    "error_404_cluster_not_found": (lambda c: c.get_cluster(DOM, 1), True),
    "error_404_no_ai_monitoring": (lambda c: c._get(f"/websites/{DOM}/ai/prompts/"), True),
    "error_404_no_search_console": (lambda c: c._get(f"/websites/{DOM}/search-performance/"), True),
    "error_404_page_not_found": (lambda c: c.get_page(DOM, 1), True),
    "error_404_website_not_found": (lambda c: c.get_website(DOM), True),
    "error_404_website_not_found_alt_code": (lambda c: c.get_intelligence(DOM), True),
    "get_analysis_status_not_found": (lambda c: c.get_analysis_status(DOM, "nope"), True),
    "get_similar_pages": (lambda c: c.get_similar_pages(DOM, G), True),
    "pull_change_without_integration": (_raw_post(f"/websites/{DOM}/changes/1/pull/"), True),
    "reject_change_without_reason": (_raw_post(f"/websites/{DOM}/changes/1/reject/"), True),
    "reply_to_gbp_review_missing_text": (_raw_post(f"/websites/{DOM}/gbp/reviews/1/reply/"), True),
    "submit_urls_empty": (lambda c: c.submit_urls(DOM, urls=[]), True),
    "update_change_settings_invalid_mode": (lambda c: c.update_change_settings(DOM, meta_tags_mode="sometimes"), True),
}

EXPECTED_EXC = {401: AuthError, 402: PaymentRequiredError, 403: ForbiddenError, 404: NotFoundError}


def test_every_fixture_is_covered_or_listed_as_unsupported():
    covered = set(OK_CALLS) | set(ERR_CALLS) | NO_SDK_METHOD
    assert covered == set(FIXTURES)


# ---------------------------------------------------------------------------
# TypedDict keys vs fixture bodies
# ---------------------------------------------------------------------------

DICT_TYPES: Dict[str, str] = {
    "get_website": "WebsiteDetail", "get_page": "PageDetail", "get_intelligence": "IntelligenceSummary",
    "get_intelligence_with_history": "IntelligenceSummary", "get_topology": "TopologyResponse",
    "get_pagespeed": "PageSpeedResponse", "get_cluster": "ClusterDetail", "get_aiso": "AISOResponse",
    "analyze_page": "AnalysisQueued", "get_analysis_status": "AnalysisResult", "create_report": "ReportCreated",
    "get_report": "ReportDetail", "get_change": "ChangeRecord", "get_change_live": "ChangeRecord",
    "approve_change": "ChangeRecord", "approve_heading_confirmed": "ChangeRecord", "reject_change": "ChangeRecord",
    "revert_change": "ChangeRecord", "pull_change": "ChangeRecord", "verify_change": "ChangeRecord",
    "get_change_stats": "ChangeStats", "get_change_settings": "ChangeSettings", "update_change_settings": "ChangeSettings",
    "bulk_approve_changes": "BulkActionResult", "list_gbp_locations": "GBPLocationsResponse",
    "reply_to_gbp_review": "GBPReviewReplyResponse", "get_action_item": "ActionItem", "create_action_item": "ActionItem",
    "update_action_item_done": "ActionItem", "get_action_item_summary": "ActionItemSummary",
    "get_domain_health": "DomainHealthResponse", "get_serp_landscape": "SERPLandscapeResponse",
    "get_benchmarks": "BenchmarkResponse", "get_page_content_quality": "ContentQualityResponse",
    "get_page_geo_readiness": "GeoReadinessResponse", "get_page_content": "PageContentResponse",
    "submit_urls": "SubmitUrlsResponse", "get_url_status": "PageStatus",
}
ITEM_TYPES: Dict[str, str] = {
    "list_pages": "PageDetail", "list_links": "LinkItem", "list_clusters": "ClusterSummary",
    "list_content_gaps": "ContentGap", "list_competitors": "Competitor",
    "list_competitors_with_trends": "Competitor", "list_reports": "ReportSummary",
    "list_keywords": "KeywordItem", "list_page_keywords": "PageKeyword",
    "get_page_search_stats": "SearchStat", "get_page_metrics_history": "MetricsSnapshot",
    "list_backlinks": "BacklinkItem", "list_accessibility_issues": "AccessibilityIssue",
    "list_changes": "ChangeRecord", "list_content_decay": "ContentDecayAlert",
    "list_gbp_reviews": "GBPReview", "list_action_items": "ActionItem",
    "get_action_item_groups": "ActionItemGroup",
}


def _is_td(t: Any) -> bool:
    return isinstance(t, type) and hasattr(t, "__annotations__") and hasattr(t, "__total__")


def _unwrap(t: Any) -> Any:
    if get_origin(t) is Union:
        args = [a for a in get_args(t) if a is not type(None)]
        return _unwrap(args[0]) if len(args) == 1 else t
    return t


def _check(td: type, value: Any, where: str) -> None:
    hints = te.get_type_hints(td)
    raw = td.__annotations__
    required = {k for k, v in raw.items() if "NotRequired" not in str(v)}
    assert isinstance(value, dict), where
    missing = required - set(value)
    extra = set(value) - set(hints)
    assert not missing and not extra, f"{where} {td.__name__}: SDK-only={sorted(missing)} server-only={sorted(extra)}"
    for k, v in value.items():
        t = _unwrap(hints[k])
        if _is_td(t) and isinstance(v, dict):
            _check(t, v, f"{where}.{k}")
        elif get_origin(t) in (list, List) and v:
            inner = _unwrap(get_args(t)[0])
            if _is_td(inner) and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    _check(inner, item, f"{where}.{k}[{i}]")


def _case_ids(d: Dict[str, Any]) -> List[str]:
    return sorted(d)


def _run_sync(name: str, fn: Callable[[Any], Any], check_body: bool = True) -> Any:
    served = Served(name, check_body=check_body)
    c = _sync(served)
    try:
        return fn(c)
    finally:
        assert served.requests, "SDK sent no request"


async def _run_async(name: str, fn: Callable[[Any], Any], check_body: bool = True) -> Any:
    served = Served(name, check_body=check_body)
    c = _async(served)
    try:
        return await fn(c)
    finally:
        assert served.requests, "SDK sent no request"


def _assert_matches(name: str, out: Any) -> None:
    body = FIXTURES[name]["response"]["body"]
    if name == "get_report_pdf":
        assert out == base64.b64decode(FIXTURES[name]["response"]["body_base64"])
        return
    if isinstance(out, PagedResult):
        assert out.results == body["results"]
        assert out.pagination == body["pagination"]
        if name in ITEM_TYPES and body["results"]:
            for i, item in enumerate(body["results"]):
                _check(getattr(T, ITEM_TYPES[name]), item, f"{name}[{i}]")
        return
    assert out == body
    if name in DICT_TYPES:
        _check(getattr(T, DICT_TYPES[name]), body, name)
    if name in ITEM_TYPES:
        for i, item in enumerate(body["results"] if "results" in body else []):
            _check(getattr(T, ITEM_TYPES[name]), item, f"{name}[{i}]")
        if name == "list_gbp_locations":
            pass


@pytest.mark.parametrize("name", _case_ids(OK_CALLS))
def test_sync_success_matches_fixture(name: str):
    out = _run_sync(name, OK_CALLS[name])
    _assert_matches(name, out)


@pytest.mark.parametrize("name", _case_ids(OK_CALLS))
async def test_async_success_matches_fixture(name: str):
    out = await _run_async(name, OK_CALLS[name])
    _assert_matches(name, out)


def _assert_error(name: str, exc: APIError) -> None:
    resp = FIXTURES[name]["response"]
    body = resp["body"]
    status = resp["status"]
    assert exc.status_code == status
    assert exc.error_code == body["error"]
    assert exc.message == body["message"]
    want = EXPECTED_EXC.get(status)
    if want:
        assert type(exc) is want
    elif status >= 500:  # pragma: no cover
        raise AssertionError
    else:
        assert type(exc) is APIError
    if status == 402:
        assert exc.checkout_url == body["checkout_url"]  # type: ignore[attr-defined]
        assert exc.lock_state == body["lock_state"]  # type: ignore[attr-defined]


@pytest.mark.parametrize("name", _case_ids(ERR_CALLS))
def test_sync_error_maps_to_exception(name: str):
    fn, check_body = ERR_CALLS[name]
    with pytest.raises(APIError) as ei:
        _run_sync(name, fn, check_body)
    _assert_error(name, ei.value)


@pytest.mark.parametrize("name", _case_ids(ERR_CALLS))
async def test_async_error_maps_to_exception(name: str):
    fn, check_body = ERR_CALLS[name]
    with pytest.raises(APIError) as ei:
        await _run_async(name, fn, check_body)
    _assert_error(name, ei.value)


# ---------------------------------------------------------------------------
# What the fixtures cannot show
# ---------------------------------------------------------------------------


def test_empty_result_fixtures_only_show_the_envelope():
    # list_backlink_domains returns no items: the item TypedDict (BacklinkDomain)
    # is not checked against a real row. Weak spot, not proof.
    assert FIXTURES["list_backlink_domains"]["response"]["body"]["results"] == []
    out = _run_sync("list_backlink_domains", OK_CALLS["list_backlink_domains"])
    assert out.results == [] and out.pagination["total_count"] == 0


def test_async_resource_methods_hit_the_fixture_routes():
    # AsyncWebsiteResource has its own implementations; spot-check them against fixtures.
    import asyncio

    async def go() -> None:
        for name, call in {
            "list_pages": lambda w: w.pages(),
            "get_page": lambda w: w.page(1),
            "get_change": lambda w: w.change(1),
            "list_action_items": lambda w: w.action_items(),
            "get_action_item_summary": lambda w: w.action_item_summary(),
            "get_domain_health": lambda w: w.domain_health(),
            "get_page_content": lambda w: w.page_content(1),
            "get_report_pdf": lambda w: w.report_pdf(1),
        }.items():
            served = Served(name)
            c = _async(served)
            out = await call(c.website(DOM))
            _assert_matches(name, out)

    asyncio.run(go())


def test_enum_values_in_fixtures_are_typed():
    changes = [FIXTURES[n]["response"]["body"] for n in ("get_change", "get_change_live", "approve_change")]
    changes += FIXTURES["list_changes"]["response"]["body"]["results"]
    assert changes
    for ch in changes:
        assert ch["status"] in get_args(T.ChangeStatus)
        assert ch["change_type"] in get_args(T.ChangeType)
    reports = [FIXTURES["get_report"]["response"]["body"]]
    reports += FIXTURES["list_reports"]["response"]["body"]["results"]
    for r in reports:
        assert r["status"] in get_args(T.ReportStatus)
    assert get_args(T.ReportStatus) == ("not_set", "in_progress", "finished", "error")
    assert te.get_type_hints(T.ChangeRecord)["status"] == T.ChangeStatus
