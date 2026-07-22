#!/usr/bin/env python3
"""
Статическая проверка: запрещённые API новее Python 3.8.

Запуск:
    python scripts/check_py38_compat.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Только реальные вызовы/импорты, не строки в этом же чекере
FORBIDDEN = [
    (
        re.compile(r"(?<![\"'])\basyncio\.timeout\s*\("),
        "asyncio.timeout() есть только в Python 3.11+",
    ),
    (
        re.compile(r"(?<![\"'])\basyncio\.TaskGroup\b"),
        "asyncio.TaskGroup есть только в Python 3.11+",
    ),
    (
        re.compile(r"(?<![.\w])ExceptionGroup\b"),
        "ExceptionGroup есть только в Python 3.11+",
    ),
    (
        re.compile(r"^\s*(?:from\s+zoneinfo\b|import\s+zoneinfo\b)", re.M),
        "zoneinfo есть только в Python 3.9+ (без backports)",
    ),
    (
        re.compile(r"^\s*(?:from\s+tomllib\b|import\s+tomllib\b)", re.M),
        "tomllib есть только в Python 3.11+",
    ),
]

# Реальный вызов, не комментарий и не упоминание в строке чекера/hotfix
TO_THREAD_CALL_RE = re.compile(r"(?<![\"'#])\basyncio\.to_thread\s*\(")

SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "storage",
    "logs",
    "configs",
    "plugins",
    "node_modules",
    "scripts",  # сам чекер
}

SKIP_FILES = {
    "hotfix_py38_update.py",
    "py38_compat.py",
}


def iter_py_files():
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        yield path


def line_is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"{path}: не прочитать ({exc})"]

    rel = path.relative_to(ROOT).as_posix()
    lines = text.splitlines()

    for regex, reason in FORBIDDEN:
        for match in regex.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            if line_is_comment(lines[line_no - 1]):
                continue
            errors.append(f"{rel}:{line_no}: {reason}")

    for match in TO_THREAD_CALL_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        if line_is_comment(lines[line_no - 1]):
            continue
        errors.append(
            f"{rel}:{line_no}: asyncio.to_thread() запрещён — "
            "на Python 3.8 этого API нет. Используй sync-вызов "
            "или полагайся на bot.core.py38_compat (импорт в main.py)."
        )

    return errors


def main() -> int:
    main_py = ROOT / "main.py"
    main_text = main_py.read_text(encoding="utf-8") if main_py.exists() else ""
    if "py38_compat" not in main_text:
        print("FAIL: main.py должен импортировать bot.core.py38_compat в начале")
        return 1

    init_py = ROOT / "bot" / "core" / "__init__.py"
    init_text = init_py.read_text(encoding="utf-8") if init_py.exists() else ""
    if "py38_compat" not in init_text:
        print("FAIL: bot/core/__init__.py должен импортировать py38_compat первым")
        return 1

    all_errors: list[str] = []
    for path in iter_py_files():
        all_errors.extend(check_file(path))

    if all_errors:
        print("Python 3.8 compatibility check FAILED:\n")
        for err in all_errors:
            print(" -", err)
        print(f"\n{len(all_errors)} problem(s)")
        return 1

    print("OK: Python 3.8 compatibility check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
