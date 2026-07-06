from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, Optional, Tuple

import httpx

from seojuice.injection._transform import (
    Manifest,
    add_manifest_comment,
    add_ssr_flag,
    apply_broken_link_fixes,
    apply_content_diffs,
    inject_internal_links,
    replace_h1,
    replace_images,
    replace_meta_tags,
    validate_api_response,
)

logger = logging.getLogger("seojuice.injection")

_SUGGESTIONS_URL = "https://smart.seojuice.io/suggestions"


class _SuggestionsCache:
    """Simple in-memory TTL cache for suggestions responses."""

    def __init__(self, ttl: float = 300.0) -> None:
        self._ttl = ttl
        self._store: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()


_cache = _SuggestionsCache()


def fetch_suggestions_sync(
    page_url: str,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Fetch SEO suggestions for a URL. Returns empty dict on any failure."""
    cached = _cache.get(page_url)
    if cached is not None:
        return cached

    try:
        response = httpx.get(
            _SUGGESTIONS_URL,
            params={"url": page_url},
            timeout=timeout,
        )
        if response.status_code != 200:
            return {}
        data: Dict[str, Any] = response.json()
        _cache.set(page_url, data)
        return data
    except Exception:
        logger.debug("Failed to fetch suggestions for %s", page_url, exc_info=True)
        return {}


async def fetch_suggestions_async(
    page_url: str,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Async fetch SEO suggestions for a URL. Returns empty dict on any failure."""
    cached = _cache.get(page_url)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                _SUGGESTIONS_URL,
                params={"url": page_url},
                timeout=timeout,
            )
        if response.status_code != 200:
            return {}
        data: Dict[str, Any] = response.json()
        _cache.set(page_url, data)
        return data
    except Exception:
        logger.debug("Failed to fetch suggestions for %s", page_url, exc_info=True)
        return {}


# ---------------------------------------------------------------------------
# Shared HTML injection: full server-side parity with the Cloudflare Worker.
# ---------------------------------------------------------------------------

_BODY_TAG_RE = re.compile(r"<body[\s>]", re.IGNORECASE)


def apply_suggestions(html: str, data: Dict[str, Any]) -> str:
    """Inject SEO suggestions into HTML, mirroring the Worker's ``transformHTML``.

    Applies meta/OG/schema tags, image alt-text, internal links, content diffs,
    h1 replacement, and broken-link fixes, then appends a manifest comment and
    an SSR flag. Fails open (returns the original HTML unchanged) on any
    exception, or if the result is empty, less than half the original length,
    or missing a ``<body>`` tag.

    ``validate_api_response`` (C1) gates the content-mutating transforms only;
    the manifest comment and SSR flag are appended unconditionally whenever
    ``data`` is truthy, matching the Worker's unconditional ``addSSRFlag`` call.
    """
    if not data:
        return html

    original = html
    out = html
    manifest = Manifest()
    try:
        if validate_api_response(data):
            out = replace_meta_tags(out, data, manifest)
            out = replace_images(out, data, manifest)
            out = inject_internal_links(out, data, manifest)
            out = apply_content_diffs(out, data.get("diffs") or [], manifest)
            out = replace_h1(out, data, manifest)
            out = apply_broken_link_fixes(out, data.get("broken_link_fixes") or [])

        out = add_manifest_comment(out, manifest)
        out = add_ssr_flag(out)

        if not out or len(out) < len(original) * 0.5 or not _BODY_TAG_RE.search(out):
            out = original
    except Exception:
        logger.debug("Failed to apply suggestions, failing open", exc_info=True)
        out = original

    return out
