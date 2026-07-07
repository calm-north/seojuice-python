from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import NotRequired, TypedDict


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationMeta(TypedDict):
    page: int
    page_size: int
    total_count: int
    total_pages: int


# ---------------------------------------------------------------------------
# Websites
# ---------------------------------------------------------------------------


class WebsiteSummary(TypedDict):
    domain: str
    created_at: str


class WebsiteKPIs(TypedDict):
    total_links: int
    total_pages: int
    total_keywords: int


class WebsiteDetail(TypedDict):
    domain: str
    created_at: str
    last_processed_at: Optional[str]
    platform: Optional[str]
    industry: Optional[str]
    scores: Dict[str, Any]
    seo_score: Optional[float]
    report: Optional[Dict[str, Any]]
    kpis: WebsiteKPIs


class WebsiteListResponse(TypedDict):
    results: List[WebsiteSummary]


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


class LinkItem(TypedDict):
    page_from: str
    page_to: str
    keyword: Optional[str]
    created_at: Optional[str]
    impressions: int


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


class ReadabilityScores(TypedDict):
    flesch_kincaid: Optional[float]
    automated_readability: Optional[float]
    dale_chall: Optional[float]
    coleman_liau: Optional[float]


class PageSummary(TypedDict):
    id: int
    url: str
    title: Optional[str]
    page_type: Optional[str]
    seo_score: Optional[float]
    accessibility_score: Optional[float]
    meta_description: Optional[str]
    language_code: Optional[str]
    created_at: Optional[str]
    last_processed_at: Optional[str]
    readability: ReadabilityScores


class PageDetail(PageSummary):
    onpage_score: Optional[float]
    conversion_score: Optional[float]
    structured_data: Optional[Dict[str, Any]]
    has_structured_data: bool
    og_title: Optional[str]
    og_description: Optional[str]
    og_image: Optional[str]
    links: List[LinkItem]


# ---------------------------------------------------------------------------
# Intelligence
# ---------------------------------------------------------------------------


class IntelligenceHistory(TypedDict):
    dates: List[str]
    seo_scores: List[float]
    clicks: List[int]
    impressions: List[int]


class IntelligenceTrends(TypedDict):
    seo_score_change: float
    pages_change: int
    clicks_change_pct: float
    impressions_change_pct: float


class IntelligenceSummary(TypedDict):
    domain: str
    seo_score: float
    aiso_score: float
    total_pages: int
    total_clusters: int
    total_internal_links: int
    orphan_pages: int
    content_gaps: int
    last_crawled_at: Optional[str]
    history: NotRequired[IntelligenceHistory]
    trends: NotRequired[IntelligenceTrends]


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------


class TopologyPageItem(TypedDict):
    url: str
    title: str


class MostLinkedPage(TypedDict):
    url: str
    title: str
    incoming_links: int


class TopologyResponse(TypedDict):
    total_pages: int
    total_internal_links: int
    orphan_pages_count: int
    orphan_pages: List[TopologyPageItem]
    link_depth_distribution: Dict[str, int]
    avg_links_per_page: float
    most_linked_pages: List[MostLinkedPage]


# ---------------------------------------------------------------------------
# PageSpeed
# ---------------------------------------------------------------------------


class CoreWebVitals(TypedDict):
    lcp: Optional[float]
    cls: Optional[float]
    fid: Optional[float]
    inp: Optional[float]
    fcp: Optional[float]
    ttfb: Optional[float]


class PageSpeedScores(TypedDict):
    performance: Optional[float]
    accessibility: Optional[float]
    best_practices: Optional[float]
    seo: Optional[float]


class ResourceSizes(TypedDict):
    total_kb: Optional[float]
    js_kb: Optional[float]
    css_kb: Optional[float]
    image_kb: Optional[float]


class PageSpeedResponse(TypedDict):
    url: str
    loading_time: Optional[float]
    core_web_vitals: CoreWebVitals
    scores: PageSpeedScores
    resource_sizes: ResourceSizes
    measured_at: Optional[str]


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------


class ClusterSummary(TypedDict):
    id: int
    name: str
    slug: str
    page_count: int
    total_clicks: int
    avg_position: float


class ClusterKeyword(TypedDict):
    keyword: str
    impressions: int


class ClusterTimeSeries(TypedDict):
    dates: List[str]
    clicks: List[int]
    impressions: List[int]
    positions: List[float]


class ClusterDetail(ClusterSummary):
    top_keywords: List[ClusterKeyword]
    time_series: ClusterTimeSeries


# ---------------------------------------------------------------------------
# Content Gaps
# ---------------------------------------------------------------------------


class ContentGapKeyword(TypedDict):
    keyword: str
    rank_potential: int
    color: str


class ContentGap(TypedDict):
    id: int
    page_name: str
    category: str
    intent: str
    seo_potential: float
    total_search_volume: int
    keywords: List[ContentGapKeyword]
    aiso_driven: bool
    is_generated: bool
    has_potential_candidate: bool


# ---------------------------------------------------------------------------
# Competitors
# ---------------------------------------------------------------------------


