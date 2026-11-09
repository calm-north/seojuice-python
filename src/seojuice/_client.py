from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from seojuice._pagination import PagedResult
from seojuice._types import (
    ActionItem,
    ActionItemGroup,
    ActionItemSummary,
    AISOResponse,
    AnalysisQueued,
    AnalysisResult,
    BenchmarkResponse,
    BulkActionResult,
    ChangeRecord,
    ChangeSettings,
    ChangeStats,
    ClusterDetail,
    ClusterSummary,
    Competitor,
    ContentGap,
    ContentQualityResponse,
    DomainHealthResponse,
    GBPLocationsResponse,
    GBPReviewReplyResponse,
    GeoReadinessResponse,
    IntelligenceSummary,
    PageContentResponse,
    PageDetail,
    PageStatus,
    PageSpeedResponse,
    PaginationMeta,
    ReportCreated,
    ReportDetail,
    ReportSummary,
    SERPLandscapeResponse,
    SimilarPagesResponse,
    SubmitUrlsResponse,
    TopologyResponse,
    WebsiteDetail,
    WebsiteListResponse,
)


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values and convert booleans to lowercase strings."""
    cleaned: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = "true" if value else "false"
        else:
            cleaned[key] = value
    return cleaned


# The changes filter takes the legacy vocabulary (partners/views.py
# WebsiteChangesView); responses carry lifecycle names. Accept both.
_STATUS_FILTER = {
    "proposed": "pending",
    "live": "applied",
    "rolled_back": "reverted",
}

_ACTION_ITEM_ACTIONS = ("done", "in_progress", "dismiss", "reopen")


def _status_filter(status: Optional[str]) -> Optional[str]:
    return _STATUS_FILTER.get(status, status) if status else status


def _changes_params(
    status: Optional[str],
    change_type: Optional[str],
    risk_level: Optional[str],
    url: Optional[str],
    batch_id: Optional[str],
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    if risk_level is not None:
        warnings.warn(
            "risk_level is ignored by the server and is no longer sent",
            DeprecationWarning,
            stacklevel=3,
        )
    return {
        "status": _status_filter(status),
        "change_type": change_type,
        "url": url,
        "batch_id": batch_id,
        "page": page,
        "page_size": page_size,
    }


def _reject_body(reason: Optional[str]) -> Dict[str, Any]:
    if not reason or not reason.strip():
        raise ValueError("reason is required when rejecting a change")
    return {"reason": reason}


def _approve_body(confirm_heading: bool) -> Optional[Dict[str, Any]]:
    return {"confirm_heading": True} if confirm_heading else None


def _bulk_body(
    action: str,
    ids: Optional[List[int]],
    batch_id: Optional[str],
    reason: Optional[str],
    integration: Optional[str],
) -> Dict[str, Any]:
    if not ids and not batch_id:
        raise ValueError("ids or batch_id is required")
    body: Dict[str, Any] = {"action": action}
    if ids:
        body["ids"] = ids
    if batch_id:
        body["batch_id"] = batch_id
    if reason:
        body["reason"] = reason
    if integration:
        body["integration"] = integration
    return body


def _action_item_body(action: str) -> Dict[str, Any]:
    if action not in _ACTION_ITEM_ACTIONS:
        raise ValueError(
            f"action must be one of: {', '.join(_ACTION_ITEM_ACTIONS)}"
        )
    return {"action": action}


class _BaseClient(ABC):
    """Mixin providing all endpoint methods.

    Subclasses must implement ``_request`` (and ``_request_bytes`` for binary
    downloads).  The sync client uses these directly; the async client
    overrides them with coroutine equivalents.
    """

    @abstractmethod
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        ...

    @abstractmethod
    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        ...

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=_clean_params(params or {}))

    def _post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", path, json=json)

    def _patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PATCH", path, json=json)

    def _paginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PagedResult[Any]:
        data = self._get(path, params)
        pagination: PaginationMeta = data.get("pagination", {
            "page": 1,
            "page_size": len(data.get("results", [])),
            "total_count": len(data.get("results", [])),
            "total_pages": 1,
        })
        return PagedResult(results=data.get("results", []), pagination=pagination)

    # ------------------------------------------------------------------
    # Websites
    # ------------------------------------------------------------------

    def list_websites(self) -> WebsiteListResponse:
        return self._get("/websites/")

    def get_website(self, domain: str) -> WebsiteDetail:
        return self._get(f"/websites/{domain}/")

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def list_pages(
        self,
        domain: str,
        *,
        url: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PagedResult[PageDetail]:
        return self._paginate(
            f"/websites/{domain}/pages/",
            {"url": url, "page": page, "page_size": page_size},
        )

    def get_page(self, domain: str, page_id: int) -> PageDetail:
        return self._get(f"/websites/{domain}/pages/{page_id}/")

    # ------------------------------------------------------------------
    # Links
    # ------------------------------------------------------------------

    def list_links(
        self,
        domain: str,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/links/",
            {"page": page, "page_size": page_size},
        )

    # ------------------------------------------------------------------
    # Intelligence
    # ------------------------------------------------------------------

    def get_intelligence(
        self,
        domain: str,
        *,
        period: str = "30d",
        include_history: bool = False,
        include_trends: bool = False,
    ) -> IntelligenceSummary:
        return self._get(
            f"/websites/{domain}/intelligence/",
            {
                "period": period,
                "include_history": include_history,
                "include_trends": include_trends,
            },
        )

    # ------------------------------------------------------------------
    # Topology
    # ------------------------------------------------------------------

    def get_topology(self, domain: str) -> TopologyResponse:
        return self._get(f"/websites/{domain}/topology/")

    # ------------------------------------------------------------------
    # PageSpeed
    # ------------------------------------------------------------------

    def get_pagespeed(self, domain: str, url: str) -> PageSpeedResponse:
        return self._get(f"/websites/{domain}/pagespeed/", {"url": url})

    # ------------------------------------------------------------------
    # Clusters
    # ------------------------------------------------------------------

    def list_clusters(
        self,
        domain: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ClusterSummary]:
        return self._paginate(
            f"/websites/{domain}/clusters/",
            {"page": page, "page_size": page_size},
        )

    def get_cluster(self, domain: str, cluster_id: int) -> ClusterDetail:
        return self._get(f"/websites/{domain}/clusters/{cluster_id}/")

    # ------------------------------------------------------------------
    # Content Gaps
    # ------------------------------------------------------------------

    def list_content_gaps(
        self,
        domain: str,
        *,
        category: Optional[str] = None,
        intent: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ContentGap]:
        return self._paginate(
            f"/websites/{domain}/content-gaps/",
            {
                "category": category,
                "intent": intent,
                "page": page,
                "page_size": page_size,
            },
        )

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------

    def list_competitors(
        self,
        domain: str,
        *,
        include_trends: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Competitor]:
        return self._paginate(
            f"/websites/{domain}/competitors/",
            {
                "include_trends": include_trends,
                "page": page,
                "page_size": page_size,
            },
        )

    # ------------------------------------------------------------------
    # AISO
    # ------------------------------------------------------------------

    def get_aiso(
        self,
        domain: str,
        *,
        period: str = "30d",
        include_history: bool = False,
    ) -> AISOResponse:
        return self._get(
            f"/websites/{domain}/aiso/",
            {"period": period, "include_history": include_history},
        )

    # ------------------------------------------------------------------
    # Similar Pages
    # ------------------------------------------------------------------

    def get_similar_pages(
        self,
        domain: str,
        url: str,
        *,
        limit: int = 10,
    ) -> SimilarPagesResponse:
        return self._get(
            f"/websites/{domain}/similar/",
            {"url": url, "limit": limit},
        )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze_page(self, domain: str, url: str) -> AnalysisQueued:
        return self._post(
            f"/websites/{domain}/analyze/",
            {"url": url},
        )

    def get_analysis_status(
        self,
        domain: str,
        analysis_id: str,
    ) -> AnalysisResult:
        return self._get(f"/websites/{domain}/analyze/{analysis_id}/")

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def list_reports(
        self,
        domain: str,
        *,
        page: int = 1,
        page_size: int = 12,
    ) -> PagedResult[ReportSummary]:
        return self._paginate(
            f"/websites/{domain}/reports/",
            {"page": page, "page_size": page_size},
        )

    def create_report(
        self,
        domain: str,
        report_type: str = "this_month",
    ) -> ReportCreated:
        return self._post(
            f"/websites/{domain}/reports/",
            {"type": report_type},
        )

    def get_report(self, domain: str, report_id: int) -> ReportDetail:
        return self._get(f"/websites/{domain}/reports/{report_id}/")

    def download_report_pdf(self, domain: str, report_id: int) -> bytes:
        return self._request_bytes(
            "GET",
            f"/websites/{domain}/reports/{report_id}/pdf/",
        )

    # ------------------------------------------------------------------
    # Keywords
    # ------------------------------------------------------------------

    def list_keywords(
        self,
        domain: str,
        *,
        category: Optional[str] = None,
        include_serp: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/keywords/",
            {
                "category": category,
                "include_serp": include_serp,
                "page": page,
                "page_size": page_size,
            },
        )

    def list_page_keywords(
        self,
        domain: str,
        page_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/pages/{page_id}/keywords/",
            {"page": page, "page_size": page_size},
        )

    # ------------------------------------------------------------------
    # Page Search Stats & Metrics History
    # ------------------------------------------------------------------

    def get_page_search_stats(
        self,
        domain: str,
        page_id: int,
        *,
        period: str = "30d",
        page: int = 1,
        page_size: int = 30,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/pages/{page_id}/search-stats/",
            {"period": period, "page": page, "page_size": page_size},
        )

    def get_page_metrics_history(
        self,
        domain: str,
        page_id: int,
        *,
        period: str = "90d",
        page: int = 1,
        page_size: int = 30,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/pages/{page_id}/metrics-history/",
            {"period": period, "page": page, "page_size": page_size},
        )

    # ------------------------------------------------------------------
    # Backlinks
    # ------------------------------------------------------------------

    def list_backlinks(
        self,
        domain: str,
        *,
        status: Optional[str] = None,
        dofollow: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/backlinks/",
            {
                "status": status,
                "dofollow": dofollow,
                "page": page,
                "page_size": page_size,
            },
        )

    def list_backlink_domains(
        self,
        domain: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/backlink-domains/",
            {"page": page, "page_size": page_size},
        )

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------

    def list_accessibility_issues(
        self,
        domain: str,
        *,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        auto_fixable: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/accessibility-issues/",
            {
                "severity": severity,
                "category": category,
                "auto_fixable": auto_fixable,
                "page": page,
                "page_size": page_size,
            },
        )

    # ------------------------------------------------------------------
    # Changes
    # ------------------------------------------------------------------

    def list_changes(
        self,
        domain: str,
        *,
        status: Optional[str] = None,
        change_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        url: Optional[str] = None,
        batch_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/changes/",
            _changes_params(
                status, change_type, risk_level, url, batch_id, page, page_size
            ),
        )

    def get_change(self, domain: str, change_id: int) -> ChangeRecord:
        return self._get(f"/websites/{domain}/changes/{change_id}/")

    def get_change_stats(self, domain: str) -> ChangeStats:
        return self._get(f"/websites/{domain}/changes/stats/")

    def get_change_settings(self, domain: str) -> ChangeSettings:
        return self._get(f"/websites/{domain}/changes/settings/")

    def update_change_settings(
        self,
        domain: str,
        **settings: Any,
    ) -> ChangeSettings:
        return self._patch(f"/websites/{domain}/changes/settings/", settings)

    def approve_change(
        self,
        domain: str,
        change_id: int,
        *,
        confirm_heading: bool = False,
    ) -> ChangeRecord:
        return self._post(
            f"/websites/{domain}/changes/{change_id}/approve/",
            _approve_body(confirm_heading),
        )

    def reject_change(
        self,
        domain: str,
        change_id: int,
        *,
        reason: str,
    ) -> ChangeRecord:
        return self._post(
            f"/websites/{domain}/changes/{change_id}/reject/",
            _reject_body(reason),
        )

    def revert_change(
        self,
        domain: str,
        change_id: int,
        *,
        reason: Optional[str] = None,
    ) -> ChangeRecord:
        body = {"reason": reason} if reason else None
        return self._post(
            f"/websites/{domain}/changes/{change_id}/revert/", body
        )

    def pull_change(
        self,
        domain: str,
        change_id: int,
        *,
        integration: str,
    ) -> ChangeRecord:
        return self._post(
            f"/websites/{domain}/changes/{change_id}/pull/",
            {"integration": integration},
        )

    def verify_change(
        self,
        domain: str,
        change_id: int,
        *,
        integration: str,
    ) -> ChangeRecord:
        return self._post(
            f"/websites/{domain}/changes/{change_id}/verify/",
            {"integration": integration},
        )

    def bulk_change_action(
        self,
        domain: str,
        *,
        action: str,
        ids: Optional[List[int]] = None,
        batch_id: Optional[str] = None,
        reason: Optional[str] = None,
        integration: Optional[str] = None,
    ) -> BulkActionResult:
        return self._post(
            f"/websites/{domain}/changes/bulk/",
            _bulk_body(action, ids, batch_id, reason, integration),
        )

    # ------------------------------------------------------------------
    # Content Decay
    # ------------------------------------------------------------------

    def list_content_decay(
        self,
        domain: str,
        *,
        is_active: Optional[bool] = None,
        severity: Optional[str] = None,
        decay_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/content-decay/",
            {
                "is_active": is_active,
                "severity": severity,
                "decay_type": decay_type,
                "page": page,
                "page_size": page_size,
            },
        )

    # ------------------------------------------------------------------
    # Google Business Profile
    # ------------------------------------------------------------------

    def list_gbp_locations(self, domain: str) -> GBPLocationsResponse:
        return self._get(f"/websites/{domain}/gbp/locations/")

    def list_gbp_reviews(
        self,
        domain: str,
        *,
        rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        needs_attention: Optional[bool] = None,
        location_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/gbp/reviews/",
            {
                "rating": rating,
                "sentiment": sentiment,
                "needs_attention": needs_attention,
                "location_id": location_id,
                "page": page,
                "page_size": page_size,
            },
        )

    def reply_to_gbp_review(
        self,
        domain: str,
        review_id: int,
        reply_text: str,
    ) -> GBPReviewReplyResponse:
        return self._post(
            f"/websites/{domain}/gbp/reviews/{review_id}/reply/",
            {"reply_text": reply_text},
        )

    # ------------------------------------------------------------------
    # Action Items
    # ------------------------------------------------------------------

    def list_action_items(
        self,
        domain: str,
        *,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        source_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return self._paginate(
            f"/websites/{domain}/action-items/",
            {
                "status": status,
                "category": category,
                "priority": priority,
                "source_type": source_type,
                "page": page,
                "page_size": page_size,
            },
        )

    def get_action_item(self, domain: str, item_id: int) -> ActionItem:
        return self._get(f"/websites/{domain}/action-items/{item_id}/")

    def create_action_item(
        self,
        domain: str,
        *,
        title: str,
        description: Optional[str] = None,
        guidance: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        estimated_effort: Optional[str] = None,
    ) -> ActionItem:
        body: Dict[str, Any] = {"title": title}
        if description is not None:
            body["description"] = description
        if guidance is not None:
            body["guidance"] = guidance
        if category is not None:
            body["category"] = category
        if priority is not None:
            body["priority"] = priority
        if estimated_effort is not None:
            body["estimated_effort"] = estimated_effort
        return self._post(f"/websites/{domain}/action-items/", body)

    def update_action_item(
        self,
        domain: str,
        item_id: int,
        *,
        action: str,
    ) -> ActionItem:
        return self._patch(
            f"/websites/{domain}/action-items/{item_id}/",
            _action_item_body(action),
        )

    def get_action_item_groups(
        self,
        domain: str,
        *,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ActionItemGroup]:
        return self._paginate(
            f"/websites/{domain}/action-items/groups/",
            {"category": category, "page": page, "page_size": page_size},
        )

    def get_action_item_summary(self, domain: str) -> ActionItemSummary:
        return self._get(f"/websites/{domain}/action-items/summary/")

    # ------------------------------------------------------------------
    # Domain Health
    # ------------------------------------------------------------------

    def get_domain_health(
        self,
        domain: str,
        *,
        recompute: Optional[bool] = None,
        domain_type: Optional[str] = None,
    ) -> DomainHealthResponse:
        return self._get(
            f"/websites/{domain}/domain-health/",
            {"recompute": recompute, "domain_type": domain_type},
        )

    # ------------------------------------------------------------------
    # SERP Landscape
    # ------------------------------------------------------------------

    def get_serp_landscape(
        self,
        domain: str,
        *,
        market: Optional[str] = None,
    ) -> SERPLandscapeResponse:
        return self._get(
            f"/websites/{domain}/serp-landscape/", {"market": market}
        )

    # ------------------------------------------------------------------
    # Benchmarks
    # ------------------------------------------------------------------

    def get_benchmarks(self, domain: str) -> BenchmarkResponse:
        return self._get(f"/websites/{domain}/benchmarks/")

    # ------------------------------------------------------------------
    # Content Quality
    # ------------------------------------------------------------------

    def get_content_quality(
        self,
        domain: str,
        page_id: Union[int, str],
        *,
        full_audit: Optional[bool] = None,
    ) -> ContentQualityResponse:
        return self._get(
            f"/websites/{domain}/pages/{page_id}/content-quality/",
            {"full_audit": full_audit},
        )

    # ------------------------------------------------------------------
    # Geo Readiness
    # ------------------------------------------------------------------

    def get_geo_readiness(
        self,
        domain: str,
        page_id: Union[int, str],
        *,
        full_audit: Optional[bool] = None,
    ) -> GeoReadinessResponse:
        return self._get(
            f"/websites/{domain}/pages/{page_id}/geo-readiness/",
            {"full_audit": full_audit},
        )

    # ------------------------------------------------------------------
    # Page Content
    # ------------------------------------------------------------------

    def get_page_content(
        self,
        domain: str,
        page_id: Union[int, str],
    ) -> PageContentResponse:
        return self._get(f"/websites/{domain}/pages/{page_id}/content/")

    # ------------------------------------------------------------------
    # URL Submission
    # ------------------------------------------------------------------

    def submit_urls(
        self,
        domain: str,
        *,
        urls: List[Union[str, Dict[str, Any]]],
    ) -> SubmitUrlsResponse:
        return self._post(f"/websites/{domain}/urls/", {"urls": urls})

    def get_url_status(
        self,
        domain: str,
        *,
        url: str,
    ) -> PageStatus:
        return self._get(f"/websites/{domain}/urls/status/", {"url": url})
