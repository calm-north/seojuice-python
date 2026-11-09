from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlsplit


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


def _unwrap_next_image_url(url: str) -> str:
    # Next.js optimizer: the image is the `url` param, not the endpoint.
    try:
        parsed = urlsplit(url)
        if parsed.path != "/_next/image":
            return url
        values = parse_qs(parsed.query).get("url")
        if not values or not values[0]:
            return url
        return urljoin(url, values[0]) if parsed.netloc else values[0]
    except ValueError:
        return url


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    url = _unwrap_next_image_url(url).split("?")[0]
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


_LD_JSON_BLOCK_RE = re.compile(
    r'<script([^>]*type=["\']application/ld\+json["\'][^>]*)>([\s\S]*?)</script>',
    re.IGNORECASE,
)
_OWN_ATTR_RE = re.compile(r"\sdata-seojuice(?=[\s=>/]|$)", re.IGNORECASE)

# Mirrors SCHEMA_COVERS in seojuice-ssr.js: a proposed type is redundant when
# any covering type is already on the page.
_SCHEMA_COVERS: Dict[str, List[str]] = {
    "Article": ["Article", "BlogPosting", "NewsArticle", "TechArticle", "ScholarlyArticle", "Report"],
    "WebPage": [
        "WebPage", "CollectionPage", "AboutPage", "ContactPage", "ItemPage", "ProfilePage", "FAQPage",
        "QAPage", "SearchResultsPage", "CheckoutPage", "MedicalWebPage", "RealEstateListing",
    ],
    "Organization": [
        "Organization", "Corporation", "NGO", "EducationalOrganization", "School", "CollegeOrUniversity",
        "ElementarySchool", "HighSchool", "MiddleSchool", "Preschool", "GovernmentOrganization",
        "NewsMediaOrganization", "MedicalOrganization", "ResearchOrganization", "SportsOrganization",
        "SportsTeam", "PerformingGroup", "OnlineBusiness", "OnlineStore", "Airline", "Consortium",
        "LibrarySystem", "WorkersUnion", "LocalBusiness", "AccountingService", "AutomotiveBusiness",
        "AutoDealer", "AutoRepair", "Dentist", "EmergencyService", "EntertainmentBusiness",
        "FinancialService", "FoodEstablishment", "Bakery", "BarOrPub", "CafeOrCoffeeShop", "Restaurant",
        "GovernmentOffice", "HealthAndBeautyBusiness", "BeautySalon", "DaySpa", "HairSalon",
        "HomeAndConstructionBusiness", "Electrician", "GeneralContractor", "Plumber", "InternetCafe",
        "LegalService", "Attorney", "Notary", "LodgingBusiness", "Hotel", "Hostel", "Motel",
        "MedicalBusiness", "Pharmacy", "Physician", "ProfessionalService", "RealEstateAgent",
        "RecyclingCenter", "SelfStorage", "ShoppingCenter", "SportsActivityLocation", "Store",
        "TouristInformationCenter", "TravelAgency", "Person",
    ],
}


def _strip_own_ld_json(html: str) -> str:
    def repl(m: "re.Match[str]") -> str:
        return "" if _OWN_ATTR_RE.search(m.group(1)) else m.group(0)

    return re.sub(
        r'<script([^>]*type=["\']application/ld\+json["\'][^>]*)>[\s\S]*?</script>\n?',
        lambda m: repl(m),
        html,
        flags=re.IGNORECASE,
    )


def _collect_ld_json_types(node: Any, types: set) -> None:  # type: ignore[type-arg]
    if isinstance(node, list):
        for item in node:
            _collect_ld_json_types(item, types)
        return
    if not isinstance(node, dict):
        return
    graph = node.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            _collect_ld_json_types(item, types)
    t = node.get("@type")
    if isinstance(t, str):
        types.add(t)
    elif isinstance(t, list):
        types.update(x for x in t if isinstance(x, str))


def _collect_present_ld_json_types(html: str) -> set:  # type: ignore[type-arg]
    types: set = set()  # type: ignore[type-arg]
    for m in _LD_JSON_BLOCK_RE.finditer(html):
        if _OWN_ATTR_RE.search(m.group(1)):
            continue
        try:
            _collect_ld_json_types(json.loads(m.group(2)), types)
        except ValueError:
            continue
    return types