class CompetitorKeyword(TypedDict):
    keyword: str
    your_position: int
    their_position: int
    volume: int


class CompetitorTrends(TypedDict):
    intersections_change: int
    traffic_change_pct: float
    keywords_change: int


class Competitor(TypedDict):
    id: int
    domain: str
    score: float
    intersections: int
    estimated_traffic: int
    content_gaps_count: int
    avg_position: float
    top_keywords: List[CompetitorKeyword]
    trends: NotRequired[CompetitorTrends]


# ---------------------------------------------------------------------------
# AISO
# ---------------------------------------------------------------------------


class AISOSubScores(TypedDict):
    visibility: float
    sentiment: float
    position: float
    coverage: float
    competitive: float


class AISOHistory(TypedDict):
    months: List[str]
    aiso_scores: List[float]
    total_mentions: List[int]
    your_mentions: List[int]


class AISOResponse(TypedDict):
    aiso_score: float
    sub_scores: AISOSubScores
    total_mentions: int
    your_mentions: int
    avg_position: float
    positive_rate: float
    providers: Dict[str, Any]
    history: NotRequired[AISOHistory]


# ---------------------------------------------------------------------------
# Similar Pages
# ---------------------------------------------------------------------------


class SimilarPageItem(TypedDict):
    url: str
    title: str
    similarity: float
    cluster: Optional[str]


class SimilarPagesResponse(TypedDict):
    source: TopologyPageItem
    similar_pages: List[SimilarPageItem]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


class AnalysisQueued(TypedDict):
    analysis_id: str
    url: str
    status: str
    status_url: str
    estimated_time_seconds: int


class AnalysisResult(TypedDict):
    analysis_id: str
    status: str
    url: str


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class ReportSummary(TypedDict):
    id: int
    type: str
    type_display: str
    status: str
    date: Optional[str]
    end_date: Optional[str]
    created_at: Optional[str]
    has_pdf: bool


class ReportDetail(ReportSummary):
    summary: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]
    updated_at: Optional[str]
    pdf_url: Optional[str]


class ReportCreated(TypedDict):
    report_id: int
    status: str
    status_url: str
    task_id: str


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------


class KeywordItem(TypedDict):
    id: int
    name: str
    page_url: Optional[str]
    category: Optional[str]
    search_volume: Optional[int]
    keyword_difficulty: Optional[int]
    cpc: Optional[float]
    competition: Optional[float]
    ai_search_volume: Optional[int]
    last_updated: Optional[str]


class PageKeywordStats(TypedDict):
    clicks: Optional[int]
    impressions: Optional[int]
    ctr: Optional[float]
    rank: Optional[float]


class PageKeyword(TypedDict):
    id: int
    keyword: str
    processed_at: Optional[str]
    stats: Optional[PageKeywordStats]


# ---------------------------------------------------------------------------
# Search Stats & Metrics
# ---------------------------------------------------------------------------


class SearchStat(TypedDict):
    date: Optional[str]
    clicks: Optional[int]
    impressions: Optional[int]
    ctr: Optional[float]
    rank: Optional[float]


class MetricsSnapshot(TypedDict):
    created_at: Optional[str]
    seo_score: Optional[float]
    onpage_score: Optional[float]
    accessibility_score: Optional[float]
    word_count: Optional[int]
    gsc_clicks: Optional[int]
    gsc_impressions: Optional[int]
    gsc_avg_position: Optional[float]
    gsc_ctr: Optional[float]
    is_orphan: bool
    total_incoming_links: Optional[int]
    total_outgoing_links: Optional[int]
    cwv_lcp: Optional[float]
    cwv_cls: Optional[float]
    cwv_fid: Optional[float]
    cwv_inp: Optional[float]
    cwv_fcp: Optional[float]
    cwv_ttfb: Optional[float]


# ---------------------------------------------------------------------------
# Backlinks
# ---------------------------------------------------------------------------


class BacklinkItem(TypedDict):
    id: int
    source_url: str
    target_url: str
    anchor_text: Optional[str]
    status: Optional[str]
    link_type: Optional[str]
    dofollow: bool
    nofollow: bool
    is_new: bool
    is_lost: bool
    page_from_rank: Optional[int]
    first_discovered_at: Optional[str]
    last_crawled_at: Optional[str]


class BacklinkDomain(TypedDict):
    id: int
    domain: str
    rank: Optional[int]
    spam_score: Optional[float]
    country: Optional[str]
    platform: Optional[str]
    tld: Optional[str]


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------


class AccessibilityIssue(TypedDict):
    id: int
    page_url: Optional[str]
    category: str
    severity: str
    wcag_criterion: Optional[str]
    description: Optional[str]
    fix_guidance: Optional[str]
    element_snippet: Optional[str]
    auto_fixable: bool
    auto_fixed: bool
    created_at: Optional[str]


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------


