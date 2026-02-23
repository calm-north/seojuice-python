from __future__ import annotations

from typing import Dict, Type


class SEOJuiceError(Exception):
    """Base for all SDK errors."""


class APIError(SEOJuiceError):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{status_code}] {error_code}: {message}")


class AuthError(APIError):
    """401 Unauthorized."""


class ForbiddenError(APIError):
    """403 Forbidden."""


class NotFoundError(APIError):
    """404 Not Found."""


class RateLimitError(APIError):
    """429 Too Many Requests."""


class ServerError(APIError):
    """5xx Server Error."""


_STATUS_TO_EXCEPTION: Dict[int, Type[APIError]] = {
    401: AuthError,
    403: ForbiddenError,
    404: NotFoundError,
    429: RateLimitError,
}


def raise_for_response(status_code: int, body: dict) -> None:  # type: ignore[type-arg]
    if status_code < 400:
        return
    error_code = body.get("error", "unknown_error")
    message = body.get("message", "An unexpected error occurred")
    exc_class = _STATUS_TO_EXCEPTION.get(status_code)
    if exc_class:
        raise exc_class(status_code, error_code, message)
    if status_code >= 500:
        raise ServerError(status_code, error_code, message)
    raise APIError(status_code, error_code, message)
