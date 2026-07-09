from __future__ import annotations

import hashlib
import hmac

from seojuice import verify_webhook_signature


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class TestVerifyWebhookSignature:
    def test_valid_signature_returns_true(self):
        secret = "whsec_test123"
        body = b'{"event": "change.applied", "change": {"id": 1}}'
        signature = _sign(secret, body)

        assert verify_webhook_signature(secret, body, signature) is True

    def test_tampered_body_returns_false(self):
        secret = "whsec_test123"
        body = b'{"event": "change.applied", "change": {"id": 1}}'
        signature = _sign(secret, body)

        tampered_body = b'{"event": "change.applied", "change": {"id": 2}}'

        assert verify_webhook_signature(secret, tampered_body, signature) is False

    def test_wrong_secret_returns_false(self):
        body = b'{"event": "change.created"}'
        signature = _sign("whsec_correct", body)

        assert verify_webhook_signature("whsec_wrong", body, signature) is False

    def test_str_body_matches_equivalent_bytes_signature(self):
        secret = "whsec_test123"
        body_str = '{"event": "change.rejected"}'
        signature = _sign(secret, body_str.encode("utf-8"))

        assert verify_webhook_signature(secret, body_str, signature) is True

    def test_bytes_body_also_works(self):
        secret = "whsec_test123"
        body_bytes = b'{"event": "change.rejected"}'
        signature = _sign(secret, body_bytes)

        assert verify_webhook_signature(secret, body_bytes, signature) is True

    def test_uses_constant_time_comparison(self, monkeypatch):
        calls = []
        real_compare_digest = hmac.compare_digest

        def spy(a, b):
            calls.append((a, b))
            return real_compare_digest(a, b)

        monkeypatch.setattr(hmac, "compare_digest", spy)

        secret = "whsec_test123"
        body = b"payload"
        signature = _sign(secret, body)

        assert verify_webhook_signature(secret, body, signature) is True
        assert len(calls) == 1

    def test_malformed_signature_returns_false_not_raises(self):
        secret = "whsec_test123"
        body = b"payload"

        assert verify_webhook_signature(secret, body, "not-hex-at-all!!") is False

    def test_none_signature_returns_false_not_raises(self):
        secret = "whsec_test123"
        body = b"payload"
        assert verify_webhook_signature(secret, body, None) is False

    def test_none_secret_returns_false_not_raises(self):
        body = b"payload"
        sig = _sign("whsec_test123", body)
        assert verify_webhook_signature(None, body, sig) is False

    def test_empty_secret_returns_false(self):
        body = b"payload"
        sig = _sign("whsec_test123", body)
        assert verify_webhook_signature("", body, sig) is False

    def test_empty_signature_returns_false(self):
        secret = "whsec_test123"
        body = b"payload"
        assert verify_webhook_signature(secret, body, "") is False

    def test_none_body_returns_false(self):
        secret = "whsec_test123"
        sig = _sign(secret, b"")
        assert verify_webhook_signature(secret, None, sig) is False

    def test_non_str_signature_returns_false(self):
        secret = "whsec_test123"
        body = b"payload"
        assert verify_webhook_signature(secret, body, 12345) is False

    def test_valid_signature_still_verifies_after_guards(self):
        secret = "whsec_test123"
        body = b'{"event": "change.applied"}'
        sig = _sign(secret, body)
        assert verify_webhook_signature(secret, body, sig) is True
