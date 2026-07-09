from __future__ import annotations

import hashlib
import hmac
from typing import Optional, Union


def verify_webhook_signature(
    secret: str,
    body: Union[bytes, str],
    signature: Optional[str],
) -> bool:
    """Verify an HMAC-SHA256 webhook signature against the raw request body.

    Fails closed: returns ``False`` (never raises) when ``secret``, ``body``, or
    ``signature`` is ``None``, empty, or the wrong type — so a request with a
    missing ``X-SEOJuice-Signature`` header rejects with 401 rather than 500.

    ``secret`` is used as-is (UTF-8 encoded) as the HMAC key — it is not
    hex-decoded. ``signature`` must be the raw hex digest sent in the
    ``X-SEOJuice-Signature`` header (no ``sha256=`` prefix).
    """
    if not secret or not isinstance(secret, str):
        return False
    if not isinstance(signature, str) or not signature:
        return False
    if body is None or not isinstance(body, (bytes, str)):
        return False
    body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
