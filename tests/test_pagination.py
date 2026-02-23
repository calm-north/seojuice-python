from __future__ import annotations

from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from seojuice._pagination import PagedResult, async_auto_paginate, auto_paginate
from seojuice._types import PaginationMeta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pagination(
    page: int = 1,
    page_size: int = 10,
    total_count: int = 10,
    total_pages: int = 1,
) -> PaginationMeta:
    return {
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# PagedResult
# ---------------------------------------------------------------------------


class TestPagedResult:
    def test_stores_results(self):
        items = [{"id": 1}, {"id": 2}]
        pr = PagedResult(results=items, pagination=_pagination())
        assert pr.results == items

    def test_stores_pagination(self):
        pag = _pagination(page=2, total_pages=5)
        pr = PagedResult(results=[], pagination=pag)
        assert pr.pagination == pag

    def test_has_next_true_when_not_on_last_page(self):
        pr = PagedResult(results=[], pagination=_pagination(page=1, total_pages=3))
        assert pr.has_next is True

    def test_has_next_false_on_last_page(self):
        pr = PagedResult(results=[], pagination=_pagination(page=3, total_pages=3))
        assert pr.has_next is False

    def test_has_next_false_when_single_page(self):
        pr = PagedResult(results=[{"id": 1}], pagination=_pagination(page=1, total_pages=1))
        assert pr.has_next is False

    def test_total_count(self):
        pr = PagedResult(results=[], pagination=_pagination(total_count=42))
        assert pr.total_count == 42

    def test_iter_yields_results(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        pr = PagedResult(results=items, pagination=_pagination())
        assert list(pr) == items

    def test_len_returns_result_count(self):
        pr = PagedResult(results=[{"id": 1}, {"id": 2}], pagination=_pagination())
        assert len(pr) == 2

    def test_len_empty(self):
        pr = PagedResult(results=[], pagination=_pagination())
        assert len(pr) == 0

    def test_repr_shows_items_and_page_info(self):
        pr = PagedResult(
            results=[{"id": 1}, {"id": 2}],
            pagination=_pagination(page=2, total_pages=5),
        )
        assert repr(pr) == "PagedResult(items=2, page=2/5)"

    def test_repr_first_page(self):
        pr = PagedResult(
            results=[{"a": 1}],
            pagination=_pagination(page=1, total_pages=1),
        )
        assert repr(pr) == "PagedResult(items=1, page=1/1)"


# ---------------------------------------------------------------------------
# auto_paginate (sync generator)
# ---------------------------------------------------------------------------


class TestAutoPaginate:
    def test_yields_all_items_across_pages(self):
        call_count = 0

        def fetch_page(page: int = 1, page_size: int = 2, **kwargs: Any) -> PagedResult:
            nonlocal call_count
            call_count += 1
            if page == 1:
                return PagedResult(
                    results=[{"id": 1}, {"id": 2}],
                    pagination=_pagination(page=1, page_size=2, total_count=5, total_pages=3),
                )
            elif page == 2:
                return PagedResult(
                    results=[{"id": 3}, {"id": 4}],
                    pagination=_pagination(page=2, page_size=2, total_count=5, total_pages=3),
                )
            else:
                return PagedResult(
                    results=[{"id": 5}],
                    pagination=_pagination(page=3, page_size=2, total_count=5, total_pages=3),
                )

        items = list(auto_paginate(fetch_page, page_size=2))

        assert items == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
        assert call_count == 3

    def test_stops_after_last_page(self):
        call_count = 0

        def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            nonlocal call_count
            call_count += 1
            return PagedResult(
                results=[{"id": 1}],
                pagination=_pagination(page=1, page_size=10, total_count=1, total_pages=1),
            )

        items = list(auto_paginate(fetch_page))

        assert items == [{"id": 1}]
        assert call_count == 1

    def test_yields_nothing_for_empty_results(self):
        def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            return PagedResult(
                results=[],
                pagination=_pagination(page=1, page_size=10, total_count=0, total_pages=1),
            )

        items = list(auto_paginate(fetch_page))
        assert items == []

    def test_passes_kwargs_to_fetch_function(self):
        received_kwargs: dict = {}

        def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            received_kwargs.update(kwargs)
            return PagedResult(
                results=[],
                pagination=_pagination(page=1, total_pages=1),
            )

        list(auto_paginate(fetch_page, page_size=5, category="seo"))
        assert received_kwargs["category"] == "seo"

    def test_default_page_size_is_100(self):
        received_page_sizes: List[int] = []

        def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            received_page_sizes.append(page_size)
            return PagedResult(
                results=[],
                pagination=_pagination(page=1, total_pages=1),
            )

        list(auto_paginate(fetch_page))
        assert received_page_sizes == [100]


# ---------------------------------------------------------------------------
# async_auto_paginate
# ---------------------------------------------------------------------------


class TestAsyncAutoPaginate:
    async def test_yields_all_items_across_pages(self):
        call_count = 0

        async def fetch_page(page: int = 1, page_size: int = 2, **kwargs: Any) -> PagedResult:
            nonlocal call_count
            call_count += 1
            if page == 1:
                return PagedResult(
                    results=[{"id": 1}, {"id": 2}],
                    pagination=_pagination(page=1, page_size=2, total_count=4, total_pages=2),
                )
            else:
                return PagedResult(
                    results=[{"id": 3}, {"id": 4}],
                    pagination=_pagination(page=2, page_size=2, total_count=4, total_pages=2),
                )

        items = []
        async for item in async_auto_paginate(fetch_page, page_size=2):
            items.append(item)

        assert items == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        assert call_count == 2

    async def test_stops_after_single_page(self):
        call_count = 0

        async def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            nonlocal call_count
            call_count += 1
            return PagedResult(
                results=[{"id": 1}],
                pagination=_pagination(page=1, total_pages=1),
            )

        items = []
        async for item in async_auto_paginate(fetch_page):
            items.append(item)

        assert items == [{"id": 1}]
        assert call_count == 1

    async def test_yields_nothing_for_empty_results(self):
        async def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            return PagedResult(
                results=[],
                pagination=_pagination(page=1, total_pages=1),
            )

        items = []
        async for item in async_auto_paginate(fetch_page):
            items.append(item)

        assert items == []

    async def test_passes_kwargs_to_async_fetch_function(self):
        received_kwargs: dict = {}

        async def fetch_page(page: int = 1, page_size: int = 10, **kwargs: Any) -> PagedResult:
            received_kwargs.update(kwargs)
            return PagedResult(
                results=[],
                pagination=_pagination(page=1, total_pages=1),
            )

        async for _ in async_auto_paginate(fetch_page, page_size=50, status="active"):
            pass

        assert received_kwargs["status"] == "active"
