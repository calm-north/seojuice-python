"""
Redis caching layer for SEOJuice API responses.

Wraps redis-py to provide cache-aside helpers for suggestion data,
with key expiry and pattern-based invalidation.

Requirements:
    pip install seojuice redis
"""
from __future__ import annotations

import json
import os
from typing import Any

import redis

from seojuice import SEOJuice
from seojuice.injection._fetcher import fetch_suggestions_sync


class SEORedisCache:
    """Thin cache wrapper around redis-py for SEOJuice suggestion data."""

    PREFIX = "seojuice"

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, url: str) -> str:
        return f"{self.PREFIX}:{url}"

    def get_cached_suggestions(self, url: str) -> dict[str, Any] | None:
        """Fetch cached suggestions, returning None on miss or error."""
        try:
            raw = self._redis.get(self._key(url))
        except redis.RedisError:
            return None
        if raw is None:
            return None
        return json.loads(raw)

    def cache_suggestions(self, url: str, data: dict[str, Any], ttl: int = 3600) -> None:
        """Store suggestions in Redis with a TTL (default 1 hour)."""
        try:
            self._redis.setex(self._key(url), ttl, json.dumps(data))
        except redis.RedisError:
            pass  # fail-open

    def invalidate_url(self, url: str) -> None:
        """Delete the cache entry for a single URL."""
        self._redis.delete(self._key(url))

    def invalidate_pattern(self, domain: str) -> None:
        """Delete all cache entries matching a domain via SCAN."""
        pattern = f"{self.PREFIX}:*{domain}*"
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                self._redis.delete(*keys)
            if cursor == 0:
                break


def main() -> None:
    """Example: cache-aside pattern with the sync client."""
    cache = SEORedisCache(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    url = "https://example.com/blog/seo-guide"

    # Try cache first
    suggestions = cache.get_cached_suggestions(url)
    if suggestions is None:
        suggestions = fetch_suggestions_sync(url, timeout=3.0)
        if suggestions:
            cache.cache_suggestions(url, suggestions)

    print("Suggestions:", suggestions)


if __name__ == "__main__":
    main()
