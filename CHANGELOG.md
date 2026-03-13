# Changelog

## 1.1.0 (2026-03-13)

### New Features

- **Changes Management** — Full change lifecycle API with 11 methods: `list_changes`, `get_change`, `change_stats`, `change_settings`, `update_change_settings`, `approve_change`, `reject_change`, `revert_change`, `pull_change`, `verify_change`, `bulk_change_action`
- **Action Items** — CRUD operations for SEO action items: `list_action_items`, `get_action_item`, `create_action_item`, `update_action_item`, `action_item_summary`, `get_action_item_groups`
- **Webhook Verification** — `verify_webhook_signature()` helper for HMAC-SHA256 signature validation of incoming webhooks
- **Domain Health** — `get_domain_health()` endpoint for overall domain health scoring
- **SERP Landscape** — `get_serp_landscape()` endpoint for search engine results page analysis
- **Benchmarks** — `get_benchmarks()` endpoint for industry benchmark comparisons
- **Content Quality** — `get_content_quality(page_id)` page-scoped endpoint for content quality scoring
- **Geo Readiness** — `get_geo_readiness(page_id)` page-scoped endpoint for geo-targeting readiness
- **Page Content** — `get_page_content(page_id)` endpoint for raw page content retrieval
- **URL Submission** — `submit_urls()` and `get_url_status()` for submitting URLs for processing

### New Types

- `ChangeRecord`, `ChangeStats`, `ChangeSettings`, `BulkActionResult`, `ChangeWebhookPayload`
- `ActionItem`, `ActionItemSummary`, `ActionItemGroup`
- `DomainHealthResponse`, `SERPLandscapeResponse`, `BenchmarkResponse`
- `ContentQualityResponse`, `GeoReadinessResponse`, `PageContentResponse`
- All domain types now exported from top-level `seojuice` package

### New Examples

- [`changes_management.py`](examples/changes_management.py) — Full change lifecycle: stats, triage, bulk approve, review/reject, automation settings
- [`webhook_receiver.py`](examples/webhook_receiver.py) — Flask-based webhook receiver with HMAC-SHA256 signature verification
- [`action_items.py`](examples/action_items.py) — Action item summary, listing, groups, create, update workflow

### Bug Fixes

- Fixed `create_report()` sending wrong body key (`report_type` → `type`)
- Fixed `reply_to_gbp_review()` sending wrong body key (`reply` → `reply_text`)
- Fixed `get_action_item_groups()` return type from `PagedResult[Any]` to `PagedResult[ActionItemGroup]`
- Fixed version mismatch between `pyproject.toml` and `__init__.py`

### Domain-Scoped Client

All new endpoints are also available via the domain-scoped `WebsiteResource` and `AsyncWebsiteResource`:

```python
site = client.website("example.com")
stats = site.change_stats()
items = site.action_items()
health = site.domain_health()
```

## 1.0.0 (2026-02-23)

- Initial release
