"""
Приветственное сообщение: автоответ покупателю при первом обращении.

Когда покупатель впервые пишет в чат, бот один раз отправляет настроенный
продавцом текст. Настройка: /menu → «Приветственное сообщение».
"""

import json
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.keyboards import get_welcome_menu, CBT

logger = logging.getLogger(__name__)
router = Router()

WELCOME_FILE = Path("storage/welcome_message.json")

DEFAULT_WELCOME_TEXT = (
    "👋 Здравствуйте! Спасибо за обращение.\n"
    "Опишите ваш заказ — я на связи и помогу."
)


class WelcomeState(StatesGroup):
    """Состояния для настройки приветственного сообщения."""
    waiting_for_text = State()


def load_welcome() -> dict:
    """Загрузить настройки приветственного сообщения."""
    if not WELCOME_FILE.exists():
        data = {"enabled": False, "text": DEFAULT_WELCOME_TEXT}
        save_welcome(data)
        return data
    try:
        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("bad format")
        data.setdefault("enabled", False)
        data.setdefault("text", DEFAULT_WELCOME_TEXT)
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки welcome_message.json: {e}")
        return {"enabled": False, "text": DEFAULT_WELCOME_TEXT}


def save_welcome(data: dict) -> None:
    """Сохранить настройки приветственного сообщения."""
    try:
        WELCOME_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WELCOME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения welcome_message.json: {e}")


def _menu_text(data: dict) -> str:
    enabled = data.get("enabled", False)
    text = data.get("text", DEFAULT_WELCOME_TEXT)
    preview = text if len(text) <= 500 else text[:500] + "…"
    return (
        "👋 <b>Приветственное сообщение</b>\n\n"
        "Бот один раз ответит покупателю этим текстом, когда тот впервые "
        "напишет в чат.\n\n"
        f"<b>Статус:</b> {'✅ Включено' if enabled else '❌ Выключено'}\n\n"
        "<b>Текущий текст:</b>\n"
        f"<blockquote>{preview}</blockquote>"
    )


@router.callback_query(F.data == CBT.WELCOME_MENU)
async def callback_welcome_menu(callback: CallbackQuery, **kwargs):
    """Меню приветственного сообщения."""
    await callback.answer()
    data = load_welcome()
    await callback.message.edit_text(
        _menu_text(data),
        reply_markup=get_welcome_menu(data.get("enabled", False)),
    )


@router.callback_query(F.data == CBT.TOGGLE_WELCOME)
async def callback_toggle_welcome(callback: CallbackQuery, **kwargs):
    """Включить/выключить приветственное сообщение."""
    data = load_welcome()
    data["enabled"] = not data.get("enabled", False)
    save_welcome(data)
    await callback.answer(
        f"Приветствие {'включено' if data['enabled'] else 'выключено'}",
        show_alert=False,
    )
    await callback.message.edit_text(
        _menu_text(data),
        reply_markup=get_welcome_menu(data.get("enabled", False)),
    )


@router.callback_query(F.data == CBT.SET_WELCOME_TEXT)
async def callback_set_welcome_text(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Запросить новый текст приветствия."""
    await callback.answer()
    await state.set_state(WelcomeState.waiting_for_text)
    await callback.message.answer(
        "✏️ <b>Изменение текста приветствия</b>\n\n"
        "Напишите новый текст и отправьте его одним сообщением в этот чат.\n"
        "Именно этот текст бот будет отправлять покупателю при первом обращении.\n\n"
        "Текущий текст будет <b>полностью заменён</b> на новый.\n\n"
        "Поддерживается HTML-разметка: <b>жирный</b>, <i>курсив</i>, <code>код</code>.\n"
        "Отправьте /cancel для отмены."
    )


@router.message(WelcomeState.waiting_for_text)
async def process_welcome_text(message: Message, state: FSMContext, **kwargs):
    """Сохранить новый текст приветствия."""
    if message.text and message.text.strip() == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено")
        return

    new_text = (message.text or "").strip()
    if not new_text:
        await message.answer("❌ Нужно отправить текстовое сообщение. Напишите новый текст приветствия и отправьте его.")
        return
    if len(new_text) > 2000:
        await message.answer("❌ Слишком длинный текст (макс. 2000 символов). Сократите.")
        return

    data = load_welcome()
    data["text"] = new_text
    save_welcome(data)
    await state.clear()

    preview = new_text if len(new_text) <= 100 else new_text[:100] + "…"
    await message.answer(
        "✅ <b>Текст приветствия сохранён!</b>\n\n"
        "Теперь при первом обращении покупатель получит:\n"
        f"<blockquote>{preview}</blockquote>\n\n"
        f"<b>Статус:</b> {'✅ Включено' if data.get('enabled') else '❌ Выключено (включите в меню)'}",
        reply_markup=get_welcome_menu(data.get("enabled", False)),
    )
