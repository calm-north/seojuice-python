# Changelog

## 1.4.0

### Fixed
- **Error boundary no longer crashes on non-JSON error bodies (security-shaped).** `_request`/`_arequest` now check the HTTP status before parsing and synthesize the typed error from the status code when the body isn't JSON — an HTML 502/504, a plain-text 503, or an empty-body 429 now raise `ServerError`/`RateLimitError` (both `SEOJuiceError`) instead of a raw `json.JSONDecodeError` that bypassed every documented `except`.
- **Webhook verifier fails closed (security).** `verify_webhook_signature` now returns `False` (never raises) on a `None`/empty/non-`str` secret, body, or signature — a request with a missing `X-SEOJuice-Signature` header rejects with 401 instead of an unhandled 500. `signature` is widened to `Optional[str]`.
- **`WebsiteResource` write-path methods are now explicitly typed.** `bulk_change_action`, `update_action_item`, `create_action_item`, `reject_change`, `revert_change`, `pull_change`, `verify_change`, `submit_urls`, and `url_status` gained the real keyword-only signatures (mirroring the async client), so mypy catches wrong kwargs on the `.website(...)` facade. `update_change_settings` stays variadic by design.
- **User-Agent version drift.** The UA advertised `seojuice-python/0.1.0` on every release; it now derives from `__version__` (single-sourced in `_version.py`).
- **Falsy API keys are rejected.** `SEOJuice(None)`/`("")`/`("  ")` now raise `ValueError("api_key is required")` instead of sending `Bearer None`.

### Added
- **`APIConnectionError` / `APITimeoutError`** (both subclasses of `SEOJuiceError`). `httpx` connect/read timeouts, connection-refused, and DNS failures are now wrapped into the typed hierarchy, so `except SEOJuiceError` catches the most common production failure.

### Docs
- Corrected the README `bulk_change_action` (`ids=`) and `update_action_item` (`action=`) snippets, reworded the Django `<title>` claim to "injection when missing", and repointed the 11 `examples/*.py` links to absolute GitHub URLs (they 404'd on PyPI). Added a CI gate that compiles every README fence and imports every example to block future drift.

## 1.3.0

### Fixed
- **structured_data now injects as valid JSON-LD against the live payload** (single- or double-encoded, defensively decoded; the previous double-decode silently dropped the schema on the real single-encoded payload).
- **JSON-LD is emitted as raw UTF-8** (`ensure_ascii=False`) to match the node/php SDKs and the edge Worker byte-for-byte on localized schema.
- **CJK internal links at sentence end** — the link boundary now allows full-width Japanese punctuation (`。、！？）」』`).
- **Content diffs on hydrated pages** — occurrence/ambiguity detection now ignores `<script>`/`<style>` regions, so hydration-script duplicates (e.g. Next.js App Router) no longer skip the visible-body diff.
- **Async `create_report` / `reply_to_review` sent the wrong request-body keys.** `AsyncWebsiteResource` built its POST bodies with `report_type`/`reply` instead of the API's `type`/`reply_text`, so async report creation silently defaulted to `this_month` and async GBP review replies posted empty text (server 400). Both corrected; the sync client was already correct.

### Added
- **`ChangeRecord` / `ChangeSettings` type completeness** — `ChangeRecord` gains `risk_level`, `batch_id`, `batch_label`, `edited_manually`; `ChangeSettings` gains `h1_tags_mode`; `exclude_paths` is now optional — matching the live API's change schema.

## 1.2.0 (2026-07-06)

### Server-Side Injection: Full Parity

`apply_suggestions()` (used by `SEOJuiceDjangoMiddleware` and `SEOJuiceASGIMiddleware`) now ports the full Cloudflare Worker + WordPress plugin transform pipeline instead of a head-only meta-tag injector:

- **Internal links** — keyword-to-URL injection with first-occurrence dedup, skip-tags (`<a>`, `<script>`, `<style>`, `<title>`, `h1`–`h6`), custom link class, and CJK/Japanese boundary detection (`isAsian`)
- **Image alt-text** — fills missing or short (`< 5` chars) `alt` attributes matched by normalized `src`/`data-src` URL
- **Content diffs** — replace-only content mutation with drift/ambiguity/idempotency guards
- **H1 replacement** — with `data-seojuice="h1"` marker
- **Broken-link fixes** — `replace`/`unlink` actions on `<a href>`/`<img src>`, reading `new_url` with a `replacement_url` fallback
- **`validate_api_response`** gate — rejects payloads with no actionable content or an `errors` field before running any transform
- **Content-area targeting** (`insert_into_content_only`) — restricts link injection to block-content tags (`p`, `li`, `span`, `div`, `td`, `blockquote`, `dd`, `figcaption`) when enabled
- **`data-seojuice*` markers** + a `<!-- seojuice: ... -->` manifest comment for idempotency and observability
- **`window.seojuiceSSR = true`** SSR flag appended before `</body>`
- **Fail-open** — any exception, empty output, output `< 0.5×` original length, or a missing `<body>` tag reverts to the original HTML unchanged
- Fixed a `structured_data` single-encode bug — the field is stored double-JSON-encoded upstream and is now double-decoded before rendering as `<script type="application/ld+json">`

No new runtime dependency — stdlib `re`/`json` only (`httpx` unchanged). The Django/ASGI middleware are unchanged in wiring; they gain full parity automatically by calling `apply_suggestions`.

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
