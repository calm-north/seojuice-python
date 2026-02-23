from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    List,
    TypeVar,
)

from seojuice._types import PaginationMeta

T = TypeVar("T")


class PagedResult(Generic[T]):
    """Wrapper around a paginated API response."""

    def __init__(self, results: List[T], pagination: PaginationMeta) -> None:
        self.results = results
        self.pagination = pagination

    @property
    def has_next(self) -> bool:
        return self.pagination["page"] < self.pagination["total_pages"]

    @property
    def total_count(self) -> int:
        return self.pagination["total_count"]

    def __iter__(self) -> Iterator[T]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __repr__(self) -> str:
        page = self.pagination["page"]
        total = self.pagination["total_pages"]
        count = len(self.results)
        return f"PagedResult(items={count}, page={page}/{total})"


def auto_paginate(
    fetch_page: Callable[..., PagedResult[T]],
    page_size: int = 100,
    **kwargs: Any,
) -> Iterator[T]:
    """Sync generator that yields individual items across all pages."""
    page = 1
    while True:
        result = fetch_page(page=page, page_size=page_size, **kwargs)
        yield from result.results
        if not result.has_next:
            break
        page += 1


async def async_auto_paginate(
    fetch_page: Callable[..., Awaitable[PagedResult[T]]],
    page_size: int = 100,
    **kwargs: Any,
) -> AsyncIterator[T]:
    """Async generator that yields individual items across all pages."""
    page = 1
    while True:
        result = await fetch_page(page=page, page_size=page_size, **kwargs)
        for item in result.results:
            yield item
        if not result.has_next:
            break
        page += 1
