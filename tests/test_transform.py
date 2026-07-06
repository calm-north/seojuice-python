from __future__ import annotations

import json
from typing import Any, Dict

from seojuice.injection._transform import (
    Manifest,
    apply_broken_link_fixes,
    apply_content_diffs,
    escape_html,
    inject_internal_links,
    normalize_image_url,
    replace_h1,
    replace_images,
    replace_meta_tags,
    tokenize_html,
)


def _data(**kw: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "suggestions": [],
        "images": [],
        "diffs": [],
        "broken_link_fixes": [],
        "title": "",
        "meta_description": "",
        "meta_keywords": "",
        "og_title": "",
        "og_description": "",
        "og_url": "",
        "og_image": "",
        "structured_data": "",
        "h1": "",
        "isAsian": False,
        "custom_link_class": "",
        "insert_into_content_only": False,
        "errors": [],
    }
    base.update(kw)
    return base


def test_escape_html_uses_numeric_apostrophe():
    assert escape_html("a'b<c>&\"d") == "a&#039;b&lt;c&gt;&amp;&quot;d"


def test_normalize_image_url_strips_scheme_and_query():
    assert normalize_image_url("https://x.com/a.png?w=1") == "//x.com/a.png"
    assert normalize_image_url("http://x.com/a.png") == "//x.com/a.png"


def test_tokenize_html_splits_text_and_tags():
    assert tokenize_html("a<b>c</b>") == [("text", "a"), ("tag", "<b>"), ("text", "c"), ("tag", "</b>")]


# ---------------------------------------------------------------------------
# replace_meta_tags / replace_h1 (Task 2)
# ---------------------------------------------------------------------------


def test_title_added_only_when_absent():
    assert '<title data-seojuice="title">Hi</title>' in replace_meta_tags("<head></head>", _data(title="Hi"), Manifest())
    assert "<title>X</title>" in replace_meta_tags("<head><title>X</title></head>", _data(title="Hi"), Manifest())


def test_structured_data_double_decoded():
    inner = {"@context": "https://schema.org", "@type": "Article"}
    out = replace_meta_tags("<head></head>", _data(structured_data=json.dumps(json.dumps(inner))), Manifest())
    assert (
        '<script type="application/ld+json" data-seojuice="schema">{"@context":"https://schema.org","@type":"Article"}</script>'
        in out
    )


def test_h1_replaced_and_marked():
    assert replace_h1("<h1 class='t'>old</h1>", _data(h1="New"), Manifest()) == '<h1 class=\'t\' data-seojuice="h1">New</h1>'


# ---------------------------------------------------------------------------
# replace_images (Task 3)
# ---------------------------------------------------------------------------


def test_fills_empty_alt_by_normalized_url():
    data = {**_data(), "images": [{"url": "https://cdn.x/a.png", "alt_text": "A nice chart"}]}
    out = replace_images('<img src="https://cdn.x/a.png?v=2">', data, Manifest())
    assert out == '<img alt="A nice chart" data-seojuice="alt" src="https://cdn.x/a.png?v=2">'


def test_keeps_good_alt():
    data = {**_data(), "images": [{"url": "https://cdn.x/a.png", "alt_text": "A nice chart"}]}
    html = '<img src="https://cdn.x/a.png" alt="already meaningful">'
    assert replace_images(html, data, Manifest()) == html


# ---------------------------------------------------------------------------
# inject_internal_links (Task 4)
# ---------------------------------------------------------------------------


def test_links_first_occurrence_only():
    data = {**_data(), "suggestions": [{"keyword": "SWP plan", "url": "/swp", "id": 7}]}
    out = inject_internal_links("<p>Learn SWP plan. Another SWP plan here.</p>", data, Manifest())
    assert out == '<p>Learn <a href="/swp" data-seojuice-cs="7">SWP plan</a>. Another SWP plan here.</p>'


def test_never_links_inside_anchor_or_heading():
    data = {**_data(), "suggestions": [{"keyword": "SWP", "url": "/swp", "id": 1}]}
    assert inject_internal_links('<a href="/x">SWP</a>', data, Manifest()) == '<a href="/x">SWP</a>'
    assert inject_internal_links("<h1>SWP</h1>", data, Manifest()) == "<h1>SWP</h1>"


def test_asian_boundary_links_between_han():
    data = {**_data(), "isAsian": True, "suggestions": [{"keyword": "投资", "url": "/x", "id": 2}]}
    out = inject_internal_links("<p>我要投资基金</p>", data, Manifest())
    assert '<a href="/x" data-seojuice-cs="2">投资</a>' in out


# ---------------------------------------------------------------------------
# apply_content_diffs (Task 5)
# ---------------------------------------------------------------------------


def test_applies_unique_diff_with_marker():
    out = apply_content_diffs(
        "<div><p>old copy</p></div>",
        [{"id": 9, "original_text": "<p>old copy</p>", "replacement_html": "<p>new copy</p>"}],
        Manifest(),
    )
    assert out == '<div><p data-seojuice-cs="9">new copy</p></div>'


def test_skips_ambiguous():
    html = "<p>dup</p><p>dup</p>"
    assert apply_content_diffs(html, [{"id": 1, "original_text": "dup", "replacement_html": "X"}], Manifest()) == html


def test_skips_drifted():
    html = "<p>present</p>"
    assert (
        apply_content_diffs(html, [{"id": 1, "original_text": "missing", "replacement_html": "X"}], Manifest()) == html
    )


# ---------------------------------------------------------------------------
# apply_broken_link_fixes (Task 6)
# ---------------------------------------------------------------------------


def test_replace_edge_new_url():
    assert (
        apply_broken_link_fixes(
            '<a href="/dead">x</a>',
            [{"action": "replace", "tag": "a", "attr": "href", "broken_url": "/dead", "new_url": "/live"}],
        )
        == '<a href="/live">x</a>'
    )


def test_replace_legacy_replacement_url():
    assert (
        apply_broken_link_fixes(
            '<a href="/dead">x</a>',
            [
                {
                    "action": "replace",
                    "tag": "a",
                    "attr": "href",
                    "broken_url": "/dead",
                    "new_url": "",
                    "replacement_url": "/live",
                }
            ],
        )
        == '<a href="/live">x</a>'
    )


def test_unlink_removes_anchor():
    assert (
        apply_broken_link_fixes(
            'before<a href="/dead">x</a>after',
            [{"action": "unlink", "tag": "a", "attr": "href", "broken_url": "/dead"}],
        )
        == "beforeafter"
    )


def test_does_not_touch_data_href():
    html = '<a data-href="/dead">x</a>'
    assert (
        apply_broken_link_fixes(
            html,
            [{"action": "replace", "tag": "a", "attr": "href", "broken_url": "/dead", "new_url": "/live"}],
        )
        == html
    )
