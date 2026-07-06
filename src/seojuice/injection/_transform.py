from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class Manifest:
    cs: List[int] = field(default_factory=list)
    meta: List[str] = field(default_factory=list)
    img: int = 0
    schema: int = 0
    h1: int = 0


def escape_html(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    url = url.split("?")[0]
    if url.startswith("https:"):
        return url[6:]
    if url.startswith("http:"):
        return url[5:]
    return url


_TAG_RE = re.compile(r"(<[^>]*>)")


def tokenize_html(html: str) -> List[Tuple[str, str]]:
    segments: List[Tuple[str, str]] = []
    last = 0
    for m in _TAG_RE.finditer(html):
        if m.start() > last:
            segments.append(("text", html[last : m.start()]))
        segments.append(("tag", m.group(0)))
        last = m.end()
    if last < len(html):
        segments.append(("text", html[last:]))
    return segments


SKIP_TAG_RE = re.compile(r"^<(a|script|style|title|h[1-6])[\s/>]", re.IGNORECASE)
CLOSE_TAG_RE = re.compile(r"^</(a|script|style|title|h[1-6])>", re.IGNORECASE)

_HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)


def replace_meta_tags(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    title = data.get("title")
    if title and not re.search(r"<title[\s>]", html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<title data-seojuice="title">{escape_html(title)}</title>\n</head>', html, count=1
        )
        manifest.meta.append("title")

    meta_description = data.get("meta_description")
    if meta_description and not re.search(r'<meta\s+name=["\']description["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta name="description" content="{escape_html(meta_description)}" data-seojuice="meta-description">\n</head>',
            html,
            count=1,
        )
        manifest.meta.append("meta-description")

    meta_keywords = data.get("meta_keywords")
    if meta_keywords and not re.search(r'<meta\s+name=["\']keywords["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta name="keywords" content="{escape_html(meta_keywords)}" data-seojuice="meta-keywords">\n</head>',
            html,
            count=1,
        )
        manifest.meta.append("meta-keywords")

    og_title = data.get("og_title")
    if og_title and not re.search(r'<meta\s+property=["\']og:title["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta property="og:title" content="{escape_html(og_title)}" data-seojuice="og-title">\n</head>',
            html,
            count=1,
        )
        manifest.meta.append("og-title")

    og_description = data.get("og_description")
    if og_description and not re.search(r'<meta\s+property=["\']og:description["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta property="og:description" content="{escape_html(og_description)}" data-seojuice="og-description">\n</head>',
            html,
            count=1,
        )
        manifest.meta.append("og-description")

    og_url = data.get("og_url")
    if og_url and not re.search(r'<meta\s+property=["\']og:url["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta property="og:url" content="{escape_html(og_url)}">\n</head>', html, count=1
        )

    og_image = data.get("og_image")
    if og_image and not re.search(r'<meta\s+property=["\']og:image["\']', html, re.IGNORECASE):
        html = _HEAD_CLOSE_RE.sub(
            f'<meta property="og:image" content="{escape_html(og_image)}">\n</head>', html, count=1
        )

    raw = data.get("structured_data")
    if raw and raw != "null":
        try:
            inner = json.loads(raw)
            obj = json.loads(inner)
            if not re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>', html, re.IGNORECASE):
                tag = (
                    '<script type="application/ld+json" data-seojuice="schema">'
                    f"{json.dumps(obj, separators=(',', ':'))}</script>"
                )
                html = re.sub(r"</head>", tag + "\n</head>", html, count=1, flags=re.IGNORECASE)
                manifest.schema = 1
        except (ValueError, TypeError):
            pass

    return html


def replace_h1(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    h1 = data.get("h1")
    if not h1:
        return html

    def _repl(m: "re.Match[str]") -> str:
        open_tag, close_tag = m.group(1), m.group(3)
        marked_open = open_tag
        if "data-seojuice=" not in marked_open:
            marked_open = re.sub(r">$", ' data-seojuice="h1">', marked_open)
        manifest.h1 = 1
        return marked_open + escape_html(h1) + close_tag

    return re.sub(r"(<h1[^>]*>)([\s\S]*?)(</h1>)", _repl, html, count=1, flags=re.IGNORECASE)


_IMG_RE = re.compile(r"<img([^>]+)>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'(?:src|data-src)=["\']([^"\']+)["\']')
_IMG_ALT_RE = re.compile(r'alt=["\']([^"\']*)["\']')


def replace_images(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    images = data.get("images")
    if not isinstance(images, list):
        return html

    image_map: Dict[str, str] = {}
    for img in images:
        url = img.get("url")
        alt_text = img.get("alt_text")
        if url and alt_text:
            image_map[normalize_image_url(url)] = alt_text

    if not image_map:
        return html

    def _repl(m: "re.Match[str]") -> str:
        match, attributes = m.group(0), m.group(1)
        src_match = _IMG_SRC_RE.search(attributes)
        if not src_match:
            return match

        normalized_src = normalize_image_url(src_match.group(1))
        if normalized_src not in image_map:
            return match

        alt_match = _IMG_ALT_RE.search(match)
        existing_alt = alt_match.group(1) if alt_match else ""
        if existing_alt and len(existing_alt) >= 5:
            return match

        alt_text = escape_html(image_map[normalized_src])
        manifest.img += 1

        if alt_match:
            replaced = _IMG_ALT_RE.sub(f'alt="{alt_text}"', match, count=1)
            if "data-seojuice=" not in replaced:
                replaced = replaced.replace("<img", '<img data-seojuice="alt"', 1)
            return replaced
        return match.replace("<img", f'<img alt="{alt_text}" data-seojuice="alt"', 1)

    return _IMG_RE.sub(_repl, html)


_ASIAN = r"一-鿿぀-ゟ゠-ヿ"


def _keyword_pattern(keyword: str, is_asian: bool) -> "re.Pattern[str]":
    kw = re.escape(keyword)
    if is_asian:
        return re.compile(rf"(^|[{_ASIAN}])({kw})(?=[{_ASIAN}.!?)\]/]|$)")
    pre = r"(^|[\s([{<>\"'«‹„/:\-])"
    post = r"(?=$|[\s)\]}>\"'»›/.,:;!?\-])"
    return re.compile(pre + rf"({kw})" + post, re.IGNORECASE)


def inject_internal_links(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    suggestions = data.get("suggestions")
    if not isinstance(suggestions, list) or not suggestions:
        return html

    is_asian = bool(data.get("isAsian"))
    custom_link_class = data.get("custom_link_class") or ""

    replaced_keywords: set[str] = set()
    links: List[Dict[str, Any]] = []
    for link in suggestions:
        keyword = link.get("keyword")
        url = link.get("url")
        if not keyword or not url:
            continue
        kl = keyword.lower()
        if kl in replaced_keywords:
            continue
        links.append(
            {
                "keyword": keyword,
                "kl": kl,
                "url": url,
                "id": link.get("id"),
                "pattern": _keyword_pattern(keyword, is_asian),
            }
        )

    if not links:
        return html

    segments = tokenize_html(html)
    skip_depth = 0
    result: List[str] = []

    for seg_type, value in segments:
        if seg_type == "tag":
            if SKIP_TAG_RE.match(value):
                skip_depth += 1
            elif CLOSE_TAG_RE.match(value) and skip_depth > 0:
                skip_depth -= 1
            result.append(value)
            continue

        text = value
        if skip_depth == 0:
            for link in links:
                if link["kl"] in replaced_keywords:
                    continue

                def _repl(m: "re.Match[str]", link: Dict[str, Any] = link) -> str:
                    prefix = m.group(1) or ""
                    class_attr = f' class="seojuice-link {custom_link_class}"' if custom_link_class else ""
                    cs_attr = f' data-seojuice-cs="{link["id"]}"' if link["id"] is not None else ""
                    anchor = (
                        f'<a href="{escape_html(link["url"])}"{class_attr}{cs_attr}>'
                        f'{escape_html(link["keyword"])}</a>'
                    )
                    return prefix + anchor

                text, n = link["pattern"].subn(_repl, text, count=1)
                if n:
                    replaced_keywords.add(link["kl"])
                    if link["id"] is not None:
                        manifest.cs.append(link["id"])
        result.append(text)

    return "".join(result)
