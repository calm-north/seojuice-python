from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from seojuice.injection._fetcher import apply_suggestions

VDIR = Path(__file__).parent / "fixtures" / "ssr-parity-vectors"

# This vector intentionally pins the *raw Worker's* known gap (it reads only
# fix.new_url, never falling back to fix.replacement_url) rather than the SDK's
# required behavior. Per the vector's own "notes" field: "the fallback is a
# deliberate SDK-side delta from the raw Worker and is verified by each SDK's
# own unit tests ... NOT by this shared vector." sdk-python implements the
# delta in `apply_broken_link_fixes` (Task 6, covered by
# test_replace_legacy_replacement_url in test_transform.py), so its output for
# this vector legitimately differs from expected_html — verified below instead.
_WORKER_GAP_VECTORS = {"brokenlink_legacy_replacement_url_worker_noop"}


def _norm(html: str) -> str:
    return re.sub(r"\s+", " ", html).strip()


@pytest.mark.parametrize(
    "vf",
    [p for p in sorted(VDIR.glob("*.json")) if p.stem not in _WORKER_GAP_VECTORS],
    ids=lambda p: p.stem,
)
def test_matches_worker_vector(vf: Path) -> None:
    v = json.loads(vf.read_text())
    assert _norm(apply_suggestions(v["input_html"], v["payload"])) == _norm(v["expected_html"])


def test_legacy_replacement_url_fallback_is_sdk_delta_from_worker_gap() -> None:
    """sdk-python deliberately diverges from brokenlink_legacy_replacement_url_worker_noop.

    The raw Worker silently no-ops when only `replacement_url` is set (bug: it
    never reads that field). sdk-python's `apply_broken_link_fixes` implements
    the documented spec delta (`new_url or replacement_url`), so it actually
    fixes the link here instead of leaving it broken.
    """
    vf = VDIR / "brokenlink_legacy_replacement_url_worker_noop.json"
    v = json.loads(vf.read_text())
    out = apply_suggestions(v["input_html"], v["payload"])
    assert 'href="/live-page2"' in out
    assert 'href="/dead-page2"' not in out
