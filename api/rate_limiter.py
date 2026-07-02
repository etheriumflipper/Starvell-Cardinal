"""Ограничение частоты запросов к Starvell API."""

import asyncio
import os
import time


def _effective_rpm(default: int = 40) -> int:
    raw = os.getenv("STARVELL_MAX_PER_MINUTE", "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value <= 0:
        return default
    return min(value, 40)


STARVELL_MAX_PER_MINUTE = _effective_rpm(40)
MIN_INTERVAL_SECONDS = 60.0 / float(STARVELL_MAX_PER_MINUTE)


class _AsyncMinIntervalLimiter:
    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = float(min_interval_seconds)
        self._lock = asyncio.Lock()
        self._next_allowed = 0.0

    async def wait(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            async with self._lock:
                now = loop.time()
                if self._next_allowed <= 0.0:
                    self._next_allowed = now
                delay = self._next_allowed - now
                if delay > 0:
                    await asyncio.sleep(delay)
                    now = loop.time()
                self._next_allowed = now + self._min_interval
        except asyncio.CancelledError:
            raise


_limiter = _AsyncMinIntervalLimiter(MIN_INTERVAL_SECONDS)


async def throttle() -> None:
    await _limiter.wait()
