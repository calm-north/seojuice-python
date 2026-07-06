from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple


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
