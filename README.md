<div align="center">

<!-- Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,50:16213e,100:0f3460&height=180&section=header&text=Starvell%20Cardinal&fontSize=42&fontColor=e94560&animation=fadeIn&fontAlignY=32&desc=Telegram-бот%20для%20автоматизации%20Starvell&descAlignY=55&descSize=16&descAlign=50" width="100%" />

<br/>

[![Version](https://img.shields.io/badge/version-0.3.0-e94560?style=for-the-badge&logo=semantic-release&logoColor=white)](version.py)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/starvellingbot)
[![Starvell](https://img.shields.io/badge/Starvell-Automation-0f3460?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTEyIDJMMTUuMDkgOC4yNkwyMiAxMi4wOUwxNS4wOSAxNS43NEwxMiAyMkwxMiAxMi4wOUw1IDEyLjA5TDEyIDJaIi8+PC9zdmc+)](https://starvell.com)
[![License](https://img.shields.io/badge/License-MIT-16213e?style=for-the-badge)](LICENSE)

<p>
  <a href="https://t.me/starvellingbot"><b>📢 Канал</b></a> •
  <a href="https://t.me/knowtake"><b>👤 Автор</b></a> •
  <a href="https://github.com/etheriumflipper/StarvellCardinal"><b>💻 GitHub</b></a>
</p>

---

**Starvell Cardinal** — Telegram-бот для продавцов на [Starvell.com](https://starvell.com).  
Автоподнятие лотов · автоответы · авто-выдача · вечный онлайн · плагины · автообновления.

<br/>

```ascii
   ★  S T A R V E L L   C A R D I N A L  ★
        автоматизация · плагины · онлайн
```

</div>

---

## ⚡ Установка одной командой

```bash
wget https://raw.githubusercontent.com/etheriumflipper/StarvellCardinal/main/install.sh -O install.sh && bash install.sh
```

## 🚀 Быстрый старт

<table>
<tr>
<td width="50%">

### 🐧 Linux / VPS

```bash
git clone https://github.com/etheriumflipper/StarvellCardinal.git
cd StarvellCardinal
sudo bash install.sh
```

```bash
sudo systemctl status starvell-cardinal
sudo journalctl -u starvell-cardinal -f
```

</td>
<td width="50%">

### 🪟 Windows

```bat
git clone https://github.com/etheriumflipper/StarvellCardinal.git
cd StarvellCardinal
Setup.bat
Start.bat
```

</td>
</tr>
</table>

## 🧠 Возможности

| Функция | Описание |
|---------|----------|
| 📦 **Авто-поднятие** | Bump лотов по всем категориям автоматически |
| 💬 **Автоответы** | Ответы на сообщения покупателей |
| 🎁 **Авто-выдача** | Выдача товаров по шаблонам |
| 🟢 **Вечный онлайн** | HTTP heartbeat + Socket.IO (если доступен) |
| 🧩 **Плагины** | Расширяемая система модулей |
| 🔄 **Автообновления** | Уведомления и `/update` из GitHub |

## 🛡️ Антибот Starvell (v0.3.0)

Starvell усилил защиту (QRATOR). Cardinal адаптирован:

- ✅ Запросы профиля через **Next.js Data API** вместо HTML `/users/` (фикс 403)
- ✅ **Browser-like headers** + rate limiter для всех запросов
- ✅ **HTTP heartbeat** как основной метод онлайна (Socket.IO может быть 404)
- ✅ Умная обработка **Telegram flood control** при смене имени бота

## 🧷 Первый запуск

1. `Bot Token` от `@BotFather`
2. Пароль для доступа к боту
3. `session_cookie` от Starvell.com

Мастер создаст `configs/_main.cfg` и запустит сервис.

## 🗂️ Структура

```text
StarvellCardinal/
├── main.py              # Точка входа
├── api/                 # Starvell API клиент
├── bot/                 # Telegram-бот
├── configs/             # Конфигурация
├── docs/                # Документация
└── plugins/             # Плагины (пусто в чистой версии)
```

## 🔄 Автообновления

При выходе новой версии админы получают уведомление с кнопкой **«Обновить сейчас»** или командой `/update`.

> Перед релизом повышайте `VERSION` в [version.py](version.py).

## 🔗 Ссылки

| | |
|---|---|
| 👤 Автор | [@knowtake](https://t.me/knowtake) |
| 📢 Канал | [@starvellingbot](https://t.me/starvellingbot) |
| 💻 GitHub | [etheriumflipper/StarvellCardinal](https://github.com/etheriumflipper/StarvellCardinal) |
| 🌍 Starvell | [starvell.com](https://starvell.com) |

## 📄 Лицензия

[MIT](LICENSE) © [@knowtake](https://t.me/knowtake)

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,50:16213e,100:0f3460&height=100&section=footer&fontSize=14&fontColor=e94560&text=Made%20with%20%E2%9D%A4%20by%20@knowtake" width="100%" />
</div>
