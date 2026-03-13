from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

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
# Shared HTML injection helpers
# ---------------------------------------------------------------------------

_HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)


def _build_meta_tag(name: str, content: str) -> str:
    safe_content = content.replace('"', "&quot;")
    return f'<meta name="{name}" content="{safe_content}">'


def _build_og_tag(prop: str, content: str) -> str:
    safe_content = content.replace('"', "&quot;")
    return f'<meta property="og:{prop}" content="{safe_content}">'


def apply_suggestions(html: str, data: Dict[str, Any]) -> str:
    """Inject SEO tags from suggestions data before </head>."""
    if not data:
        return html

    tags: List[str] = []

    meta_description = data.get("meta_description")
    if meta_description:
        tags.append(_build_meta_tag("description", meta_description))

    og_title = data.get("og_title")
    if og_title:
        tags.append(_build_og_tag("title", og_title))

    og_description = data.get("og_description")
    if og_description:
        tags.append(_build_og_tag("description", og_description))

    og_url = data.get("og_url")
    if og_url:
        tags.append(_build_og_tag("url", og_url))

    og_image = data.get("og_image")
    if og_image:
        tags.append(_build_og_tag("image", og_image))

    structured_data = data.get("structured_data")
    if structured_data:
        sd_json = json.dumps(structured_data, separators=(",", ":"))
        tags.append(f'<script type="application/ld+json">{sd_json}</script>')

    title = data.get("title")
    if title:
        safe_title = title.replace("<", "&lt;").replace(">", "&gt;")
        html = re.sub(
            r"<title>[^<]*</title>",
            f"<title>{safe_title}</title>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )

    broken_link_fixes = data.get("broken_link_fixes") or []
    for fix in broken_link_fixes:
        broken_url = fix.get("broken_url", "")
        action = fix.get("action", "")
        if not broken_url or not action:
            continue
        escaped = re.escape(broken_url)
        if action == "unlink":
            html = re.sub(
                r'<a\s[^>]*href=["\']' + escaped + r'["\'][^>]*>(.*?)</a>',
                r"\1",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
        elif action == "replace":
            replacement_url = fix.get("replacement_url", "")
            if replacement_url:
                safe_url = replacement_url.replace('"', "&quot;")
                html = re.sub(
                    r'(<a\s[^>]*href=)["\']' + escaped + r'["\']([^>]*>)',
                    r'\g<1>"' + safe_url + r'"\g<2>',
                    html,
                    flags=re.IGNORECASE,
                )

    if not tags:
        return html

    injection = "\n".join(tags) + "\n"
    html = _HEAD_CLOSE_RE.sub(injection + "</head>", html, count=1)
    return html
