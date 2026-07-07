from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

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
    PageSpeedResponse,
    ReportCreated,
    ReportDetail,
    ReportSummary,
    SERPLandscapeResponse,
    SimilarPagesResponse,
    TopologyResponse,
    WebsiteDetail,
)

if TYPE_CHECKING:
    from seojuice._async import AsyncSEOJuice
    from seojuice._client import _BaseClient


class WebsiteResource:
    """Domain-scoped proxy for synchronous API calls."""

    def __init__(self, client: _BaseClient, domain: str) -> None:
        self._client = client
        self._domain = domain

    @property
    def domain(self) -> str:
        return self._domain

    def detail(self) -> WebsiteDetail:
        return self._client.get_website(self._domain)

    def pages(self, **kwargs: Any) -> PagedResult[PageDetail]:
        return self._client.list_pages(self._domain, **kwargs)

    def page(self, page_id: int) -> PageDetail:
        return self._client.get_page(self._domain, page_id)

    def links(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_links(self._domain, **kwargs)

    def intelligence(self, **kwargs: Any) -> IntelligenceSummary:
        return self._client.get_intelligence(self._domain, **kwargs)

    def topology(self) -> TopologyResponse:
        return self._client.get_topology(self._domain)

    def pagespeed(self, url: str) -> PageSpeedResponse:
        return self._client.get_pagespeed(self._domain, url)

    def clusters(self, **kwargs: Any) -> PagedResult[ClusterSummary]:
        return self._client.list_clusters(self._domain, **kwargs)

    def cluster(self, cluster_id: int) -> ClusterDetail:
        return self._client.get_cluster(self._domain, cluster_id)

    def content_gaps(self, **kwargs: Any) -> PagedResult[ContentGap]:
        return self._client.list_content_gaps(self._domain, **kwargs)

    def competitors(self, **kwargs: Any) -> PagedResult[Competitor]:
        return self._client.list_competitors(self._domain, **kwargs)

    def aiso(self, **kwargs: Any) -> AISOResponse:
        return self._client.get_aiso(self._domain, **kwargs)

    def similar_pages(self, url: str, **kwargs: Any) -> SimilarPagesResponse:
        return self._client.get_similar_pages(self._domain, url, **kwargs)

    def analyze(self, url: str) -> AnalysisQueued:
        return self._client.analyze_page(self._domain, url)

    def analysis_status(self, analysis_id: str) -> AnalysisResult:
        return self._client.get_analysis_status(self._domain, analysis_id)

    def reports(self, **kwargs: Any) -> PagedResult[ReportSummary]:
        return self._client.list_reports(self._domain, **kwargs)

    def create_report(self, report_type: str = "this_month") -> ReportCreated:
        return self._client.create_report(self._domain, report_type)

    def report(self, report_id: int) -> ReportDetail:
        return self._client.get_report(self._domain, report_id)

    def report_pdf(self, report_id: int) -> bytes:
        return self._client.download_report_pdf(self._domain, report_id)

    def keywords(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_keywords(self._domain, **kwargs)

    def page_keywords(self, page_id: int, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_page_keywords(self._domain, page_id, **kwargs)

    def page_search_stats(self, page_id: int, **kwargs: Any) -> PagedResult[Any]:
        return self._client.get_page_search_stats(self._domain, page_id, **kwargs)

    def page_metrics_history(self, page_id: int, **kwargs: Any) -> PagedResult[Any]:
        return self._client.get_page_metrics_history(self._domain, page_id, **kwargs)

    def backlinks(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_backlinks(self._domain, **kwargs)

    def backlink_domains(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_backlink_domains(self._domain, **kwargs)

    def accessibility_issues(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_accessibility_issues(self._domain, **kwargs)

    def changes(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_changes(self._domain, **kwargs)

    def content_decay(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_content_decay(self._domain, **kwargs)

    def gbp_locations(self) -> GBPLocationsResponse:
        return self._client.list_gbp_locations(self._domain)

    def gbp_reviews(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_gbp_reviews(self._domain, **kwargs)

    def reply_to_review(
        self,
        review_id: int,
        reply_text: str,
    ) -> GBPReviewReplyResponse:
        return self._client.reply_to_gbp_review(self._domain, review_id, reply_text)

    # Changes management
    def change(self, change_id: int) -> ChangeRecord:
        return self._client.get_change(self._domain, change_id)

    def change_stats(self) -> ChangeStats:
        return self._client.get_change_stats(self._domain)

    def change_settings(self) -> ChangeSettings:
        return self._client.get_change_settings(self._domain)

    def update_change_settings(self, **settings: Any) -> ChangeSettings:
        return self._client.update_change_settings(self._domain, **settings)

    def approve_change(self, change_id: int) -> ChangeRecord:
        return self._client.approve_change(self._domain, change_id)

    def reject_change(self, change_id: int, **kwargs: Any) -> ChangeRecord:
        return self._client.reject_change(self._domain, change_id, **kwargs)

    def revert_change(self, change_id: int, **kwargs: Any) -> ChangeRecord:
        return self._client.revert_change(self._domain, change_id, **kwargs)

    def pull_change(self, change_id: int, **kwargs: Any) -> ChangeRecord:
        return self._client.pull_change(self._domain, change_id, **kwargs)

    def verify_change(self, change_id: int, **kwargs: Any) -> ChangeRecord:
        return self._client.verify_change(self._domain, change_id, **kwargs)

    def bulk_change_action(self, **kwargs: Any) -> BulkActionResult:
        return self._client.bulk_change_action(self._domain, **kwargs)

    # Action Items
    def action_items(self, **kwargs: Any) -> PagedResult[Any]:
        return self._client.list_action_items(self._domain, **kwargs)

    def action_item(self, item_id: int) -> ActionItem:
        return self._client.get_action_item(self._domain, item_id)

    def create_action_item(self, **kwargs: Any) -> ActionItem:
        return self._client.create_action_item(self._domain, **kwargs)

    def update_action_item(self, item_id: int, **kwargs: Any) -> ActionItem:
        return self._client.update_action_item(self._domain, item_id, **kwargs)

    def action_item_groups(self, **kwargs: Any) -> PagedResult[ActionItemGroup]:
        return self._client.get_action_item_groups(self._domain, **kwargs)

    def action_item_summary(self) -> ActionItemSummary:
        return self._client.get_action_item_summary(self._domain)

    # New endpoints
    def domain_health(self, **kwargs: Any) -> DomainHealthResponse:
        return self._client.get_domain_health(self._domain, **kwargs)

    def serp_landscape(self, **kwargs: Any) -> SERPLandscapeResponse:
        return self._client.get_serp_landscape(self._domain, **kwargs)

    def benchmarks(self) -> BenchmarkResponse:
        return self._client.get_benchmarks(self._domain)

    def content_quality(self, page_id: int, **kwargs: Any) -> ContentQualityResponse:
        return self._client.get_content_quality(self._domain, page_id, **kwargs)

    def geo_readiness(self, page_id: int, **kwargs: Any) -> GeoReadinessResponse:
        return self._client.get_geo_readiness(self._domain, page_id, **kwargs)

    def page_content(self, page_id: int) -> PageContentResponse:
        return self._client.get_page_content(self._domain, page_id)

    def submit_urls(self, **kwargs: Any) -> Dict[str, Any]:
        return self._client.submit_urls(self._domain, **kwargs)

    def url_status(self, **kwargs: Any) -> Dict[str, Any]:
        return self._client.get_url_status(self._domain, **kwargs)


class AsyncWebsiteResource:
    """Domain-scoped proxy for asynchronous API calls."""

    def __init__(self, client: AsyncSEOJuice, domain: str) -> None:
        self._client = client
        self._domain = domain

    @property
    def domain(self) -> str:
        return self._domain

    async def detail(self) -> WebsiteDetail:
        return await self._client._aget(f"/websites/{self._domain}/")

    async def pages(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> PagedResult[PageDetail]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/pages/",
            {"page": page, "page_size": page_size},
        )

    async def page(self, page_id: int) -> PageDetail:
        return await self._client._aget(f"/websites/{self._domain}/pages/{page_id}/")

    async def links(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/links/",
            {"page": page, "page_size": page_size},
        )

    async def intelligence(
        self,
        *,
        period: str = "30d",
        include_history: bool = False,
        include_trends: bool = False,
    ) -> IntelligenceSummary:
        return await self._client._aget(
            f"/websites/{self._domain}/intelligence/",
            {
                "period": period,
                "include_history": include_history,
                "include_trends": include_trends,
            },
        )

    async def topology(self) -> TopologyResponse:
        return await self._client._aget(f"/websites/{self._domain}/topology/")

    async def pagespeed(self, url: str) -> PageSpeedResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/pagespeed/",
            {"url": url},
        )

    async def clusters(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ClusterSummary]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/clusters/",
            {"page": page, "page_size": page_size},
        )

    async def cluster(self, cluster_id: int) -> ClusterDetail:
        return await self._client._aget(
            f"/websites/{self._domain}/clusters/{cluster_id}/",
        )

    async def content_gaps(
        self,
        *,
        category: Optional[str] = None,
        intent: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ContentGap]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/content-gaps/",
            {
                "category": category,
                "intent": intent,
                "page": page,
                "page_size": page_size,
            },
        )

    async def competitors(
        self,
        *,
        include_trends: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Competitor]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/competitors/",
            {
                "include_trends": include_trends,
                "page": page,
                "page_size": page_size,
            },
        )

    async def aiso(
        self,
        *,
        period: str = "30d",
        include_history: bool = False,
    ) -> AISOResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/aiso/",
            {"period": period, "include_history": include_history},
        )

    async def similar_pages(
        self,
        url: str,
        *,
        limit: int = 10,
    ) -> SimilarPagesResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/similar/",
            {"url": url, "limit": limit},
        )

    async def analyze(self, url: str) -> AnalysisQueued:
        return await self._client._apost(
            f"/websites/{self._domain}/analyze/",
            {"url": url},
        )

    async def analysis_status(self, analysis_id: str) -> AnalysisResult:
        return await self._client._aget(
            f"/websites/{self._domain}/analyze/{analysis_id}/",
        )

    async def reports(
        self,
        *,
        page: int = 1,
        page_size: int = 12,
    ) -> PagedResult[ReportSummary]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/reports/",
            {"page": page, "page_size": page_size},
        )

    async def create_report(
        self,
        report_type: str = "this_month",
    ) -> ReportCreated:
        return await self._client._apost(
            f"/websites/{self._domain}/reports/",
            {"type": report_type},
        )

    async def report(self, report_id: int) -> ReportDetail:
        return await self._client._aget(
            f"/websites/{self._domain}/reports/{report_id}/",
        )

    async def report_pdf(self, report_id: int) -> bytes:
        return await self._client._arequest_bytes(
            "GET",
            f"/websites/{self._domain}/reports/{report_id}/pdf/",
        )

    async def keywords(
        self,
        *,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/keywords/",
            {"category": category, "page": page, "page_size": page_size},
        )

    async def page_keywords(
        self,
        page_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/pages/{page_id}/keywords/",
            {"page": page, "page_size": page_size},
        )

    async def page_search_stats(
        self,
        page_id: int,
        *,
        period: str = "30d",
        page: int = 1,
        page_size: int = 30,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/pages/{page_id}/search-stats/",
            {"period": period, "page": page, "page_size": page_size},
        )

    async def page_metrics_history(
        self,
        page_id: int,
        *,
        period: str = "90d",
        page: int = 1,
        page_size: int = 30,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/pages/{page_id}/metrics-history/",
            {"period": period, "page": page, "page_size": page_size},
        )

    async def backlinks(
        self,
        *,
        status: Optional[str] = None,
        dofollow: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/backlinks/",
            {
                "status": status,
                "dofollow": dofollow,
                "page": page,
                "page_size": page_size,
            },
        )

    async def backlink_domains(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/backlink-domains/",
            {"page": page, "page_size": page_size},
        )

    async def accessibility_issues(
        self,
        *,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        auto_fixable: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/accessibility-issues/",
            {
                "severity": severity,
                "category": category,
                "auto_fixable": auto_fixable,
                "page": page,
                "page_size": page_size,
            },
        )

    async def changes(
        self,
        *,
        status: Optional[str] = None,
        change_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/changes/",
            {
                "status": status,
                "change_type": change_type,
                "risk_level": risk_level,
                "page": page,
                "page_size": page_size,
            },
        )

    async def content_decay(
        self,
        *,
        is_active: Optional[bool] = None,
        severity: Optional[str] = None,
        decay_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/content-decay/",
            {
                "is_active": is_active,
                "severity": severity,
                "decay_type": decay_type,
                "page": page,
                "page_size": page_size,
            },
        )

    async def gbp_locations(self) -> GBPLocationsResponse:
        return await self._client._aget(f"/websites/{self._domain}/gbp/locations/")

    async def gbp_reviews(
        self,
        *,
        rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        needs_attention: Optional[bool] = None,
        location_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/gbp/reviews/",
            {
                "rating": rating,
                "sentiment": sentiment,
                "needs_attention": needs_attention,
                "location_id": location_id,
                "page": page,
                "page_size": page_size,
            },
        )

    async def reply_to_review(
        self,
        review_id: int,
        reply_text: str,
    ) -> GBPReviewReplyResponse:
        return await self._client._apost(
            f"/websites/{self._domain}/gbp/reviews/{review_id}/reply/",
            {"reply_text": reply_text},
        )

    # Changes management
    async def change(self, change_id: int) -> ChangeRecord:
        return await self._client._aget(
            f"/websites/{self._domain}/changes/{change_id}/"
        )

    async def change_stats(self) -> ChangeStats:
        return await self._client._aget(
            f"/websites/{self._domain}/changes/stats/"
        )

    async def change_settings(self) -> ChangeSettings:
        return await self._client._aget(
            f"/websites/{self._domain}/changes/settings/"
        )

    async def update_change_settings(self, **settings: Any) -> ChangeSettings:
        return await self._client._apatch(
            f"/websites/{self._domain}/changes/settings/", settings
        )

    async def approve_change(self, change_id: int) -> ChangeRecord:
        return await self._client._apost(
            f"/websites/{self._domain}/changes/{change_id}/approve/"
        )

    async def reject_change(
        self, change_id: int, *, reason: Optional[str] = None
    ) -> ChangeRecord:
        body = {"reason": reason} if reason else None
        return await self._client._apost(
            f"/websites/{self._domain}/changes/{change_id}/reject/", body
        )

    async def revert_change(
        self, change_id: int, *, reason: Optional[str] = None
    ) -> ChangeRecord:
        body = {"reason": reason} if reason else None
        return await self._client._apost(
            f"/websites/{self._domain}/changes/{change_id}/revert/", body
        )

    async def pull_change(
        self, change_id: int, *, integration: str
    ) -> ChangeRecord:
        return await self._client._apost(
            f"/websites/{self._domain}/changes/{change_id}/pull/",
            {"integration": integration},
        )

    async def verify_change(
        self, change_id: int, *, integration: str
    ) -> ChangeRecord:
        return await self._client._apost(
            f"/websites/{self._domain}/changes/{change_id}/verify/",
            {"integration": integration},
        )

    async def bulk_change_action(
        self,
        *,
        action: str,
        ids: List[int],
        reason: Optional[str] = None,
        integration: Optional[str] = None,
    ) -> BulkActionResult:
        body: Dict[str, Any] = {"action": action, "ids": ids}
        if reason:
            body["reason"] = reason
        if integration:
            body["integration"] = integration
        return await self._client._apost(
            f"/websites/{self._domain}/changes/bulk/", body
        )

    # Action Items
    async def action_items(
        self,
        *,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        source_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[Any]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/action-items/",
            {
                "status": status,
                "category": category,
                "priority": priority,
                "source_type": source_type,
                "page": page,
                "page_size": page_size,
            },
        )

    async def action_item(self, item_id: int) -> ActionItem:
        return await self._client._aget(
            f"/websites/{self._domain}/action-items/{item_id}/"
        )

    async def create_action_item(
        self,
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
        return await self._client._apost(
            f"/websites/{self._domain}/action-items/", body
        )

    async def update_action_item(
        self,
        item_id: int,
        *,
        action: str,
        snooze_days: Optional[int] = None,
    ) -> ActionItem:
        body: Dict[str, Any] = {"action": action}
        if snooze_days is not None:
            body["snooze_days"] = snooze_days
        return await self._client._apatch(
            f"/websites/{self._domain}/action-items/{item_id}/", body
        )

    async def action_item_groups(
        self,
        *,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ActionItemGroup]:
        return await self._client._apaginate(
            f"/websites/{self._domain}/action-items/groups/",
            {"category": category, "page": page, "page_size": page_size},
        )

    async def action_item_summary(self) -> ActionItemSummary:
        return await self._client._aget(
            f"/websites/{self._domain}/action-items/summary/"
        )

    # New endpoints
    async def domain_health(
        self,
        *,
        recompute: Optional[bool] = None,
        domain_type: Optional[str] = None,
    ) -> DomainHealthResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/domain-health/",
            {"recompute": recompute, "domain_type": domain_type},
        )

    async def serp_landscape(
        self, *, market: Optional[str] = None
    ) -> SERPLandscapeResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/serp-landscape/", {"market": market}
        )

    async def benchmarks(self) -> BenchmarkResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/benchmarks/"
        )

    async def content_quality(
        self,
        page_id: Union[int, str],
        *,
        full_audit: Optional[bool] = None,
    ) -> ContentQualityResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/pages/{page_id}/content-quality/",
            {"full_audit": full_audit},
        )

    async def geo_readiness(
        self,
        page_id: Union[int, str],
        *,
        full_audit: Optional[bool] = None,
    ) -> GeoReadinessResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/pages/{page_id}/geo-readiness/",
            {"full_audit": full_audit},
        )

    async def page_content(self, page_id: Union[int, str]) -> PageContentResponse:
        return await self._client._aget(
            f"/websites/{self._domain}/pages/{page_id}/content/"
        )

    async def submit_urls(
        self, *, urls: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return await self._client._apost(
            f"/websites/{self._domain}/urls/", {"urls": urls}
        )

    async def url_status(self, *, url: str) -> Dict[str, Any]:
        return await self._client._aget(
            f"/websites/{self._domain}/urls/status/", {"url": url}
        )
