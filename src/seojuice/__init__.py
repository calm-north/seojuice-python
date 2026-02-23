from __future__ import annotations

from seojuice._async import AsyncSEOJuice
from seojuice._exceptions import (
    APIError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    SEOJuiceError,
    ServerError,
)
from seojuice._pagination import PagedResult, auto_paginate
from seojuice._sync import SEOJuice

__version__ = "0.1.0"

__all__ = [
    "SEOJuice",
    "AsyncSEOJuice",
    "PagedResult",
    "auto_paginate",
    "SEOJuiceError",
    "APIError",
    "AuthError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]
