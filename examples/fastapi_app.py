"""
FastAPI integration with SEOJuice.

Demonstrates async client lifecycle, ASGI middleware, and API endpoints
for retrieving SEO intelligence data.

Requirements:
    pip install seojuice[fastapi] fastapi uvicorn

Run:
    uvicorn examples.fastapi_app:app --reload
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Query, Request

from seojuice import AsyncSEOJuice, auto_paginate
from seojuice.injection.asgi import SEOJuiceASGIMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the async client on startup and close it on shutdown."""
    client = AsyncSEOJuice(os.environ["SEOJUICE_API_KEY"])
    app.state.seojuice = client
    yield
    await client.close()


app = FastAPI(title="SEOJuice Demo", lifespan=lifespan)

app.add_middleware(
    SEOJuiceASGIMiddleware,
    base_url="https://example.com",
    timeout=3.0,
    enabled=True,
)


def _client(request: Request) -> AsyncSEOJuice:
    return request.app.state.seojuice


@app.get("/api/seo/{domain}")
async def get_seo_overview(request: Request, domain: str) -> dict:
    """Return intelligence summary and AISO score for a domain."""
    client = _client(request)
    site = client.website(domain)

    intel = await site.intelligence(period="30d", include_trends=True)
    aiso = await site.aiso()

    return {
        "domain": domain,
        "intelligence": intel,
        "aiso": aiso,
    }


@app.get("/api/seo/{domain}/gaps")
async def get_content_gaps(
    request: Request,
    domain: str,
    intent: str | None = Query(None, description="Filter by intent type"),
    category: str | None = Query(None, description="Filter by category"),
) -> dict:
    """Return content gaps with optional intent/category filtering."""
    client = _client(request)
    site = client.website(domain)

    kwargs: dict = {}
    if intent:
        kwargs["intent"] = intent
    if category:
        kwargs["category"] = category

    gaps = await site.content_gaps(**kwargs)
    return {"domain": domain, "gaps": list(gaps)}
