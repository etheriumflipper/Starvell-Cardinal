"""
AutoSteam Starvell - Автоматическое пополнение баланса Steam через API Bazaar-Store
Переписан для Starvell Cardinal
"""

import json
import time
import logging
import uuid
import re
import aiohttp
from pathlib import Path
from typing import Optional, Dict

# === МЕТАДАННЫЕ ===
NAME = "AutoSteam Starvell"
VERSION = "2.0.0"
DESCRIPTION = "Автоматическое пополнение баланса Steam через API Bazaar-Store"
AUTHOR = "@embedium"
UUID = "f9e8d7c6-b5a4-4321-9876-543210fedcba"

logger = logging.getLogger("AutoSteam")
LOGGER_PREFIX = "[STEAM AUTO DEPOSIT]"

# Базовый URL согласно документации
BAZAAR_API_URL = "https://api.ns.gifts/api/v1"

# Пути к файлам хранилища
STORAGE_DIR = Path(f"storage/plugins/{UUID}")
SETTINGS_FILE = STORAGE_DIR / "settings.json"
ORDERS_FILE = STORAGE_DIR / "orders.json"

# Настройки по умолчанию
DEFAULT_SETTINGS = {
    "bazaar_email": "",
    "bazaar_password": "",
    "min_amount": 0.22,
    "allowed_categories": ["Steam", "Пополнение Steam", "Steam баланс"]
}


def ensure_storage():
    """Создать директорию если не существует"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def load_json(filepath: Path, default=None):
    """Загрузить JSON файл"""
    if default is None:
        default = {}

    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Ошибка загрузки {filepath}: {e}")

    return default


def save_json(filepath: Path, data):
    """Сохранить JSON файл"""
    ensure_storage()
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка сохранения {filepath}: {e}")


class SteamAutoDepositBot:
    def __init__(self):
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.bazaar_token: Optional[str] = None
        self.token_expiry: float = 0

        # Регулярные выражения
        self.currency_re = re.compile(r"(RUB|UAH|KZT|рубл|грив|тенге)", re.IGNORECASE)
        self.steam_re = re.compile(r"(?:https?:\/\/)?steamcommunity\.com\/id\/(\w+)", re.IGNORECASE)

        # Хранилище заказов: order_id -> order_info
        self.order_data: Dict[str, dict] = {}
        self.order_timestamps: Dict[str, float] = {}  # order_id -> timestamp создания
        self.max_order_age = 3600  # Максимальный возраст заказа в секундах (1 час)

    def cleanup_old_orders(self):
        """Очистить старые заказы из памяти"""
        current_time = time.time()
        expired_orders = [
            order_id for order_id, timestamp in self.order_timestamps.items()
            if current_time - timestamp > self.max_order_age
        ]

        for order_id in expired_orders:
            if order_id in self.order_data:
                del self.order_data[order_id]
            del self.order_timestamps[order_id]
            logger.debug(f"{LOGGER_PREFIX} Удален устаревший заказ {order_id}")

    async def get_bazaar_token(self):
        """Получить или обновить токен Bazaar API"""
        if time.time() < self.token_expiry - 300:
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BAZAAR_API_URL}/get_token",
                    json={
                        "email": self.settings["bazaar_email"],
                        "password": self.settings["bazaar_password"]
                    }
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    self.bazaar_token = data["token"]
                    self.token_expiry = data["exp"]
                    logger.info(f"{LOGGER_PREFIX} Bazaar token updated")
        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Auth error: {str(e)}")
            raise

    async def check_balance(self) -> float:
        """Проверить баланс Bazaar"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BAZAAR_API_URL}/check_balance",
                    headers={"Authorization": f"Bearer {self.bazaar_token}"}
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return float(data["balance"])
        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Balance check error: {str(e)}")
            raise

    async def create_order(self, service_id: int, quantity: float, steam_login: str) -> str:
        """Создать заказ в Bazaar"""
        custom_id = str(uuid.uuid4())
        payload = {
            "service_id": service_id,
            "quantity": quantity,
            "custom_id": custom_id,
            "data": steam_login
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BAZAAR_API_URL}/create_order",
                    headers={"Authorization": f"Bearer {self.bazaar_token}"},
                    json=payload
                ) as response:
                    response.raise_for_status()
                    return custom_id
        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Order creation error: {str(e)}")
            raise

    async def pay_order(self, custom_id: str):
        """Оплатить заказ в Bazaar"""
        payload = {"custom_id": custom_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BAZAAR_API_URL}/pay_order",
                    headers={"Authorization": f"Bearer {self.bazaar_token}"},
                    json=payload
                ) as response:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Payment error: {str(e)}")
            raise

    def parse_currency(self, input_str: str) -> str:
        """Определить валюту из строки"""
        input_str = input_str.upper()
        if "RUB" in input_str or "РУБЛ" in input_str:
            return "RUB"
        elif "UAH" in input_str or "ГРИВ" in input_str:
            return "UAH"
        elif "KZT" in input_str or "ТЕНГЕ" in input_str:
            return "KZT"
        return "UNKNOWN"

    async def handle_new_order(self, order_data: dict, starvell_service=None, **kwargs):
        """Обработчик нового заказа"""
        try:
            if not starvell_service:
                return

            # Проверяем категорию
            lot_name = order_data.get("lot_name", "")
            if not any(cat.lower() in lot_name.lower() for cat in self.settings["allowed_categories"]):
                logger.debug(f"{LOGGER_PREFIX} Заказ {order_data['id']} не относится к категории Steam")
                return

            lot_description = order_data.get("lot_description", "")
            if not lot_description:
                if order_data.get("chat_id"):
                    await starvell_service.send_message(
                        order_data["chat_id"],
                        "❌ Описание лота отсутствует."
                    )
                return

            # Проверяем валюту
            currency_match = self.currency_re.search(lot_description)
            if not currency_match:
                if order_data.get("chat_id"):
                    await starvell_service.send_message(
                        order_data["chat_id"],
                        "❌ В описании лота не указана валюта (RUB/UAH/KZT)"
                    )
                return

            currency = self.parse_currency(currency_match.group(0))
            amount = order_data.get("amount", 0)

            if amount < self.settings["min_amount"]:
                if order_data.get("chat_id"):
                    await starvell_service.send_message(
                        order_data["chat_id"],
                        f"❌ Сумма заказа меньше минимальной ({self.settings['min_amount']}$)"
                    )
                return

            # Сохраняем данные заказа
            self.order_data[order_data["id"]] = {
                "currency": currency,
                "sum": amount,
                "chat_id": order_data.get("chat_id")
            }
            self.order_timestamps[order_data["id"]] = time.time()

            # Очищаем старые заказы
            self.cleanup_old_orders()

            # Запрашиваем Steam логин
            if order_data.get("chat_id"):
                await starvell_service.send_message(
                    order_data["chat_id"],
                    f"💰 Валюта пополнения: {currency}\n"
                    "📝 Отправьте ваш Steam логин или ссылку на профиль (например, https://steamcommunity.com/id/yourlogin):"
                )

        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Order handling error: {str(e)}")

    async def handle_new_message(self, message_data: dict, starvell_service=None, **kwargs):
        """Обработчик нового сообщения"""
        try:
            if not starvell_service:
                return

            content = message_data.get("content", "")
            chat_id = message_data.get("chat_id")
            author = message_data.get("author")

            if not content or not chat_id:
                return

            # Ищем заказ для этого чата
            order_id = None
            order_info = None

            for oid, info in self.order_data.items():
                if info.get("chat_id") == chat_id:
                    order_id = oid
                    order_info = info
                    break

            if not order_id or not order_info:
                return

            # Проверяем Steam логин
            match = self.steam_re.search(content)
            if not match:
                await starvell_service.send_message(
                    chat_id,
                    "❌ Неверный формат Steam логина. Укажите ссылку на профиль или логин в формате: https://steamcommunity.com/id/yourlogin"
                )
                return

            steam_login = match.group(1)
            await self.process_deposit(order_id, order_info, steam_login, starvell_service)

        except Exception as e:
            logger.error(f"{LOGGER_PREFIX} Message handling error: {str(e)}")

    async def process_deposit(self, order_id: str, order_info: dict, steam_login: str, starvell_service):
        """Обработка пополнения Steam"""
        try:
            await self.get_bazaar_token()
            total_sum = order_info["sum"]
            chat_id = order_info["chat_id"]

            # Проверяем баланс
            balance = await self.check_balance()
            if balance < total_sum:
                await starvell_service.send_message(
                    chat_id,
                    f"❌ Недостаточно средств на балансе. Текущий баланс: {balance:.2f}$"
                )
                return

            # Создаем и оплачиваем заказ
            custom_id = await self.create_order(1, total_sum, steam_login)
            await self.pay_order(custom_id)

            await starvell_service.send_message(
                chat_id,
                f"✅ Аккаунт {steam_login} пополнен на {total_sum:.2f}$\n"
                "🙏 Спасибо за покупку!"
            )

            # Удаляем заказ из обработки
            if order_id in self.order_data:
                del self.order_data[order_id]
            if order_id in self.order_timestamps:
                del self.order_timestamps[order_id]

        except Exception as e:
            await starvell_service.send_message(
                order_info["chat_id"],
                f"❌ Ошибка: {str(e)}"
            )
            logger.error(f"{LOGGER_PREFIX} Deposit error: {str(e)}")


