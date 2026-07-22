"""
Совместимость с Python 3.8.

Патчит отсутствующие API (например asyncio.to_thread из 3.9+),
чтобы автообнова и остальной код не падали на 3.8.
Импортировать как можно раньше (из main.py).
"""

from __future__ import annotations

import asyncio
import functools
import sys
from typing import Any, Callable


MIN_PYTHON = (3, 8)


def ensure_python_supported() -> None:
    if sys.version_info < MIN_PYTHON:
        major, minor = MIN_PYTHON
        raise SystemExit(
            f"Нужен Python {major}.{minor}+, сейчас "
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )


def _to_thread(func: Callable[..., Any], *args: Any, **kwargs: Any):
    """Аналог asyncio.to_thread для Python < 3.9."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


def patch_asyncio() -> None:
    """Добавить asyncio.to_thread, если его нет (Python 3.8)."""
    if not hasattr(asyncio, "to_thread"):
        # type: ignore[attr-defined]
        asyncio.to_thread = _to_thread  # noqa: B018


def apply() -> None:
    """Применить все патчи совместимости."""
    ensure_python_supported()
    patch_asyncio()


# Автопатч при импорте модуля
apply()
