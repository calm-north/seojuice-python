from __future__ import annotations

from seojuice.injection._transform import escape_html, normalize_image_url, tokenize_html


def test_escape_html_uses_numeric_apostrophe():
    assert escape_html("a'b<c>&\"d") == "a&#039;b&lt;c&gt;&amp;&quot;d"


def test_normalize_image_url_strips_scheme_and_query():
    assert normalize_image_url("https://x.com/a.png?w=1") == "//x.com/a.png"
    assert normalize_image_url("http://x.com/a.png") == "//x.com/a.png"


def test_tokenize_html_splits_text_and_tags():
    assert tokenize_html("a<b>c</b>") == [("text", "a"), ("tag", "<b>"), ("text", "c"), ("tag", "</b>")]
