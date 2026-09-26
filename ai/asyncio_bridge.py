"""Run a coroutine from synchronous test code.

Playwright's sync API keeps an event loop running on the main thread, so
``asyncio.run`` there raises "cannot be called from a running event loop".
Running the coroutine on a short-lived worker thread (with its own loop)
works in every context: pytest, Playwright tests, notebooks.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

T = TypeVar("T")


def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run ``coro`` to completion on a worker thread and return its result (exceptions propagate)."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()
