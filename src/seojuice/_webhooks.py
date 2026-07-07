from __future__ import annotations

import hashlib
import hmac
from typing import Union


def verify_webhook_signature(secret: str, body: Union[bytes, str], signature: str) -> bool:
    """Verify an HMAC-SHA256 webhook signature against the raw request body.

    `secret` is used as-is (UTF-8 encoded) as the HMAC key — it is not hex-decoded.
    `signature` must be the raw hex digest sent in the `X-SEOJuice-Signature` header.
    """
    body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
