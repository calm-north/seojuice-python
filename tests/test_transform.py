from __future__ import annotations

import json
from typing import Any, Dict

from seojuice.injection._transform import (
    Manifest,
    escape_html,
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
