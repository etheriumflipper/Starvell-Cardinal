"""
Автодемпер цен для Starvell Cardinal
Автоматически понижает цены при демпинге конкурентов

ВАЖНО: Этот плагин требует доработки API методов в StarvellService:
- get_my_lots() - получить свои лоты
- get_competitors(game_id, category_id) - получить конкурентов
- update_lot_price(lot_id, new_price) - обновить цену лота

Пока эти методы не реализованы, плагин работать не будет.
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
import json

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# === МЕТАДАННЫЕ ===
NAME = "AutoDumper"
VERSION = "1.0.0"
DESCRIPTION = "Автоматически понижает цены при демпинге конкурентов"
AUTHOR = "@embedium"
UUID = "auto-dumper-starvell-001"

# === ПУТИ К ФАЙЛАМ ===
STORAGE_DIR = Path(f"storage/plugins/{UUID}")
SETTINGS_FILE = STORAGE_DIR / "settings.json"
LOG_FILE = Path("logs") / "auto_dumper.log"

# === НАСТРОЙКИ ПО УМОЛЧАНИЮ ===
DEFAULT_SETTINGS = {
    "enabled": False,
    "check_interval": 300,  # Проверка каждые 5 минут (в секундах)
    "min_competitor_reviews": 10,  # Минимум отзывов у конкурента для реакции
    "price_decrease_percent": 2,  # На сколько % снижать цену
    "price_decrease_fixed": 0,  # Фиксированная сумма снижения (0 = отключено)
    "min_price_limit": 50,  # Минимальная цена (не опускаться ниже)
    "max_decrease_per_day": 10,  # Максимум снижений цены в день на один товар
    "notify_telegram": True,
    "log_all_checks": False,  # Логировать все проверки (даже без изменений)
}

# Глобальные переменные
_task = None
_starvell_service = None
_bot = None
_settings = DEFAULT_SETTINGS.copy()
_price_changes_today = {}  # {lot_id: count}
_last_reset_date = None


# === РАБОТА С НАСТРОЙКАМИ ===

def ensure_storage():
    """Создать директорию хранилища"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_settings():
    """Загрузить настройки из файла"""
    global _settings

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                _settings.update(loaded)
                logger.info(f"[AutoDumper] Настройки загружены")
        except Exception as e:
            logger.error(f"[AutoDumper] Ошибка загрузки настроек: {e}")


def save_settings():
    """Сохранить настройки в файл"""
    try:
        ensure_storage()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_settings, f, indent=2, ensure_ascii=False)
        logger.info(f"[AutoDumper] Настройки сохранены")
    except Exception as e:
        logger.error(f"[AutoDumper] Ошибка сохранения настроек: {e}")


def log_to_file(message: str):
    """Записать в лог-файл"""
    try:
        ensure_storage()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        logger.error(f"[AutoDumper] Ошибка записи в лог: {e}")


# === УВЕДОМЛЕНИЯ ===

async def notify_admin(message: str):
    """Отправить уведомление админам"""
    if not _settings["notify_telegram"] or not _bot:
        return

    try:
        from bot.core.config import BotConfig
        admin_ids = BotConfig.ADMIN_IDS()

        for admin_id in admin_ids:
            try:
                await _bot.send_message(
                    admin_id,
                    f"🤖 <b>AutoDumper</b>\n\n{message}",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"[AutoDumper] Ошибка отправки уведомления: {e}")
    except Exception as e:
        logger.error(f"[AutoDumper] Ошибка notify_admin: {e}")


# === ЛОГИКА ДЕМПЕРА ===

def reset_daily_counters():
    """Сбросить счётчики изменений цен (раз в день)"""
    global _price_changes_today, _last_reset_date
    today = date.today()

    if _last_reset_date != today:
        _price_changes_today = {}
        _last_reset_date = today
        logger.info("[AutoDumper] Счётчики изменений цен сброшены")


