from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

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
    domain_health_score: Optional[float]
    domain_health_breakdown: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    kpis: WebsiteKPIs
    avg_content_quality_score: Optional[float]
    avg_geo_readiness_score: Optional[float]


class WebsiteListResponse(TypedDict):
    results: List[WebsiteSummary]


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


class LinkItem(TypedDict):
    page_from: Optional[str]
    page_to: Optional[str]
    keyword: Optional[str]
    created_at: Optional[str]
    impressions: Optional[int]
    clicks: Optional[int]
    ctr: Optional[float]


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
    content_quality_score: Optional[float]
    geo_readiness_score: Optional[float]
    meta_description: Optional[str]
    language_code: Optional[str]
    created_at: Optional[str]
    last_processed_at: Optional[str]
    readability: ReadabilityScores
    excluded: bool
    is_key_page: bool
    onpage_score: Optional[float]
    conversion_score: Optional[float]
    structured_data: Optional[Dict[str, Any]]
    has_structured_data: bool
    og_title: Optional[str]
    og_description: Optional[str]
    og_image: Optional[str]
    links: List[LinkItem]
    content_quality_breakdown: Optional[Dict[str, Any]]
    geo_readiness_breakdown: Optional[Dict[str, Any]]


class PageDetail(PageSummary):
    pass


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
    domain_health_score: Optional[float]
    avg_content_quality_score: Optional[float]
    avg_geo_readiness_score: Optional[float]
    total_pages: int
    total_clusters: int
    total_internal_links: int
    total_seojuice_links: int
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
    tbt: Optional[float]
    speed_index: Optional[float]


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


class ClusterIssues(TypedDict):
    competing_queries: int
    pages_without_cluster_link: int
    close_to_page_1: int
    open_action_items: int


class ClusterQualityHistory(TypedDict):
    dates: List[str]
    seo_scores: List[float]
    performance_scores: List[float]
    accessibility_scores: List[float]
    best_practices_scores: List[float]


class ClusterSummary(TypedDict):
    id: int
    name: str
    slug: str
    page_count: int
    clicks: int
    impressions: int
    ctr: Optional[float]
    avg_position: Optional[float]
    clicks_change_pct: Optional[float]
    trend: str
    pillar: Optional[Dict[str, Any]]
    cohesion: Optional[float]
    issues: ClusterIssues
    is_active: bool


class ClusterKeyword(TypedDict):
    keyword: str
    impressions: int


class ClusterTimeSeries(TypedDict):
    week_start: str
    clicks: int
    impressions: int


class ClusterDetail(ClusterSummary):
    time_series: List[ClusterTimeSeries]
    top_queries: List[Any]
    quality_history: ClusterQualityHistory


# ---------------------------------------------------------------------------
# Content Gaps
# ---------------------------------------------------------------------------


class ContentGapKeyword(TypedDict):
    keyword: str
    search_volume: Optional[int]
    keyword_difficulty: Optional[float]
    rank_potential: Optional[int]


class ContentGap(TypedDict):
    id: int
    page_name: str
    category: str
    intent: str
    seo_potential: float
    relevance: Optional[float]
    total_search_volume: int
    estimated_traffic_potential: Optional[int]
    keywords: List[ContentGapKeyword]
    aiso_driven: bool
    is_dismissed: bool
    is_generated: bool
    has_potential_candidate: bool
    created_at: Optional[str]


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
    intersections: Optional[int]
    estimated_traffic: Optional[int]
    content_gaps_count: int
    avg_position: Optional[float]
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
    cluster: NotRequired[Optional[str]]
    page_id: NotRequired[Optional[int]]
    is_orphan: NotRequired[bool]
    seo_score: NotRequired[Optional[float]]
    depth_from_homepage: NotRequired[Optional[int]]
    completed_at: NotRequired[Optional[str]]
    error_message: NotRequired[str]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


# Values the server sends in ``ReportSummary.status``.
ReportStatus = Literal["not_set", "in_progress", "finished", "error"]


class ReportSummary(TypedDict):
    id: int
    type: str
    type_display: str
    status: ReportStatus
    date: Optional[str]
    end_date: Optional[str]
    created_at: Optional[str]
    has_pdf: bool


class ReportDetail(ReportSummary):
    summary: Optional[str]
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
    created_at: Optional[str]


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
    cwv_performance_score: Optional[float]
    content_quality_score: Optional[float]
    geo_readiness_score: Optional[float]


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


# Values the server sends in ``ChangeRecord.status`` (ChangeSet lifecycle).
ChangeStatus = Literal[
    "proposed",
    "approved",
    "live",
    "rolled_back",
    "rejected",
    "superseded",
    "stale",
    "expired",
]

