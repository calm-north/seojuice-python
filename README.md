# SEOJuice Python SDK

Official Python SDK for the [SEOJuice](https://seojuice.com) Intelligence API.

- Typed wrappers for all `/api/v2/` endpoints
- Sync and async clients (powered by [httpx](https://www.python-httpx.org/))
- Built-in pagination helpers
- Django and ASGI middleware for automatic SEO tag injection
- Full type annotations with PEP 561 support

## Installation

```bash
pip install seojuice
```

With Django middleware support:

```bash
pip install seojuice[django]
```

## Quick Start

```python
from seojuice import SEOJuice

client = SEOJuice("your-api-key")

# List all websites
websites = client.list_websites()
for site in websites["results"]:
    print(site["domain"])

# Get detailed website info
detail = client.get_website("example.com")
print(detail["seo_score"])

client.close()
```

## Domain-Scoped Client

Use `.website(domain)` for a cleaner interface when working with a single domain:

```python
from seojuice import SEOJuice

with SEOJuice("your-api-key") as client:
    site = client.website("example.com")

    # Get website details
    detail = site.detail()

    # List pages
    pages = site.pages(page_size=20)
    for page in pages:
        print(page["url"], page["seo_score"])

    # Get intelligence summary with trends
    intel = site.intelligence(period="30d", include_trends=True)

    # Check AISO score
    aiso = site.aiso(include_history=True)
    print(f"AISO: {aiso['aiso_score']}")

    # List content gaps
    gaps = site.content_gaps(intent="informational")
    for gap in gaps:
        print(gap["page_name"], gap["seo_potential"])
```

## Pagination

### Manual Pagination

```python
result = client.list_pages("example.com", page=1, page_size=10)

print(f"Total: {result.total_count}")
print(f"Has next: {result.has_next}")

for page in result:
    print(page["url"])
```

### Auto-Pagination

Iterate through all pages automatically:

```python
from seojuice import SEOJuice, auto_paginate

client = SEOJuice("your-api-key")

for page in auto_paginate(
    lambda **kw: client.list_pages("example.com", **kw),
    page_size=100,
):
    print(page["url"])
```

## Async Usage

```python
import asyncio
from seojuice import AsyncSEOJuice

async def main():
    async with AsyncSEOJuice("your-api-key") as client:
        site = client.website("example.com")

        detail = await site.detail()
        pages = await site.pages(page_size=50)

        for page in pages:
            print(page["url"])

asyncio.run(main())
```

### Async Auto-Pagination

```python
from seojuice._pagination import async_auto_paginate

async with AsyncSEOJuice("your-api-key") as client:
    site = client.website("example.com")

    async for page in async_auto_paginate(site.pages, page_size=100):
        print(page["url"])
```

## Error Handling

```python
from seojuice import SEOJuice, AuthError, NotFoundError, RateLimitError, APIError

client = SEOJuice("your-api-key")

try:
    detail = client.get_website("example.com")
except AuthError:
    print("Invalid API key")
except NotFoundError:
    print("Website not found")
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
except APIError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```

Exception hierarchy:

- `SEOJuiceError` -- base exception
  - `APIError` -- any HTTP 4xx/5xx
    - `AuthError` -- 401
    - `ForbiddenError` -- 403
    - `NotFoundError` -- 404
    - `RateLimitError` -- 429
    - `ServerError` -- 5xx

## PDF Report Download

```python
with SEOJuice("your-api-key") as client:
    site = client.website("example.com")

    # Create a report
    created = site.create_report("this_month")
    print(f"Report queued: {created['report_id']}")

    # Download PDF (once report is ready)
    pdf_bytes = site.report_pdf(created["report_id"])
    with open("report.pdf", "wb") as f:
        f.write(pdf_bytes)
```

## Django Middleware

Automatically inject SEO meta tags, Open Graph tags, and structured data into your HTML responses.

### Setup

Add to your `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    "seojuice.injection.django.SEOJuiceDjangoMiddleware",
]

# Optional settings
SEOJUICE_INJECTION_ENABLED = True   # Default: True
SEOJUICE_INJECTION_TIMEOUT = 5.0    # Default: 5.0 seconds
```

The middleware fetches suggestions from `smart.seojuice.io` and injects:
- `<meta name="description">` tag
- Open Graph tags (`og:title`, `og:description`, `og:url`, `og:image`)
- `<title>` tag replacement
- JSON-LD structured data

Responses are cached in-memory with a 5-minute TTL. Non-HTML responses are passed through unchanged.

## FastAPI / ASGI Middleware

For any ASGI framework (FastAPI, Starlette, etc.):

```python
from fastapi import FastAPI
from seojuice.injection.asgi import SEOJuiceASGIMiddleware

app = FastAPI()

app.add_middleware(
    SEOJuiceASGIMiddleware,
    base_url="https://example.com",
    timeout=3.0,
    enabled=True,
)
```

## Configuration

Both clients accept these constructor arguments:

| Parameter     | Type              | Default                          | Description                    |
|---------------|-------------------|----------------------------------|--------------------------------|
| `api_key`     | `str`             | (required)                       | Your SEOJuice API key          |
| `base_url`    | `str`             | `https://seojuice.com/api/v2`    | API base URL                   |
| `timeout`     | `float`           | `30.0`                           | Request timeout in seconds     |
| `http_client` | `httpx.Client`    | `None`                           | Custom httpx client instance   |

## Flask Integration

Use `before_request` / `after_request` hooks for automatic SEO tag injection:

```python
from flask import Flask, g, request
from seojuice.injection._fetcher import apply_suggestions, fetch_suggestions_sync

app = Flask(__name__)

@app.before_request
def fetch_seo():
    g.seo_suggestions = fetch_suggestions_sync(request.url, timeout=3.0)

@app.after_request
def inject_seo(response):
    suggestions = getattr(g, "seo_suggestions", None)
    if suggestions and "text/html" in (response.content_type or ""):
        html = response.get_data(as_text=True)
        response.set_data(apply_suggestions(html, suggestions))
    return response
```

Install with Flask extras:

```bash
pip install seojuice[flask]
```

## Examples

| Example | Description |
|---------|-------------|
| [`intelligence_api.py`](examples/intelligence_api.py) | Full Intelligence API workflow — overview, gaps, decay, PageSpeed |
| [`django_views.py`](examples/django_views.py) | Django views and class-based mixin for SEO context |
| [`fastapi_app.py`](examples/fastapi_app.py) | FastAPI app with async client lifecycle and ASGI middleware |
| [`flask_app.py`](examples/flask_app.py) | Flask app with request hooks and TTL cache |
| [`async_workflow.py`](examples/async_workflow.py) | Concurrent fetching, async pagination, batch domain processing |
| [`celery_tasks.py`](examples/celery_tasks.py) | Background analysis, periodic decay checks, PDF report generation |
| [`redis_cache.py`](examples/redis_cache.py) | Redis caching layer with pattern-based invalidation |
| [`cms_integration.py`](examples/cms_integration.py) | Wagtail, Django CMS, and headless WordPress integrations |

## Requirements

- Python 3.9+
- httpx >= 0.24.0
- typing_extensions >= 4.0
- django >= 3.2 (optional, for Django middleware)

## License

MIT
