"""
CMS integration patterns for SEOJuice.

Covers three Python CMS platforms:
1. Wagtail — page mixin with a before_serve hook
2. Django CMS — plugin that fetches intelligence data
3. Headless CMS (WordPress REST API) — enrich WP posts with SEO data

Requirements (pick one):
    pip install seojuice wagtail
    pip install seojuice django-cms
    pip install seojuice requests   # for headless WordPress
"""
from __future__ import annotations

import os
from typing import Any

# ---------------------------------------------------------------------------
# 1. Wagtail: SEOPage mixin with automatic suggestion injection
# ---------------------------------------------------------------------------
# Uncomment to use with Wagtail:
#
# from wagtail.api import APIField
# from wagtail.models import Page
#
# from seojuice import SEOJuice
# from seojuice.injection._fetcher import fetch_suggestions_sync
#
#
# class SEOPageMixin:
#     """Mixin for Wagtail pages that injects SEO suggestions on serve."""
#
#     api_fields = [
#         APIField("seo_suggestions"),
#     ]
#
#     seo_suggestions: dict[str, Any] = {}
#
#     def serve(self, request, *args, **kwargs):
#         url = request.build_absolute_uri()
#         self.seo_suggestions = fetch_suggestions_sync(url, timeout=3.0) or {}
#         return super().serve(request, *args, **kwargs)
#
#
# class BlogPage(SEOPageMixin, Page):
#     """Example Wagtail page using the SEO mixin."""
#
#     template = "blog/blog_page.html"
#
#     def get_context(self, request, *args, **kwargs):
#         context = super().get_context(request, *args, **kwargs)
#         context["seo"] = self.seo_suggestions
#         return context


# ---------------------------------------------------------------------------
# 2. Django CMS: plugin that renders SEO intelligence data
# ---------------------------------------------------------------------------
# Uncomment to use with Django CMS:
#
# from cms.plugin_base import CMSPluginBase
# from cms.plugin_pool import plugin_pool
# from django.utils.translation import gettext_lazy as _
#
# from seojuice import SEOJuice
#
#
# @plugin_pool.register_plugin
# class SEOPlugin(CMSPluginBase):
#     """CMS plugin that displays SEO intelligence for the current site."""
#
#     name = _("SEO Intelligence")
#     render_template = "cms_plugins/seo_intelligence.html"
#     cache = True
#     module = _("SEO")
#
#     def render(self, context, instance, placeholder):
#         request = context["request"]
#         domain = request.get_host()
#
#         with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
#             site = client.website(domain)
#             context["seo_intel"] = site.intelligence(period="30d")
#             context["seo_aiso"] = site.aiso()
#
#         return context


# ---------------------------------------------------------------------------
# 3. Headless CMS: enrich WordPress REST API posts with SEO data
# ---------------------------------------------------------------------------
import requests

from seojuice import SEOJuice


def fetch_wp_posts(wp_base_url: str, per_page: int = 10) -> list[dict[str, Any]]:
    """Fetch recent posts from the WordPress REST API."""
    resp = requests.get(
        f"{wp_base_url}/wp-json/wp/v2/posts",
        params={"per_page": per_page, "_embed": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def enrich_posts_with_seo(
    domain: str,
    posts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add SEO data (similar pages, PageSpeed) to each WordPress post."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        for post in posts:
            url = post.get("link", "")
            if not url:
                continue

            result = site.similar_pages(url, limit=3)
            post["seo_similar_pages"] = result["similar_pages"]

            speed = site.pagespeed(url)
            post["seo_pagespeed"] = speed

    return posts


def main() -> None:
    wp_url = "https://blog.example.com"
    domain = "blog.example.com"

    posts = fetch_wp_posts(wp_url, per_page=5)
    enriched = enrich_posts_with_seo(domain, posts)

    for post in enriched:
        title = post.get("title", {}).get("rendered", "Untitled")
        score = post.get("seo_pagespeed", {}).get("scores", {}).get("performance")
        similar_count = len(post.get("seo_similar_pages", []))
        print(f"{title}: PageSpeed={score}, similar={similar_count}")


if __name__ == "__main__":
    main()
