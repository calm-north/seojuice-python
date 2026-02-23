"""
Async workflow patterns with AsyncSEOJuice.

Demonstrates concurrent data fetching, async auto-pagination,
and batch processing of multiple domains.

Requirements:
    pip install seojuice
"""
from __future__ import annotations

import asyncio
import os

from seojuice import AsyncSEOJuice
from seojuice._pagination import async_auto_paginate


async def concurrent_fetch(domain: str) -> None:
    """Fetch intelligence, content gaps, and decay alerts concurrently."""
    async with AsyncSEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        intel, gaps, decay = await asyncio.gather(
            site.intelligence(period="30d", include_trends=True),
            site.content_gaps(),
            site.content_decay(is_active=True, severity="high"),
        )

    print(f"[{domain}] SEO Score: {intel.get('seo_score')}")
    print(f"[{domain}] Content gaps: {len(list(gaps))}")
    print(f"[{domain}] Decay alerts: {len(list(decay))}")


async def paginate_all_pages(domain: str) -> None:
    """Iterate through every page on a domain using async auto-pagination."""
    async with AsyncSEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:
        site = client.website(domain)

        count = 0
        async for page in async_auto_paginate(site.pages, page_size=100):
            count += 1
            print(f"  {page['url']} — score: {page.get('seo_score', 'N/A')}")

        print(f"[{domain}] Total pages: {count}")


async def batch_process_domains(domains: list[str]) -> None:
    """Process multiple domains concurrently with a shared client."""
    async with AsyncSEOJuice(os.environ["SEOJUICE_API_KEY"]) as client:

        async def _process(domain: str) -> dict:
            site = client.website(domain)
            intel = await site.intelligence(period="30d")
            aiso = await site.aiso()
            return {
                "domain": domain,
                "seo_score": intel.get("seo_score"),
                "aiso_score": aiso.get("aiso_score"),
            }

        results = await asyncio.gather(*[_process(d) for d in domains])

    for result in results:
        print(f"{result['domain']}: SEO={result['seo_score']}, AISO={result['aiso_score']}")


async def main() -> None:
    domain = "example.com"

    print("--- Concurrent fetch ---")
    await concurrent_fetch(domain)

    print("\n--- Async pagination ---")
    await paginate_all_pages(domain)

    print("\n--- Batch processing ---")
    await batch_process_domains(["example.com", "blog.example.com", "shop.example.com"])


if __name__ == "__main__":
    asyncio.run(main())