# Глобальный экземпляр бота
_bot_instance = None


def on_pre_init():
    """Инициализация перед запуском бота"""
    ensure_storage()
    logger.info(f"{LOGGER_PREFIX} {NAME} v{VERSION} загружен")


async def on_init(bot=None, starvell=None, db=None, plugin_manager=None):
    """Инициализация после запуска бота"""
    global _bot_instance
    _bot_instance = SteamAutoDepositBot()
    logger.info(f"{LOGGER_PREFIX} Плагин инициализирован")


async def on_new_order(order_data: dict, starvell_service=None, **kwargs):
    """Обработчик новых заказов"""
    if _bot_instance:
        await _bot_instance.handle_new_order(order_data, starvell_service, **kwargs)


async def on_new_message(message_data: dict, starvell_service=None, **kwargs):
    """Обработчик новых сообщений"""
    if _bot_instance:
        await _bot_instance.handle_new_message(message_data, starvell_service, **kwargs)


def on_delete():
    """Удаление плагина"""
    logger.info(f"{LOGGER_PREFIX} Плагин удаляется...")


# === ПРИВЯЗКИ К СОБЫТИЯМ ===
BIND_TO_PRE_INIT = [on_pre_init]
BIND_TO_INIT = [on_init]
BIND_TO_NEW_ORDER = [on_new_order]
BIND_TO_NEW_MESSAGE = [on_new_message]
BIND_TO_DELETE = [on_delete]
