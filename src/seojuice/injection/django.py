from __future__ import annotations

from typing import Any, Callable, Optional

from seojuice.injection._fetcher import apply_suggestions, fetch_suggestions_sync


class SEOJuiceDjangoMiddleware:
    """Django middleware that injects SEO suggestions into HTML responses."""

    def __init__(self, get_response: Callable[..., Any]) -> None:
        self.get_response = get_response

        self._enabled: bool = True
        self._timeout: float = 5.0

        try:
            from django.conf import settings

            self._enabled = getattr(settings, "SEOJUICE_INJECTION_ENABLED", True)
            self._timeout = getattr(settings, "SEOJUICE_INJECTION_TIMEOUT", 5.0)
        except Exception:
            pass

    def __call__(self, request: Any) -> Any:
        response = self.get_response(request)

        if not self._enabled:
            return response

        content_type: Optional[str] = response.get("Content-Type", "")
        if not content_type or "text/html" not in content_type:
            return response

        page_url = request.build_absolute_uri()
        data = fetch_suggestions_sync(page_url, timeout=self._timeout)
        if not data:
            return response

        html = response.content.decode("utf-8", errors="replace")
        modified = apply_suggestions(html, data)
        if modified != html:
            response.content = modified.encode("utf-8")
            response["Content-Length"] = str(len(response.content))

        return response