class ChangeRecord(TypedDict):
    id: int
    change_type: str
    status: str
    risk_level: Optional[str]
    page_url: Optional[str]
    proposed_value: Optional[str]
    previous_value: Optional[str]
    reason: Optional[str]
    confidence_score: Optional[float]
    anchor_text: Optional[str]
    alternatives: List[Any]
    original_issues: List[Any]
    optimization_techniques: List[Any]
    seo_signals_improved: List[Any]
    potential_risks: List[Any]
    related_changes: List[Any]
    llm_metadata: Dict[str, Any]
    created_at: Optional[str]
    reviewed_at: Optional[str]
    applied_at: Optional[str]
    pulled_at: Optional[str]
    pulled_by_integration: Optional[str]
    verified_at: Optional[str]
    reverted_at: Optional[str]
    revert_reason: Optional[str]
    batch_id: Optional[str]
    batch_label: Optional[str]
    edited_manually: bool


class ChangeStats(TypedDict):
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]


class ChangeSettings(TypedDict):
    internal_links_mode: str
    meta_tags_mode: str
    og_tags_mode: str
    title_tags_mode: str
    h1_tags_mode: str
    structured_data_mode: str
    image_alt_mode: str
    accessibility_mode: str
    local_seo_mode: str
    gbp_review_reply_mode: str
    max_changes_per_page_per_day: int
    max_changes_per_day: int
    exclude_paths: Optional[str]


class BulkActionResult(TypedDict):
    action: str
    succeeded: List[int]
    failed: List[Dict[str, Any]]
    total_succeeded: int
    total_failed: int


class ChangeWebhookPayload(TypedDict):
    event: str
    change: ChangeRecord
    website: Dict[str, str]
    timestamp: str
    rejected_by: NotRequired[str]
    reason: NotRequired[str]
    reverted_by: NotRequired[str]
    revert_reason: NotRequired[str]


# ---------------------------------------------------------------------------
# Content Decay
# ---------------------------------------------------------------------------


class ContentDecayAlert(TypedDict):
    id: int
    page_url: Optional[str]
    severity: str
    decay_type: str
    clicks_baseline: Optional[int]
    clicks_current: Optional[int]
    clicks_change_pct: Optional[float]
    impressions_baseline: Optional[int]
    impressions_current: Optional[int]
    impressions_change_pct: Optional[float]
    position_baseline: Optional[float]
    position_current: Optional[float]
    position_change_pct: Optional[float]
    is_active: bool
    detected_at: str
    resolved_at: Optional[str]
    suggestions: List[Any]


# ---------------------------------------------------------------------------
# Google Business Profile
# ---------------------------------------------------------------------------


class GBPLocation(TypedDict):
    id: int
    location_id: str
    name: str
    address: Optional[str]
    phone: Optional[str]
    average_rating: Optional[float]
    total_reviews: int
    last_fetched_at: Optional[str]


class GBPLocationsResponse(TypedDict):
    results: List[GBPLocation]


class GBPReview(TypedDict):
    id: int
    review_id: str
    location_name: str
    author_name: str
    rating: int
    comment: Optional[str]
    reply: Optional[str]
    reply_suggestion: Optional[str]
    sentiment: Optional[str]
    needs_attention: bool
    auto_replied: bool
    published_at: Optional[str]
    reply_posted_at: Optional[str]


class GBPReviewReplyResponse(TypedDict):
    success: bool
    review_id: int
    reply: str


# ---------------------------------------------------------------------------
# Action Items
# ---------------------------------------------------------------------------


class ActionItem(TypedDict):
    id: int
    title: str
    description: Optional[str]
    guidance: Optional[str]
    category: Optional[str]
    priority: Optional[str]
    status: str
    estimated_effort: Optional[str]
    auto_fixed: bool
    created_at: Optional[str]
    completed_at: Optional[str]
    affected_pages: List[Any]
    page: Optional[Dict[str, Any]]


class ActionItemSummary(TypedDict):
    total: int
    open: int
    done: int
    snoozed: int
    dismissed: int
    auto_fixed: int
    done_this_month: int
    completion_rate: float
    by_category: Dict[str, int]
    by_priority: Dict[str, int]


class ActionItemGroup(TypedDict):
    category: str
    count: int
    priority_distribution: Dict[str, int]


# ---------------------------------------------------------------------------
# Domain Health / SERP / Benchmarks / Content Quality / Geo
# ---------------------------------------------------------------------------


class DomainHealthResponse(TypedDict):
    domain: str
    score: float
    breakdown: Dict[str, Any]
    recommendations: List[Any]


class SERPLandscapeResponse(TypedDict):
    domain: str
    features: Dict[str, Any]


class BenchmarkResponse(TypedDict):
    domain: str
    benchmarks: Dict[str, Any]


class ContentQualityResponse(TypedDict):
    url: str
    score: float
    details: Dict[str, Any]


class GeoReadinessResponse(TypedDict):
    url: str
    score: float
    details: Dict[str, Any]


class PageContentResponse(TypedDict):
    url: str
    title: Optional[str]
    meta_description: Optional[str]
    content: Optional[str]
    raw_html: Optional[str]
    structured_data: Optional[Dict[str, Any]]
    language_code: Optional[str]
    page_type: Optional[str]
    images: List[Any]
