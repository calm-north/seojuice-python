"""
Django integration patterns for SEOJuice.

Shows function-based views, a class-based mixin, and middleware configuration
for injecting SEO data into Django templates.

Requirements:
    pip install seojuice[django]

Middleware setup — add to settings.py:
    MIDDLEWARE = [
        ...
        "seojuice.injection.django.SEOJuiceDjangoMiddleware",
    ]
    SEOJUICE_INJECTION_ENABLED = True
    SEOJUICE_INJECTION_TIMEOUT = 5.0

Template usage:
    {{ seo.meta_description }}
    {{ seo.seo_score }}
    {% for gap in seo.content_gaps %}
        <li>{{ gap.page_name }} — {{ gap.seo_potential }}</li>
    {% endfor %}
"""
from __future__ import annotations

import os
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from seojuice import SEOJuice


SEOJUICE_API_KEY = os.environ["SEOJUICE_API_KEY"]


def seo_dashboard_view(request: HttpRequest) -> HttpResponse:
    """Function-based view that passes SEO intelligence to a template."""
    domain = request.GET.get("domain", "example.com")

    with SEOJuice(SEOJUICE_API_KEY) as client:
        site = client.website(domain)
        intel = site.intelligence(period="30d", include_trends=True)
        gaps = site.content_gaps(intent="informational")
        aiso = site.aiso()

    return render(request, "seo/dashboard.html", {
        "domain": domain,
        "seo": {
            "intelligence": intel,
            "content_gaps": list(gaps),
            "aiso": aiso,
            "meta_description": intel.get("meta_description", ""),
            "seo_score": intel.get("seo_score", 0),
        },
    })


class SEODataMixin:
    """Mixin that injects SEO data into any TemplateView's context.

    Usage:
        class MyPageView(SEODataMixin, TemplateView):
            template_name = "my_page.html"
            seo_domain = "example.com"
    """

    seo_domain: str = ""

    def get_seo_domain(self) -> str:
        return self.seo_domain

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)  # type: ignore[misc]
        domain = self.get_seo_domain()
        if not domain:
            return context

        with SEOJuice(SEOJUICE_API_KEY) as client:
            site = client.website(domain)
            context["seo"] = {
                "intelligence": site.intelligence(period="30d"),
                "aiso": site.aiso(),
            }
        return context


class SEODashboardView(SEODataMixin, TemplateView):
    """Example class-based view using the SEO mixin."""

    template_name = "seo/dashboard.html"
    seo_domain = "example.com"
