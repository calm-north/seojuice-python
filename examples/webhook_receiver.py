"""
Flask Webhook Receiver — Handle SEOJuice change lifecycle events.

Verifies HMAC-SHA256 signatures, routes events by type, and
processes heavy work async to respond 200 quickly.

Setup:
  1. Set SEOJUICE_WEBHOOK_SECRET in your environment (from the dashboard)
  2. Set SEOJUICE_API_KEY for API callbacks
  3. Configure the webhook URL in SEOJuice: https://yoursite.com/webhooks/seojuice

Usage:
  pip install flask
  SEOJUICE_WEBHOOK_SECRET=whsec_xxx SEOJUICE_API_KEY=sk_xxx python webhook_receiver.py
"""
import hashlib
import hmac
import json
import logging
import os
from threading import Thread

from flask import Flask, Response, jsonify, request

logger = logging.getLogger(__name__)

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["SEOJUICE_WEBHOOK_SECRET"]


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from the X-SEOJuice-Signature header."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


# --- Event handlers (run in background thread) ---


def on_change_created(payload: dict) -> None:
    change = payload["change"]
    logger.info(
        "[webhook] New %s change #%d for %s",
        change["change_type"],
        change["id"],
        change.get("page_url"),
    )


def on_change_approved(payload: dict) -> None:
    change = payload["change"]
    logger.info(
        "[webhook] Change #%d approved — ready for integration to pull",
        change["id"],
    )


def on_change_applied(payload: dict) -> None:
    change = payload["change"]
    website = payload["website"]
    logger.info(
        "[webhook] Change #%d applied to %s",
        change["id"],
        change.get("page_url"),
    )
    # Trigger CMS rebuild / cache purge here
    trigger_rebuild(website["domain"], change)


def on_change_reverted(payload: dict) -> None:
    change = payload["change"]
    website = payload["website"]
    reason = payload.get("revert_reason", "")
    logger.info(
        "[webhook] Change #%d reverted%s",
        change["id"],
        f": {reason}" if reason else "",
    )
    trigger_rebuild(website["domain"], change)


def on_change_rejected(payload: dict) -> None:
    change = payload["change"]
    reason = payload.get("reason", "")
    logger.info(
        "[webhook] Change #%d rejected%s",
        change["id"],
        f": {reason}" if reason else "",
    )


def trigger_rebuild(domain: str, change: dict) -> None:
    """Trigger a site rebuild. Replace with your actual build system."""
    logger.info(
        "[rebuild] Triggering rebuild for %s (change #%d)",
        domain,
        change["id"],
    )


EVENT_HANDLERS = {
    "change.created": on_change_created,
    "change.approved": on_change_approved,
    "change.applied": on_change_applied,
    "change.reverted": on_change_reverted,
    "change.rejected": on_change_rejected,
}


@app.route("/webhooks/seojuice", methods=["POST"])
def webhook():
    raw_body = request.get_data()
    signature = request.headers.get("X-SEOJuice-Signature", "")

    if not verify_signature(raw_body, signature):
        logger.warning("[webhook] Invalid signature, rejecting")
        return jsonify({"error": "Invalid signature"}), 401

    payload = json.loads(raw_body)
    event = payload.get("event", "")

    # Respond 200 immediately, process async
    handler = EVENT_HANDLERS.get(event)
    if handler:
        thread = Thread(target=handler, args=(payload,), daemon=True)
        thread.start()
    else:
        logger.info("[webhook] Unhandled event: %s", event)

    return jsonify({"received": True}), 200


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