async def check_and_update_prices():
    """Проверить конкурентов и обновить цены"""
    try:
        if not _starvell_service:
            logger.warning("[AutoDumper] StarvellService не доступен")
            return

        logger.info("[AutoDumper] Начинаю проверку цен...")

        # Получаем свои лоты
        my_lots = await _starvell_service.get_my_lots()

        if not my_lots:
            logger.info("[AutoDumper] Нет активных лотов")
            return

        logger.info(f"[AutoDumper] Найдено {len(my_lots)} активных лотов")

        # Проверяем каждый лот
        for lot in my_lots:
            try:
                await check_lot_price(lot)
                await asyncio.sleep(2)  # Задержка между проверками
            except Exception as e:
                logger.error(f"[AutoDumper] Ошибка проверки лота: {e}")

    except Exception as e:
        logger.error(f"[AutoDumper] Ошибка проверки цен: {e}", exc_info=True)


async def check_lot_price(lot: Dict):
    """Проверить цену лота и обновить если нужно"""
    try:
        lot_id = lot.get("id")
        lot_title = lot.get("title", "Без названия")
        my_price = float(lot.get("price", 0))

        if my_price <= _settings["min_price_limit"]:
            if _settings["log_all_checks"]:
                logger.info(f"[AutoDumper] Лот '{lot_title}' уже на минимальной цене")
            return

        # Проверяем лимит изменений в день
        reset_daily_counters()
        changes_today = _price_changes_today.get(lot_id, 0)
        if changes_today >= _settings["max_decrease_per_day"]:
            if _settings["log_all_checks"]:
                logger.info(f"[AutoDumper] Лот '{lot_title}' достиг лимита изменений в день")
            return

        # Получаем конкурентов
        game_id = lot.get("gameId")
        category_id = lot.get("categoryId")

        if not game_id or not category_id:
            logger.warning(f"[AutoDumper] У лота '{lot_title}' нет gameId или categoryId")
            return

        competitors = await _starvell_service.get_competitors(game_id, category_id)

        if not competitors:
            if _settings["log_all_checks"]:
                logger.info(f"[AutoDumper] Нет конкурентов для лота '{lot_title}'")
            return

        # Фильтруем конкурентов с нужным количеством отзывов
        min_reviews = _settings["min_competitor_reviews"]
        qualified_competitors = [
            c for c in competitors
            if c.get("sellerReviews", 0) >= min_reviews
        ]

        if not qualified_competitors:
            if _settings["log_all_checks"]:
                logger.info(f"[AutoDumper] Нет конкурентов с >= {min_reviews} отзывов")
            return

        # Находим самую низкую цену
        lowest_competitor = min(qualified_competitors, key=lambda x: float(x.get("price", 999999)))
        competitor_price = float(lowest_competitor.get("price", 0))
        competitor_name = lowest_competitor.get("sellerName", "Неизвестно")
        competitor_reviews = lowest_competitor.get("sellerReviews", 0)

        # Если наша цена выше - снижаем
        if my_price > competitor_price:
            # Вычисляем новую цену
            if _settings["price_decrease_fixed"] > 0:
                new_price = my_price - _settings["price_decrease_fixed"]
            else:
                decrease_amount = my_price * (_settings["price_decrease_percent"] / 100)
                new_price = my_price - decrease_amount

            # Не опускаемся ниже минимума
            new_price = max(new_price, _settings["min_price_limit"])

            # Опускаемся чуть ниже конкурента
            new_price = min(new_price, competitor_price - 1)

            # Округляем
            new_price = round(new_price, 2)

            # Если цена не изменилась - пропускаем
            if new_price >= my_price:
                if _settings["log_all_checks"]:
                    logger.info(f"[AutoDumper] Цена '{lot_title}' не требует изменения")
                return

            # Обновляем цену
            result = await _starvell_service.update_lot_price(lot_id, new_price)

            if result.get("success"):
                # Вычисляем изменения
                price_diff = my_price - new_price
                percent_diff = (price_diff / my_price) * 100

                # Логируем
                log_message = (
                    f"Лот: {lot_title} (ID: {lot_id})\n"
                    f"Старая цена: {my_price}₽\n"
                    f"Новая цена: {new_price}₽\n"
                    f"Снижение: {price_diff:.2f}₽ ({percent_diff:.1f}%)\n"
                    f"Конкурент: {competitor_name} ({competitor_reviews} отзывов)\n"
                    f"Цена конкурента: {competitor_price}₽"
                )

                logger.info(f"[AutoDumper] Цена снижена: {log_message}")
                log_to_file(log_message)

                # Уведомляем админа
                await notify_admin(
                    f"📉 <b>Цена снижена</b>\n\n"
                    f"<b>Лот:</b> {lot_title}\n"
                    f"<b>Было:</b> {my_price}₽\n"
                    f"<b>Стало:</b> {new_price}₽\n"
                    f"<b>Снижение:</b> {price_diff:.2f}₽ ({percent_diff:.1f}%)\n\n"
                    f"<b>Конкурент:</b> {competitor_name}\n"
                    f"<b>Отзывов:</b> {competitor_reviews}\n"
                    f"<b>Цена:</b> {competitor_price}₽"
                )

                # Увеличиваем счётчик
                _price_changes_today[lot_id] = changes_today + 1
            else:
                logger.error(f"[AutoDumper] Не удалось обновить цену: {result.get('error')}")

        else:
            if _settings["log_all_checks"]:
                logger.info(f"[AutoDumper] Цена '{lot_title}' ({my_price}₽) ниже конкурента ({competitor_price}₽)")

    except Exception as e:
        logger.error(f"[AutoDumper] Ошибка check_lot_price: {e}", exc_info=True)