def _is_type_covered(proposed: str, present: set) -> bool:  # type: ignore[type-arg]
    return any(t in present for t in _SCHEMA_COVERS.get(proposed, [proposed]))


def _ld_json_node_already_present(node: Any, present: set) -> bool:  # type: ignore[type-arg]
    if not isinstance(node, dict):
        return False
    t = node.get("@type")
    if isinstance(t, str):
        return _is_type_covered(t, present)
    if isinstance(t, list) and t:
        return all(isinstance(x, str) and _is_type_covered(x, present) for x in t)
    return False


def _normalize_schema_nodes(obj: Any) -> List[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and isinstance(obj.get("@graph"), list):
        return obj["@graph"]
    return [obj]


def replace_meta_tags(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    title = data.get("title")
    if title and not re.search(r"<title[\s>]", html, re.IGNORECASE):
        injection = f'<title data-seojuice="title">{escape_html(title)}</title>\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)
        manifest.meta.append("title")

    meta_description = data.get("meta_description")
    if meta_description and not re.search(r'<meta\s+name=["\']description["\']', html, re.IGNORECASE):
        injection = f'<meta name="description" content="{escape_html(meta_description)}" data-seojuice="meta-description">\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)
        manifest.meta.append("meta-description")

    meta_keywords = data.get("meta_keywords")
    if meta_keywords and not re.search(r'<meta\s+name=["\']keywords["\']', html, re.IGNORECASE):
        injection = f'<meta name="keywords" content="{escape_html(meta_keywords)}" data-seojuice="meta-keywords">\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)
        manifest.meta.append("meta-keywords")

    og_title = data.get("og_title")
    if og_title and not re.search(r'<meta\s+property=["\']og:title["\']', html, re.IGNORECASE):
        injection = f'<meta property="og:title" content="{escape_html(og_title)}" data-seojuice="og-title">\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)
        manifest.meta.append("og-title")

    og_description = data.get("og_description")
    if og_description and not re.search(r'<meta\s+property=["\']og:description["\']', html, re.IGNORECASE):
        injection = (
            f'<meta property="og:description" content="{escape_html(og_description)}" data-seojuice="og-description">\n'
        )
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)
        manifest.meta.append("og-description")

    og_url = data.get("og_url")
    if og_url and not re.search(r'<meta\s+property=["\']og:url["\']', html, re.IGNORECASE):
        injection = f'<meta property="og:url" content="{escape_html(og_url)}">\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)

    og_image = data.get("og_image")
    if og_image and not re.search(r'<meta\s+property=["\']og:image["\']', html, re.IGNORECASE):
        injection = f'<meta property="og:image" content="{escape_html(og_image)}">\n'
        html = _HEAD_CLOSE_RE.sub(lambda m, injection=injection: injection + m.group(0), html, count=1)

    raw = data.get("structured_data")
    if raw and raw != "null":
        try:
            # Mirror seojuice-ssr.js replaceMetaTags: the payload is a single
            # json.dumps(); a legacy caller may double-encode, so parse again
            # when the first parse yields a string.
            obj = json.loads(raw)
            if isinstance(obj, str):
                obj = json.loads(obj)
        except (ValueError, TypeError):
            return html
        nodes = _normalize_schema_nodes(obj)
        html = _strip_own_ld_json(html)
        present = _collect_present_ld_json_types(html)
        missing = [n for n in nodes if not _ld_json_node_already_present(n, present)]
        if missing:
            payload = json.dumps(missing, separators=(",", ":"), ensure_ascii=False)
            payload = payload.replace("<", "\\u003c")
            tag = (
                '<script type="application/ld+json" data-seojuice="schema">'
                f"{payload}</script>"
            )
            html = _HEAD_CLOSE_RE.sub(
                lambda m, tag=tag: tag + "\n" + m.group(0), html, count=1
            )
            manifest.schema = 1

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
_IMG_ALT_RE = re.compile(r'alt=["\']([^"\']*)["\']')

_IMAGE_ATTRS = ("src", "data-src", "data-lazy-src", "data-lazy", "data-original")
_IMAGE_SRCSET_ATTRS = ("srcset", "data-srcset")
# decodeURI leaves these escapes in place (reserved characters).
_DECODE_URI_KEEP = ";/?:@&=+$,#"


def _read_attr(attributes: str, name: str) -> Optional[str]:
    m = re.search(
        r"(?:^|\s)" + re.escape(name) + r"\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",
        attributes,
        re.IGNORECASE,
    )
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def _image_candidates(attributes: str) -> List[str]:
    out: List[str] = []
    for name in _IMAGE_ATTRS:
        v = _read_attr(attributes, name)
        if v:
            out.append(v)
    for name in _IMAGE_SRCSET_ATTRS:
        v = _read_attr(attributes, name)
        if v:
            for part in v.split(","):
                pieces = part.strip().split()
                if pieces:
                    out.append(pieces[0])
    return out


def _strip_scheme_and_query(url: str) -> str:
    if not url:
        return ""
    url = url.split("?")[0]
    if url.startswith("https:"):
        return url[6:]
    if url.startswith("http:"):
        return url[5:]
    return url


def _decode_uri(path: str) -> str:
    return re.sub(r"(?:%[0-9A-Fa-f]{2})+", lambda m: _decode_run(m.group(0)), path)


def _decode_run(run: str) -> str:
    raw = bytes(int(run[i + 1 : i + 3], 16) for i in range(0, len(run), 3))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return run
    # Keep reserved characters escaped, as decodeURI does.
    out = []
    for ch in text:
        if ch in _DECODE_URI_KEEP:
            out.append("%%%02X" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def _match_key(candidate: str, base: Optional[str], unwrapped: bool = False) -> Optional[str]:
    """Port of matchKey in seojuice-ssr.js: resolve against ``base``, unwrap a
    Next.js optimizer URL once, decode the path, drop scheme and query."""
    if not candidate:
        return None
    try:
        resolved = urljoin(base or "", candidate)
        parts = urlsplit(resolved)
        if not parts.scheme:
            raise ValueError("relative url without base")
    except ValueError:
        if re.match(r"^(data|blob):", candidate, re.IGNORECASE):
            return None
        return _strip_scheme_and_query(candidate)
    if parts.scheme in ("data", "blob"):
        return None
    if not unwrapped and parts.path == "/_next/image":
        values = parse_qs(parts.query).get("url")
        if values and values[0]:
            return _match_key(values[0], resolved, True)
    host = parts.netloc.rsplit("@", 1)[-1].lower()
    return _strip_scheme_and_query(f"{parts.scheme}://{host}{_decode_uri(parts.path)}")


def replace_images(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    images = data.get("images")
    if not isinstance(images, list):
        return html
    base = data.get("base") or None

    image_map: Dict[str, str] = {}
    for img in images:
        url = img.get("url")
        alt_text = img.get("alt_text")
        if url and alt_text:
            key = _match_key(url, base)
            if key is not None:
                image_map[key] = alt_text

    if not image_map:
        return html

    def _repl(m: "re.Match[str]") -> str:
        match, attributes = m.group(0), m.group(1)
        matched_alt = None
        for candidate in _image_candidates(attributes):
            key = _match_key(candidate, base)
            if key is not None and key in image_map:
                matched_alt = image_map[key]
                break
        if matched_alt is None:
            return match

        alt_match = _IMG_ALT_RE.search(match)
        existing_alt = alt_match.group(1) if alt_match else ""
        if existing_alt and len(existing_alt) >= 5:
            return match

        alt_text = escape_html(matched_alt)
        manifest.img += 1

        if alt_match:
            replaced = _IMG_ALT_RE.sub(lambda m, alt_text=alt_text: f'alt="{alt_text}"', match, count=1)
            if "data-seojuice=" not in replaced:
                replaced = replaced.replace("<img", '<img data-seojuice="alt"', 1)
            return replaced
        return match.replace("<img", f'<img alt="{alt_text}" data-seojuice="alt"', 1)

    return _IMG_RE.sub(_repl, html)


_ASIAN = r"一-鿿぀-ゟ゠-ヿ"


def _keyword_pattern(keyword: str, is_asian: bool) -> "re.Pattern[str]":
    kw = re.escape(keyword)
    if is_asian:
        # Lookahead includes full-width JP sentence punctuation (。、！？）」』)
        # so a keyword ending a Japanese sentence (投資信託。) still links (bug B).
        return re.compile(rf"(^|[{_ASIAN}])({kw})(?=[{_ASIAN}.!?)\]/。、！？）」』]|$)")
    pre = r"(^|[\s([{<>\"'«‹„/:|\-])"
    post = r"(?=$|[\s)\]}>\"'»›/.,:;!?|\-])"
    return re.compile(pre + rf"({kw})" + post, re.IGNORECASE)


BLOCK_CONTENT_RE = re.compile(r"^<(p|li|span|div|td|blockquote|dd|figcaption)[\s>]", re.IGNORECASE)
BLOCK_CONTENT_CLOSE_RE = re.compile(r"^</(p|li|span|div|td|blockquote|dd|figcaption)>", re.IGNORECASE)


def inject_internal_links(html: str, data: Dict[str, Any], manifest: Manifest) -> str:
    suggestions = data.get("suggestions")
    if not isinstance(suggestions, list) or not suggestions:
        return html

    is_asian = bool(data.get("isAsian"))
    custom_link_class = data.get("custom_link_class") or ""
    content_only = bool(data.get("insert_into_content_only"))

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
    block_depth = 0
    result: List[str] = []

    for seg_type, value in segments:
        if seg_type == "tag":
            if SKIP_TAG_RE.match(value):
                skip_depth += 1
            elif CLOSE_TAG_RE.match(value) and skip_depth > 0:
                skip_depth -= 1
            if BLOCK_CONTENT_RE.match(value):
                block_depth += 1
            elif BLOCK_CONTENT_CLOSE_RE.match(value) and block_depth > 0:
                block_depth -= 1
            result.append(value)
            continue

        text = value
        can_inject = skip_depth == 0 and (not content_only or block_depth > 0)
        if can_inject:
            for link in links:
                if link["kl"] in replaced_keywords:
                    continue

                def _repl(m: "re.Match[str]", link: Dict[str, Any] = link) -> str:
                    prefix = m.group(1) or ""
                    class_attr = f' class="seojuice-link {custom_link_class}"' if custom_link_class else ""
                    cs_attr = f' data-seojuice-cs="{link["id"]}"' if link["id"] is not None else ""
                    anchor = (
                        f'<a href="{escape_html(link["url"])}"{class_attr}{cs_attr}>'
                        f'{escape_html(m.group(0)[len(prefix):])}</a>'
                    )
                    return prefix + anchor

                text, n = link["pattern"].subn(_repl, text, count=1)
                if n:
                    replaced_keywords.add(link["kl"])
                    if link["id"] is not None:
                        manifest.cs.append(link["id"])
        result.append(text)

    return "".join(result)


_SINGLE_ROOT_RE = re.compile(r"^<(\w+)(\s[^>]*)?>")

# Bug C: whole-document find() treats text duplicated inside <script>/<style>
# (e.g. Next.js App Router's __next_f hydration payload) as ambiguous, so the
# diff never applies to the visible body. Compute occurrence/ambiguity against
# a masked copy where script/style *contents* (not the tags) are blanked to
# same-length \x00 runs, then splice the real html at the same index.
_SCRIPT_STYLE_RE = re.compile(r"(<(script|style)\b[^>]*>)([\s\S]*?)(</\2>)", re.IGNORECASE)


def _mask_script_style(html: str) -> str:
    def _repl(m: "re.Match[str]") -> str:
        open_tag, body, close_tag = m.group(1), m.group(3), m.group(4)
        return open_tag + "\x00" * len(body) + close_tag

    return _SCRIPT_STYLE_RE.sub(_repl, html)


def apply_content_diffs(html: str, diffs: List[Dict[str, Any]], manifest: Manifest) -> str:
    if not isinstance(diffs, list):
        return html

    for d in diffs:
        try:
            original = d.get("original_text") or ""
            replacement = d.get("replacement_html") or ""
            if not original or not replacement:
                continue

            masked = _mask_script_style(html)
            if replacement in masked and original not in masked:
                continue  # already applied

            idx = masked.find(original)
            if idx == -1:
                continue  # not in the visible region → skip (DOM drift, or only in script/style)
            if masked.find(original, idx + len(original)) != -1:
                continue  # ambiguous in the visible region → skip

            diff_id = d.get("id")
            if diff_id is not None:
                root_match = _SINGLE_ROOT_RE.match(replacement)
                if root_match:
                    marker_str = f'data-seojuice-cs="{diff_id}"'
                    if marker_str not in replacement:
                        open_tag = root_match.group(0)
                        marked_open_tag = open_tag[:-1] + f" {marker_str}>"
                        replacement = marked_open_tag + replacement[len(open_tag) :]
                    if f'data-seojuice-cs="{diff_id}"' not in html:
                        manifest.cs.append(diff_id)

            html = html[:idx] + replacement + html[idx + len(original) :]
        except Exception:
            pass  # one bad diff never aborts the page

    return html


def apply_broken_link_fixes(html: str, fixes: List[Dict[str, Any]]) -> str:
    if not isinstance(fixes, list) or not fixes:
        return html

    for fix in fixes:
        try:
            tag = (fix.get("tag") or "").lower()
            attr = (fix.get("attr") or "").lower()
            old_url = fix.get("broken_url") or fix.get("old_url") or ""
            new_url = fix.get("new_url") or fix.get("replacement_url") or ""
            action = "unlink" if fix.get("action") == "unlink" else "replace"

            if not tag or not attr or not old_url:
                continue
            if action == "replace" and not new_url:
                continue
            if tag not in ("a", "img"):
                continue
            if attr not in ("href", "src"):
                continue

            escaped_old_url = re.escape(old_url)

            if action == "replace":
                pattern = re.compile(
                    rf"(<{tag}\b[^>]*\s{attr}=)([\"'])({escaped_old_url})\2([^>]*>)", re.IGNORECASE
                )

                def _repl(m: "re.Match[str]", new_url: str = new_url) -> str:
                    before, quote, _old, after = m.group(1), m.group(2), m.group(3), m.group(4)
                    return f"{before}{quote}{escape_html(new_url)}{quote}{after}"

                html = pattern.sub(_repl, html)
            else:
                if tag == "img":
                    pattern = re.compile(
                        rf"<img\b[^>]*\s{attr}=[\"']{escaped_old_url}[\"'][^>]*>", re.IGNORECASE
                    )
                else:
                    pattern = re.compile(
                        rf"<a\b[^>]*\s{attr}=[\"']{escaped_old_url}[\"'][^>]*>[\s\S]*?</a>", re.IGNORECASE
                    )
                html = pattern.sub("", html)
        except Exception:
            pass  # one bad fix never aborts the page

    return html


def validate_api_response(data: object) -> bool:
    """Port of WP seojuice.php:429-468 (C1).

    Extends the WP checklist with ``broken_link_fixes``: the Worker-generated
    golden vectors include payloads whose only actionable field is
    broken_link_fixes (title/meta_description/suggestions/images/structured_data/
    og_title/diffs all empty), and the Worker still applies those fixes. Treating
    broken_link_fixes as non-actionable would make apply_suggestions a no-op for
    that shape of payload, contradicting the canonical Worker behavior.
    """
    if not isinstance(data, dict):
        return False
    if data.get("errors"):
        return False
    has_content = bool(
        data.get("title")
        or data.get("meta_description")
        or data.get("suggestions")
        or data.get("images")
        or data.get("structured_data")
        or data.get("og_title")
        or data.get("og_description")
        or data.get("og_image")
        or data.get("og_url")
        or data.get("meta_keywords")
        or data.get("h1")
        or (isinstance(data.get("diffs"), list) and data.get("diffs"))
        or (isinstance(data.get("broken_link_fixes"), list) and data.get("broken_link_fixes"))
    )
    if not has_content:
        return False
    for key in ("suggestions", "images", "diffs", "broken_link_fixes"):
        if key in data and not isinstance(data[key], list):
            return False
    return True


_BODY_CLOSE_RE = re.compile(r"</body>", re.IGNORECASE)


def add_manifest_comment(html: str, manifest: Manifest) -> str:
    if "<!-- seojuice:" in html:
        return html  # idempotent

    parts: List[str] = []

    if manifest.cs:
        parts.append(f"cs=[{','.join(str(i) for i in manifest.cs)}]")

    if manifest.meta:
        parts.append(f"meta=[{','.join(manifest.meta)}]")

    if manifest.img > 0:
        parts.append(f"img={manifest.img}")

    if manifest.schema:
        parts.append("schema=1")

    if manifest.h1:
        parts.append("h1=1")

    if not parts:
        return html

    comment = f"<!-- seojuice: {' '.join(parts)} -->"
    return _BODY_CLOSE_RE.sub(f"{comment}\n</body>", html, count=1)


def add_ssr_flag(html: str) -> str:
    script = "<script>window.seojuiceSSR = true;</script>"
    if "window.seojuiceSSR" in html:
        return html
    return _BODY_CLOSE_RE.sub(f"{script}\n</body>", html, count=1)
