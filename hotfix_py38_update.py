#!/usr/bin/env python3
"""
Одноразовый hotfix для ботов, застрявших на Python 3.8
с ошибкой: module 'asyncio' has no attribute 'to_thread'

Запуск из папки бота:
    python hotfix_py38_update.py
"""
from __future__ import print_function

import os
import sys
import subprocess

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen  # type: ignore

REPO = "etheriumflipper/Starvell-Cardinal"
# Коммит/тег с фиксом (не /main — у raw CDN бывает кэш)
REF = "v0.3.17"
BASE = "https://raw.githubusercontent.com/{}/{}/".format(REPO, REF)

FILES = (
    "bot/features/auto_update.py",
    "version.py",
)


def download(rel_path):
    url = BASE + rel_path
    print("↓", url)
    resp = urlopen(url, timeout=30)
    data = resp.read()
    dest = os.path.join(os.getcwd(), rel_path.replace("/", os.sep))
    folder = os.path.dirname(dest)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(dest, "wb") as fh:
        fh.write(data)
    print("✓", rel_path, "({} bytes)".format(len(data)))


def try_git_pull():
    if not os.path.isdir(".git"):
        print("! .git нет — пропускаю git pull (файлы уже скачаны)")
        return
    cmds = [
        ["git", "remote", "set-url", "origin", "https://github.com/{}.git".format(REPO)],
        ["git", "fetch", "origin", "main", "--tags"],
        ["git", "checkout", REF, "--", "bot/features/auto_update.py", "version.py"],
    ]
    for cmd in cmds:
        print("$", " ".join(cmd))
        try:
            subprocess.check_call(cmd)
        except Exception as exc:
            print("! git шаг пропущен:", exc)
            return
    print("✓ git checkout файлов с", REF)


def main():
    if not os.path.isfile("main.py"):
        print("ОШИБКА: запусти из папки Starvell Cardinal (где main.py)")
        sys.exit(1)

    print("=== Hotfix Python 3.8 / asyncio.to_thread ===")
    try_git_pull()
    for rel in FILES:
        download(rel)

    print()
    print("Готово. Перезапусти бота:")
    print("  systemctl restart starvell-cardinal")
    print("  # или твой обычный способ restart / Start.bat")
    print("После рестарта автообнова дотянет остальное до", "0.3.17+")


if __name__ == "__main__":
    main()