async def dumper_loop():
    """Основной цикл проверки цен"""
    logger.info("[AutoDumper] Цикл мониторинга запущен")

    while True:
        try:
            if not _settings["enabled"]:
                await asyncio.sleep(60)
                continue

            await check_and_update_prices()

            interval = _settings["check_interval"]
            logger.info(f"[AutoDumper] Следующая проверка через {interval} сек")
            await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("[AutoDumper] Цикл остановлен")
            break
        except Exception as e:
            logger.error(f"[AutoDumper] Ошибка в цикле: {e}", exc_info=True)
            await asyncio.sleep(60)


# === ХЭНДЛЕРЫ СОБЫТИЙ ===

async def on_init(bot, starvell, db, plugin_manager):
    """Инициализация плагина"""
    global _bot, _starvell_service

    _bot = bot
    _starvell_service = starvell

    ensure_storage()
    load_settings()

    logger.info(f"[AutoDumper] Плагин инициализирован (версия {VERSION})")
    logger.info(f"[AutoDumper] Статус: {'Включен' if _settings['enabled'] else 'Выключен'}")

    # Предупреждение о недостающих методах API
    logger.warning("[AutoDumper] ВНИМАНИЕ: Плагин требует реализации методов API в StarvellService")
    logger.warning("[AutoDumper] Необходимо добавить: get_my_lots(), get_competitors(), update_lot_price()")


async def on_start(bot, starvell, db, plugin_manager):
    """Запуск плагина"""
    global _task

    if _task is None:
        _task = asyncio.create_task(dumper_loop())
        logger.info("[AutoDumper] Фоновая задача запущена")


async def on_stop(bot, starvell, db, plugin_manager):
    """Остановка плагина"""
    global _task

    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
        logger.info("[AutoDumper] Фоновая задача остановлена")


# === КОМАНДЫ БОТА ===

router = Router()


def get_dumper_menu():
    """Клавиатура управления автодемпером"""
    status = "✅ Включен" if _settings["enabled"] else "❌ Выключен"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'🔴 Выключить' if _settings['enabled'] else '🟢 Включить'}",
            callback_data="dumper_toggle"
        )],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="dumper_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="dumper_stats")],
        [InlineKeyboardButton(text="📋 Логи", callback_data="dumper_logs")],
    ])

    return keyboard


async def cmd_dumper(message: Message):
    """Команда /dumper"""
    status = "✅ Включен" if _settings["enabled"] else "❌ Выключен"

    text = (
        f"🤖 <b>AutoDumper v{VERSION}</b>\n\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Интервал проверки:</b> {_settings['check_interval']} сек\n"
        f"<b>Мин. отзывов конкурента:</b> {_settings['min_competitor_reviews']}\n"
        f"<b>Снижение цены:</b> {_settings['price_decrease_percent']}%\n"
        f"<b>Минимальная цена:</b> {_settings['min_price_limit']}₽\n"
        f"<b>Макс. снижений в день:</b> {_settings['max_decrease_per_day']}\n\n"
        f"⚠️ <b>Внимание:</b> Плагин требует реализации методов API"
    )

    await message.answer(text, reply_markup=get_dumper_menu())


