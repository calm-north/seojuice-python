from __future__ import annotations

from seojuice.injection._fetcher import (
    apply_suggestions,
    fetch_suggestions_async,
    fetch_suggestions_sync,
)
from seojuice.injection.asgi import SEOJuiceASGIMiddleware
from seojuice.injection.django import SEOJuiceDjangoMiddleware

__all__ = [
    "apply_suggestions",
    "fetch_suggestions_sync",
    "fetch_suggestions_async",
    "SEOJuiceDjangoMiddleware",
    "SEOJuiceASGIMiddleware",
]
