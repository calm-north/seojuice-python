"""Requests the SDK sends must match what the SEOJuice server accepts.

Expected values come from server code (seojuice/partners/views.py,
seojuice/actionitems/api_views.py, seojuice/organization/single_gate.py).
Transport is strict: an unrouted request fails the test.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Tuple

import httpx
import pytest

from seojuice import AsyncSEOJuice, SEOJuice
from seojuice._exceptions import APIError, APITimeoutError

D = "example.com"
BASE = "/api/v2"
Route = Tuple[str, str]


class Strict:
    """Routes keyed by (METHOD, path). Anything else raises AssertionError."""

    def __init__(self, routes: Dict[Route, Any]) -> None:
        self.routes = routes
        self.requests: List[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = (request.method, request.url.path)
        if key not in self.routes:
            raise AssertionError(f"unrouted request: {key}")
        resp = self.routes[key]
        if isinstance(resp, httpx.Response):
            return resp
        return httpx.Response(200, json=resp)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def body(self) -> Dict[str, Any]:
        return json.loads(self.last.content) if self.last.content else {}


def sync_client(routes: Dict[Route, Any]) -> Tuple[SEOJuice, Strict]:
    s = Strict(routes)
    http = httpx.Client(
        transport=httpx.MockTransport(s),
        base_url="https://seojuice.com/api/v2",
    )
    return SEOJuice("k", http_client=http), s


def async_client(routes: Dict[Route, Any]) -> Tuple[AsyncSEOJuice, Strict]:
    s = Strict(routes)
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(s),
        base_url="https://seojuice.com/api/v2",
    )
    return AsyncSEOJuice("k", http_client=http), s


def path(suffix: str) -> str:
    return f"{BASE}/websites/{D}/{suffix}"


PAGED: Dict[str, Any] = {"results": [], "pagination": {"page": 1, "page_size": 20, "total_count": 0, "total_pages": 1}}


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------


class TestReject:
    # views.py:2456-2462 -- reason required, empty -> 422 missing_field
    def test_reject_sends_reason(self):
        c, s = sync_client({("POST", path("changes/7/reject/")): {"id": 7}})
        c.website(D).reject_change(7, reason="off brand")
        assert s.body() == {"reason": "off brand"}

    def test_reject_client_method_sends_reason(self):
        c, s = sync_client({("POST", path("changes/7/reject/")): {"id": 7}})
        c.reject_change(D, 7, reason="off brand")
        assert s.body() == {"reason": "off brand"}

    def test_reject_without_reason_is_a_usage_error(self):
        c, s = sync_client({})
        with pytest.raises((TypeError, ValueError)):
            c.reject_change(D, 7)  # type: ignore[call-arg]
        assert s.requests == []

    def test_reject_blank_reason_is_a_usage_error(self):
        c, s = sync_client({})
        with pytest.raises(ValueError):
            c.reject_change(D, 7, reason="   ")
        assert s.requests == []

    async def test_async_reject_sends_reason(self):
        c, s = async_client({("POST", path("changes/7/reject/")): {"id": 7}})
        await c.website(D).reject_change(7, reason="off brand")
        assert s.body() == {"reason": "off brand"}


class TestApprove:
    # views.py:2413-2418 -- body {"confirm_heading": true} (strict `is True`)
    def test_approve_confirm_heading_body(self):
        c, s = sync_client({("POST", path("changes/42/approve/")): {"id": 42}})
        c.approve_change(D, 42, confirm_heading=True)
        assert s.body() == {"confirm_heading": True}

    def test_approve_default_sends_no_flag(self):
        c, s = sync_client({("POST", path("changes/42/approve/")): {"id": 42}})
        c.approve_change(D, 42)
        assert "confirm_heading" not in s.body()

    def test_resource_approve_confirm_heading(self):
        c, s = sync_client({("POST", path("changes/42/approve/")): {"id": 42}})
        c.website(D).approve_change(42, confirm_heading=True)
        assert s.body() == {"confirm_heading": True}

    async def test_async_resource_approve_confirm_heading(self):
        c, s = async_client({("POST", path("changes/42/approve/")): {"id": 42}})
        await c.website(D).approve_change(42, confirm_heading=True)
        assert s.body() == {"confirm_heading": True}

    def test_heading_not_confirmed_error_code_is_exposed(self):
        resp = httpx.Response(
            400, json={"error": "confirm_heading_required", "message": "m"}
        )
        c, _ = sync_client({("POST", path("changes/42/approve/")): resp})
        with pytest.raises(APIError) as ei:
            c.approve_change(D, 42)
        assert ei.value.error_code == "confirm_heading_required"


class TestListChanges:
    # views.py:1768-1806 -- filters: status, change_type, url, batch_id
    def test_url_and_batch_id_filters(self):
        c, s = sync_client({("GET", path("changes/")): PAGED})
        c.list_changes(D, url="https://example.com/a", batch_id="6f1c2f0e-0000-4000-8000-000000000000")
        q = dict(s.last.url.params)
        assert q["url"] == "https://example.com/a"
        assert q["batch_id"] == "6f1c2f0e-0000-4000-8000-000000000000"

    def test_risk_level_is_not_sent(self):
        c, s = sync_client({("GET", path("changes/")): PAGED})
        with pytest.warns(DeprecationWarning):
            c.list_changes(D, risk_level="high")
        assert "risk_level" not in s.last.url.params

    def test_resource_url_and_batch_id(self):
        c, s = sync_client({("GET", path("changes/")): PAGED})
        c.website(D).changes(url="https://example.com/a", batch_id="b")
        assert s.last.url.params["url"] == "https://example.com/a"
        assert s.last.url.params["batch_id"] == "b"

    async def test_async_resource_url_and_batch_id(self):
        c, s = async_client({("GET", path("changes/")): PAGED})
        await c.website(D).changes(url="https://example.com/a", batch_id="b")
        assert s.last.url.params["url"] == "https://example.com/a"
        assert s.last.url.params["batch_id"] == "b"

    # views.py:1779-1788 -- filter vocabulary is pending/approved/applied/
    # verified/pulled/rejected/reverted/expired; lifecycle names filter to none.
    @pytest.mark.parametrize(
        "given,sent",
        [
            ("proposed", "pending"),
            ("live", "applied"),
            ("rolled_back", "reverted"),
            ("approved", "approved"),
            ("rejected", "rejected"),
            ("expired", "expired"),
            ("pending", "pending"),
            ("applied", "applied"),
        ],
    )
    def test_status_lifecycle_values_are_translated_for_the_filter(self, given, sent):
        c, s = sync_client({("GET", path("changes/")): PAGED})
        c.list_changes(D, status=given)
        assert s.last.url.params["status"] == sent

    @pytest.mark.parametrize("ct", ["h1_tag", "broken_link_fix", "content_patch"])
    def test_change_type_values_pass_through(self, ct):
        # actionitems/constants.py:49-65
        c, s = sync_client({("GET", path("changes/")): PAGED})
        c.list_changes(D, change_type=ct)
        assert s.last.url.params["change_type"] == ct

    def test_literal_aliases_cover_server_values(self):
        from typing import get_args

        from seojuice import ChangeStatus, ChangeType

        # delivery/models.py:171-180 LifecycleState values
        assert set(get_args(ChangeStatus)) >= {
            "proposed", "approved", "live", "rolled_back",
            "rejected", "superseded", "stale", "expired",
        }
        # actionitems/constants.py:49-65 values
        assert set(get_args(ChangeType)) >= {
            "title_tag", "h1_tag", "meta_description", "meta_keywords",
            "og_title", "og_description", "og_image", "internal_link",
            "local_schema", "nap_fix", "structured_data", "image_alt",
            "accessibility", "broken_link_fix", "content_patch",
        }


class TestBulk:
    # views.py:2588-2602 -- ids or batch_id
    def test_batch_id_without_ids(self):
        c, s = sync_client({("POST", path("changes/bulk/")): {"action": "approve"}})
        c.bulk_change_action(D, action="approve", batch_id="6f1c2f0e-0000-4000-8000-000000000000")
        assert s.body() == {"action": "approve", "batch_id": "6f1c2f0e-0000-4000-8000-000000000000"}

    def test_resource_batch_id_without_ids(self):
        c, s = sync_client({("POST", path("changes/bulk/")): {}})
        c.website(D).bulk_change_action(action="approve", batch_id="b")
        assert s.body() == {"action": "approve", "batch_id": "b"}

    async def test_async_resource_batch_id_without_ids(self):
        c, s = async_client({("POST", path("changes/bulk/")): {}})
        await c.website(D).bulk_change_action(action="approve", batch_id="b")
        assert s.body() == {"action": "approve", "batch_id": "b"}

    def test_ids_still_work(self):
        c, s = sync_client({("POST", path("changes/bulk/")): {}})
        c.bulk_change_action(D, action="approve", ids=[1, 2])
        assert s.body() == {"action": "approve", "ids": [1, 2]}

    def test_neither_ids_nor_batch_id_is_a_usage_error(self):
        c, s = sync_client({})
        with pytest.raises(ValueError):
            c.bulk_change_action(D, action="approve")
        assert s.requests == []


# ---------------------------------------------------------------------------
# Action items
# ---------------------------------------------------------------------------


class TestActionItems:
    # actionitems/api_views.py:166-183
    @pytest.mark.parametrize("action", ["done", "in_progress", "dismiss", "reopen"])
    def test_update_body_is_action_only(self, action):
        c, s = sync_client({("PATCH", path("action-items/9/")): {"id": 9}})
        c.update_action_item(D, 9, action=action)
        assert s.body() == {"action": action}

    def test_snooze_days_removed(self):
        c, _ = sync_client({})
        with pytest.raises(TypeError):
            c.update_action_item(D, 9, action="done", snooze_days=3)  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            c.website(D).update_action_item(9, action="done", snooze_days=3)  # type: ignore[call-arg]

    async def test_async_resource_update_body(self):
        c, s = async_client({("PATCH", path("action-items/9/")): {"id": 9}})
        await c.website(D).update_action_item(9, action="reopen")
        assert s.body() == {"action": "reopen"}

    @pytest.mark.parametrize("bad", ["complete", "snooze", "snoozed"])
    def test_actions_the_server_rejects_fail_before_the_request(self, bad):
        c, s = sync_client({})
        with pytest.raises(ValueError):
            c.update_action_item(D, 9, action=bad)
        assert s.requests == []


# ---------------------------------------------------------------------------
# Pages / keywords params
# ---------------------------------------------------------------------------


class TestListParams:
    # views.py:400
    def test_list_pages_url(self):
        c, s = sync_client({("GET", path("pages/")): PAGED})
        c.list_pages(D, url="https://example.com/a")
        assert s.last.url.params["url"] == "https://example.com/a"

    def test_resource_pages_url(self):
        c, s = sync_client({("GET", path("pages/")): PAGED})
        c.website(D).pages(url="https://example.com/a")
        assert s.last.url.params["url"] == "https://example.com/a"

    async def test_async_resource_pages_url(self):
        c, s = async_client({("GET", path("pages/")): PAGED})
        await c.website(D).pages(url="https://example.com/a")
        assert s.last.url.params["url"] == "https://example.com/a"

    # views.py:1572 -- only the literal "true" enables it
    def test_list_keywords_include_serp(self):
        c, s = sync_client({("GET", path("keywords/")): PAGED})
        c.list_keywords(D, include_serp=True)
        assert s.last.url.params["include_serp"] == "true"

    def test_resource_keywords_include_serp(self):
        c, s = sync_client({("GET", path("keywords/")): PAGED})
        c.website(D).keywords(include_serp=True)
        assert s.last.url.params["include_serp"] == "true"

    async def test_async_resource_keywords_include_serp(self):
        c, s = async_client({("GET", path("keywords/")): PAGED})
        await c.website(D).keywords(include_serp=True)
        assert s.last.url.params["include_serp"] == "true"


# ---------------------------------------------------------------------------
# Async top level
# ---------------------------------------------------------------------------


class TestAsyncTopLevel:
    # views.py:221-232
    async def test_list_websites(self):
        c, s = async_client({("GET", f"{BASE}/websites/"): {"results": [{"domain": D}]}})
        out = await c.list_websites()
        assert out["results"][0]["domain"] == D

    async def test_get_website(self):
        c, s = async_client({("GET", f"{BASE}/websites/{D}/"): {"domain": D}})
        out = await c.get_website(D)
        assert out["domain"] == D


# ---------------------------------------------------------------------------
# 402 and transport errors
# ---------------------------------------------------------------------------


GATE_402 = {
    "error": "subscription_required",
    "message": "Subscribe to continue.",
    "checkout_url": "https://seojuice.com/checkout/abc",
    "lock_state": "trial_expired",
}


def _pre():
    from seojuice._exceptions import PaymentRequiredError

    return PaymentRequiredError


class TestPaymentRequired:
    # organization/single_gate.py:539-546
    def test_402_maps_to_typed_exception(self):
        c, _ = sync_client({("GET", f"{BASE}/websites/"): httpx.Response(402, json=GATE_402)})
        with pytest.raises(_pre()) as ei:
            c.list_websites()
        e = ei.value
        assert e.status_code == 402
        assert e.error_code == "subscription_required"
        assert e.checkout_url == "https://seojuice.com/checkout/abc"
        assert e.lock_state == "trial_expired"
        assert isinstance(e, APIError)

    def test_402_without_extra_fields(self):
        c, _ = sync_client({("GET", f"{BASE}/websites/"): httpx.Response(402, json={"error": "x", "message": "m"})})
        with pytest.raises(_pre()) as ei:
            c.list_websites()
        assert ei.value.checkout_url is None
        assert ei.value.lock_state is None

    async def test_async_402(self):
        c, _ = async_client({("GET", f"{BASE}/websites/{D}/"): httpx.Response(402, json=GATE_402)})
        with pytest.raises(_pre()) as ei:
            await c.get_website(D)
        assert ei.value.checkout_url == "https://seojuice.com/checkout/abc"


class TestPdfTransportErrors:
    def _handler(self, exc: Exception) -> Callable[[httpx.Request], httpx.Response]:
        def h(request: httpx.Request) -> httpx.Response:
            raise exc

        return h

    def test_sync_timeout(self):
        http = httpx.Client(transport=httpx.MockTransport(self._handler(httpx.ConnectTimeout("t"))), base_url="https://seojuice.com/api/v2")
        c = SEOJuice("k", http_client=http)
        with pytest.raises(APITimeoutError):
            c.website(D).report_pdf(3)

    def test_sync_connection_error(self):
        from seojuice._exceptions import APIConnectionError

        http = httpx.Client(transport=httpx.MockTransport(self._handler(httpx.ConnectError("c"))), base_url="https://seojuice.com/api/v2")
        c = SEOJuice("k", http_client=http)
        with pytest.raises(APIConnectionError):
            c.website(D).report_pdf(3)

    async def test_async_timeout(self):
        http = httpx.AsyncClient(transport=httpx.MockTransport(self._handler(httpx.ReadTimeout("t"))), base_url="https://seojuice.com/api/v2")
        c = AsyncSEOJuice("k", http_client=http)
        with pytest.raises(APITimeoutError):
            await c.website(D).report_pdf(3)


# ---------------------------------------------------------------------------
# README and examples must call the server with values it accepts
# ---------------------------------------------------------------------------

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)

# partners/views.py:2774-2790 (+ exclude_paths); actionitems/api_views.py:166-183
SETTINGS_KEYS = {
    "internal_links_mode", "meta_tags_mode", "og_tags_mode", "title_tags_mode",
    "h1_tags_mode", "structured_data_mode", "image_alt_mode",
    "accessibility_mode", "local_seo_mode", "gbp_review_reply_mode",
    "max_changes_per_page_per_day", "max_changes_per_day", "exclude_paths",
}
ACTIONS = {"done", "in_progress", "dismiss", "dismissed", "reopen", "open"}
EFFORTS = {"easy", "medium", "hard"}  # actionitems/models.py:140-156
# Keys the server never sends (actionitems/api_views.py:217-278,
# actionitems/serializers.py:38-50, partners/views.py:1442-1446 and
# serializers.py:774-783).
ABSENT_KEYS = {"count", "overall_score", "snoozed", "similarity_score", "priority_distribution"}


def _trees() -> List[Tuple[str, ast.AST]]:
    out: List[Tuple[str, ast.AST]] = []
    for i, src in enumerate(_FENCE.findall((ROOT / "README.md").read_text())):
        out.append((f"README fence {i}", ast.parse(src)))
    for f in sorted((ROOT / "examples").glob("*.py")):
        out.append((f.name, ast.parse(f.read_text())))
    return out


def _calls(name: str):
    for where, tree in _trees():
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name:
                yield where, n


def _str_const(node: ast.AST):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


class TestDocsMatchServer:
    def test_update_action_item_actions(self):
        seen = 0
        for where, call in _calls("update_action_item"):
            for kw in call.keywords:
                if kw.arg == "action" and _str_const(kw.value) is not None:
                    seen += 1
                    assert _str_const(kw.value) in ACTIONS, (where, kw.value.value)
                assert kw.arg != "snooze_days", where
        assert seen

    def test_update_change_settings_keys(self):
        seen = 0
        for where, call in _calls("update_change_settings"):
            for kw in call.keywords:
                seen += 1
                assert kw.arg in SETTINGS_KEYS, (where, kw.arg)
        assert seen

    def test_create_action_item_effort(self):
        for where, call in _calls("create_action_item"):
            for kw in call.keywords:
                if kw.arg == "estimated_effort":
                    assert _str_const(kw.value) in EFFORTS, where

    def test_no_keys_the_server_never_sends(self):
        for where, tree in _trees():
            for n in ast.walk(tree):
                key = None
                if isinstance(n, ast.Subscript):
                    key = _str_const(n.slice)
                elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args:
                    key = _str_const(n.args[0])
                assert key not in ABSENT_KEYS, (where, key)

    def test_reject_change_always_has_reason(self):
        for where, call in _calls("reject_change"):
            assert any(kw.arg == "reason" for kw in call.keywords), where