# Values the server sends in ``ChangeRecord.change_type``.
ChangeType = Literal[
    "title_tag",
    "h1_tag",
    "meta_description",
    "meta_keywords",
    "og_title",
    "og_description",
    "og_image",
    "internal_link",
    "local_schema",
    "nap_fix",
    "structured_data",
    "image_alt",
    "accessibility",
    "broken_link_fix",
    "content_patch",
]

ActionItemAction = Literal["done", "in_progress", "dismiss", "reopen"]


class ChangeRecord(TypedDict):
    id: int
    change_type: ChangeType
    status: ChangeStatus
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
    mutation_type: str
    verification_state: str
    outcome_state: str
    apply: Optional[Dict[str, Any]]


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
    signal_type: str
    severity: str
    is_active: bool
    detected_at: str
    resolved_at: Optional[str]
    metrics: Dict[str, Any]
    decay_type: str
    clicks_baseline: Optional[int]
    clicks_current: Optional[int]
    clicks_change_pct: Optional[float]
    impressions_baseline: Optional[int]
    impressions_current: Optional[int]
    impressions_change_pct: Optional[float]
    position_baseline: Optional[float]
    position_current: Optional[float]
    position_change: Optional[float]


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
    item_type: Optional[str]
    status: str
    source_type: Optional[str]
    source_id: Optional[int]
    auto_fixable: bool
    auto_fixed: bool
    auto_fixed_at: Optional[str]
    estimated_effort: Optional[str]
    page_url: Optional[str]
    page_id: Optional[int]
    group_id: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    completed_at: Optional[str]


class ActionItemSummary(TypedDict):
    total: int
    open: int
    done: int
    dismissed: int
    resolved: int
    retired: int
    auto_fixed: int
    done_this_month: int
    completion_rate: float
    by_category: Dict[str, int]
    by_priority: Dict[str, int]


class ActionItemGroup(TypedDict):
    id: int
    title: str
    category: Optional[str]
    item_type: Optional[str]
    priority: Optional[str]
    source_type: Optional[str]
    total_items: int
    open_items: int
    done_items: int
    status: str


# ---------------------------------------------------------------------------
# Domain Health / SERP / Benchmarks / Content Quality / Geo
# ---------------------------------------------------------------------------


class DomainHealthResponse(TypedDict):
    domain: str
    domain_health_score: Optional[float]
    breakdown: Optional[Dict[str, Any]]
    citation_not_measured: List[Any]
    insights: List[Any]
    veto_applied: Optional[Any]
    recommendations: List[Any]


class SERPLandscapeResponse(TypedDict):
    feature_counts: Dict[str, int]
    total_with_snapshots: int
    keywords_data: List[Any]
    user_position_distribution: Dict[str, int]
    snippet_opportunities: List[Any]


class BenchmarkResponse(TypedDict):
    domain: str
    industry: Optional[str]
    benchmarks: Dict[str, Any]


class ContentQualityResponse(TypedDict):
    page_id: int
    page_url: str
    page_type: Optional[str]
    content_quality_score: Optional[float]
    breakdown: Dict[str, Any]
    issues: List[Any]
    veto_applied: Optional[Any]
    top_improvements: List[Any]
    geo_readiness_score: Optional[float]
    geo_readiness_breakdown: Optional[Dict[str, Any]]


class GeoReadinessResponse(TypedDict):
    page_id: int
    page_url: str
    page_type: Optional[str]
    geo_readiness_score: Optional[float]
    breakdown: Dict[str, Any]
    recommendations: List[Any]
    quotable_patterns_found: bool
    ai_engine_tips: List[Any]
    content_quality_score: Optional[float]


class PageContentResponse(TypedDict):
    id: int
    url: str
    title: Optional[str]
    meta_description: Optional[str]
    content: Optional[str]
    word_count: int
    headings: List[Dict[str, Any]]
    structured_data: Optional[Any]
    has_structured_data: bool
    language_code: Optional[str]
    page_type: Optional[str]
    images: List[Dict[str, Any]]


class PageStatus(TypedDict):
    id: int
    url: str
    title: Optional[str]
    page_type: Optional[str]
    is_content: bool
    seo_score: Optional[float]
    content_quality_score: Optional[float]
    geo_readiness_score: Optional[float]
    accessibility_score: Optional[float]
    meta_description: Optional[str]
    language_code: Optional[str]
    indexed_at: Optional[str]
    processed_at: Optional[str]
    vectorized_at: Optional[str]
    links_generated_at: Optional[str]
    scores_generated_at: Optional[str]
    seo_score_generated_at: Optional[str]
    created_at: Optional[str]


class SubmitUrlsResponse(TypedDict):
    pages: List[PageStatus]