async def callback_dumper_toggle(callback: CallbackQuery):
    """Включить/выключить автодемпер"""
    await callback.answer()

    _settings["enabled"] = not _settings["enabled"]
    save_settings()

    status = "включен" if _settings["enabled"] else "выключен"

    text = (
        f"✅ AutoDumper {status}\n\n"
        f"<b>Интервал проверки:</b> {_settings['check_interval']} сек\n"
        f"<b>Мин. отзывов конкурента:</b> {_settings['min_competitor_reviews']}\n"
        f"<b>Снижение цены:</b> {_settings['price_decrease_percent']}%"
    )

    await callback.message.edit_text(text, reply_markup=get_dumper_menu())


async def callback_dumper_stats(callback: CallbackQuery):
    """Показать статистику"""
    await callback.answer()

    total_changes = sum(_price_changes_today.values())

    text = (
        f"📊 <b>Статистика AutoDumper</b>\n\n"
        f"<b>Изменений цен сегодня:</b> {total_changes}\n"
        f"<b>Лотов изменено:</b> {len(_price_changes_today)}\n\n"
        f"⚠️ Плагин в разработке - методы API не реализованы"
    )

    await callback.message.answer(text)


async def callback_dumper_logs(callback: CallbackQuery):
    """Показать последние логи"""
    await callback.answer()

    try:
        if not LOG_FILE.exists():
            await callback.message.answer("📋 Логов пока нет")
            return

        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-10:]  # Последние 10 строк

        if not last_lines:
            await callback.message.answer("📋 Логов пока нет")
            return

        text = "📋 <b>Последние 10 записей:</b>\n\n<code>" + "".join(last_lines) + "</code>"
        await callback.message.answer(text[:4000])  # Telegram лимит

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка чтения логов: {e}")


async def callback_dumper_settings(callback: CallbackQuery):
    """Показать настройки"""
    await callback.answer()

    text = (
        f"⚙️ <b>Настройки AutoDumper</b>\n\n"
        f"<b>Интервал проверки:</b> {_settings['check_interval']} сек\n"
        f"<b>Мин. отзывов конкурента:</b> {_settings['min_competitor_reviews']}\n"
        f"<b>Снижение цены:</b> {_settings['price_decrease_percent']}%\n"
        f"<b>Фикс. снижение:</b> {_settings['price_decrease_fixed']}₽\n"
        f"<b>Минимальная цена:</b> {_settings['min_price_limit']}₽\n"
        f"<b>Макс. снижений/день:</b> {_settings['max_decrease_per_day']}\n"
        f"<b>Уведомления:</b> {'Вкл' if _settings['notify_telegram'] else 'Выкл'}\n"
        f"<b>Логировать все:</b> {'Да' if _settings['log_all_checks'] else 'Нет'}\n\n"
        f"Для изменения настроек отредактируйте файл:\n"
        f"<code>{SETTINGS_FILE}</code>"
    )

    await callback.message.answer(text)


# === ПРИВЯЗКА К СОБЫТИЯМ ===
BIND_TO_INIT = [on_init]
BIND_TO_START = [on_start]
BIND_TO_DELETE = [on_stop]

# === РЕГИСТРАЦИЯ КОМАНД ===
COMMANDS = {
    "dumper": {
        "handler": cmd_dumper,
        "description": "🤖 Управление автодемпером цен",
        "filters": [Command("dumper")]
    }
}

CALLBACKS = {
    "dumper_toggle": {
        "handler": callback_dumper_toggle,
        "filter": F.data == "dumper_toggle"
    },
    "dumper_stats": {
        "handler": callback_dumper_stats,
        "filter": F.data == "dumper_stats"
    },
    "dumper_logs": {
        "handler": callback_dumper_logs,
        "filter": F.data == "dumper_logs"
    },
    "dumper_settings": {
        "handler": callback_dumper_settings,
        "filter": F.data == "dumper_settings"
    }
}
