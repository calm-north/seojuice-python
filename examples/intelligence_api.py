"""
Intelligence API — full workflow examples.

Demonstrates the domain-scoped client for SEO analytics:
overview, content gaps, decay alerts, related pages, PageSpeed, and accessibility.

Requirements:
    pip install seojuice
"""
from __future__ import annotations

import os

from seojuice import SEOJuice, auto_paginate


def get_seo_overview(domain: str) -> None:
    """Fetch intelligence summary and AISO score for a domain."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        intel = site.intelligence(period="30d", include_trends=True)
        print(f"Domain: {domain}")
        print(f"  SEO Score : {intel['seo_score']}")
        print(f"  Pages     : {intel['total_pages']}")
        if "trends" in intel:
            print(f"  Trends    : {intel['trends']}")

        aiso = site.aiso()
        print(f"  AISO Score: {aiso['aiso_score']}")


def find_content_gaps(domain: str) -> None:
    """List informational content gaps using auto-pagination."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        print(f"\nContent gaps for {domain}:")
        for gap in auto_paginate(site.content_gaps, intent="informational"):
            print(f"  {gap['page_name']} — potential: {gap['seo_potential']}")


def find_decaying_content(domain: str) -> None:
    """Find active, high-severity content decay alerts."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        decay = site.content_decay(is_active=True, severity="high")
        print(f"\nHigh-severity decay alerts for {domain}:")
        for alert in decay:
            print(f"  {alert['page_url']} — type: {alert['decay_type']}")


def get_related_posts(domain: str, url: str) -> None:
    """Retrieve the 5 most similar pages to a given URL."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        result = site.similar_pages(url, limit=5)
        print(f"\nPages similar to {url}:")
        for page in result["similar_pages"]:
            print(f"  {page['url']} — score: {page.get('similarity_score', 'N/A')}")


def check_pagespeed(domain: str, url: str) -> None:
    """Run a PageSpeed check on a single URL."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        result = site.pagespeed(url)
        print(f"\nPageSpeed for {url}:")
        print(f"  Performance: {result.get('scores', {}).get('performance')}")
        print(f"  LCP        : {result.get('core_web_vitals', {}).get('lcp')}")
        print(f"  CLS        : {result.get('core_web_vitals', {}).get('cls')}")


def check_accessibility(domain: str) -> None:
    """List critical accessibility issues for a domain."""
    with SEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        issues = site.accessibility_issues(severity="critical")
        print(f"\nCritical accessibility issues for {domain}:")
        for issue in issues:
            print(f"  [{issue.get('category')}] {issue.get('description')}")


def main() -> None:
    domain = "example.com"
    url = f"https://{domain}/blog/seo-guide"

    get_seo_overview(domain)
    find_content_gaps(domain)
    find_decaying_content(domain)
    get_related_posts(domain, url)
    check_pagespeed(domain, url)
    check_accessibility(domain)


if __name__ == "__main__":
    main()
