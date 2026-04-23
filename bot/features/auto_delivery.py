"""
Модуль авто-выдачи товаров 
"""

import asyncio
import logging
import random
import string
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from bot.core.config import BotConfig, get_config_manager


logger = logging.getLogger("AutoDelivery")


class AutoDeliveryService:
    """
    Сервис автоматической выдачи товаров
    - Хранит товары в текстовых файлах storage/products/{lot_id}.txt
    - Каждая строка = 1 товар
    - При выдаче товар удаляется из файла
    - Поддерживает multi-delivery (выдача нескольких товаров)
    """
    
    def __init__(self):
        self.products_dir = Path("storage/products")
        self._running = False
        self.delivery_tests = {}  # Тестовые ключи: key -> lot_name
        
    async def start(self):
        """Запустить сервис"""
        self.products_dir.mkdir(parents=True, exist_ok=True)
        self._running = True
        logger.info("✅ Сервис авто-выдачи запущен")
    
    async def stop(self):
        """Остановить сервис"""
        self._running = False
        logger.info("⏹️ Сервис авто-выдачи остановлен")
    
    # ==================== Управление лотами ====================
    
    async def get_lots(self) -> List[dict]:
        """Получить список лотов с автовыдачей"""
        lots = []
        
        config = get_config_manager()
        if not config._config.has_section("AutoDelivery"):
            return lots
        
        sections = [s for s in config._config.sections() if s.startswith("AutoDelivery.")]
        
        for section in sections:
            lot_name = section.replace("AutoDelivery.", "", 1)

            enabled = config.get(section, "enabled", True)
            response_text = config.get(section, "response_text", "")
            products_file = config.get(section, "products_file", "")
            disable_on_empty = config.get(section, "disable_on_empty", False)
            disable_auto_restore = config.get(section, "disable_auto_restore", False)
            
            products_count = 0
            if products_file:
                products_count = await self.count_products(products_file)
            
            lots.append({
                "name": lot_name,
                "enabled": enabled,
                "response_text": response_text,
                "products_file": products_file,
                "products_count": products_count,
                "disable_on_empty": disable_on_empty,
                "disable_auto_restore": disable_auto_restore
            })
        
        return lots
    
    async def add_lot(self, name: str, response_text: str = ""):
        """Добавить новый лот с автовыдачей"""
        section = f"AutoDelivery.{name}"
        
        config = get_config_manager()
        if not config._config.has_section("AutoDelivery"):
            config._config.add_section("AutoDelivery")
        
        BotConfig.update(f"{section}.enabled", True)
        BotConfig.update(f"{section}.response_text", response_text)
        BotConfig.update(f"{section}.products_file", "")
        BotConfig.update(f"{section}.disable_on_empty", False)
        BotConfig.update(f"{section}.disable_auto_restore", False)
        
        logger.info(f"Добавлен лот для автовыдачи: {name}")
    
    async def delete_lot(self, name: str):
        """Удалить лот"""
        section = f"AutoDelivery.{name}"
        
        config = get_config_manager()
        if config._config.has_section(section):
            config._config.remove_section(section)
            config.save()
            logger.info(f"Удалён лот автовыдачи: {name}")
    
    async def update_lot_setting(self, name: str, setting: str, value):
        """Обновить настройку лота"""
        section = f"AutoDelivery.{name}"
        BotConfig.update(f"{section}.{setting}", value)
        logger.info(f"Настройка {setting} лота {name} обновлена: {value}")
    
    # ==================== Файлы товаров ====================
    
    async def count_products(self, file_name: str) -> int:
        """Подсчитать товары в файле"""
        file_path = self.products_dir / file_name
        
        if not file_path.exists():
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = [line.strip() for line in f if line.strip()]
                return len(products)
        except Exception as e:
            logger.error(f"Ошибка подсчёта товаров в {file_name}: {e}")
            return 0
    
    async def ensure_products_file(self, file_name: str):
        """Создать файл товаров если не существует"""
        file_path = self.products_dir / file_name
        
        if not file_path.exists():
            file_path.touch()
            logger.info(f"Создан файл товаров: {file_name}")
    
    async def create_test_key(self, lot_name: str) -> str:
        """Создать тестовый ключ автовыдачи"""
        key = "".join(random.sample(string.ascii_letters + string.digits, 50))
        self.delivery_tests[key] = lot_name
        logger.info(f"Создан тестовый ключ для лота {lot_name}")
        return key
    
    # ==================== Старые методы ====================
    
    def get_products_count(self, lot_id: str) -> int:
        """
        Получить количество доступных товаров для лота
        
        Args:
            lot_id: ID лота
            
        Returns:
            Количество товаров
        """
        file_path = self.products_dir / f"{lot_id}.txt"
        
        if not file_path.exists():
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = [line.strip() for line in f if line.strip()]
                return len(products)
        except Exception as e:
            logger.error(f"❌ Ошибка подсчёта товаров для лота {lot_id}: {e}")
            return 0
    
    def get_products(self, lot_id: str, amount: int = 1) -> Tuple[List[str], int]:
        """
        Получить товары для выдачи
        
        Args:
            lot_id: ID лота
            amount: количество товаров для выдачи
            
        Returns:
            Tuple (список товаров, количество оставшихся товаров)
            Если товаров недостаточно, вернёт ([], -1)
        """
        file_path = self.products_dir / f"{lot_id}.txt"
        
        if not file_path.exists():
            logger.warning(f"⚠️ Файл товаров для лота {lot_id} не найден")
            return [], -1
        
        try:
            # Читаем все товары
            with open(file_path, 'r', encoding='utf-8') as f:
                all_products = [line.strip() for line in f if line.strip()]
            
            # Проверяем достаточно ли товаров
            if len(all_products) < amount:
                logger.warning(f"⚠️ Недостаточно товаров для лота {lot_id}: нужно {amount}, доступно {len(all_products)}")
                return [], -1
            
            # Берём нужное количество
            products_to_deliver = all_products[:amount]
            remaining_products = all_products[amount:]
            
            # Сохраняем оставшиеся товары
            with open(file_path, 'w', encoding='utf-8') as f:
                if remaining_products:
                    f.write('\n'.join(remaining_products))
                else:
                    # Файл пустой - записываем пустую строку
                    f.write('')
            
            goods_left = len(remaining_products)
            logger.info(f"📦 Выдано {amount} товар(ов) для лота {lot_id}. Осталось: {goods_left}")
            
            return products_to_deliver, goods_left
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении товаров для лота {lot_id}: {e}")
            return [], -1
    
    def add_products(self, lot_id: str, products: List[str], at_zero_position: bool = False):
        """
        Добавить товары в файл лота
        
        Args:
            lot_id: ID лота
            products: список товаров для добавления
            at_zero_position: добавить в начало файла (для возврата товаров)
        """
        file_path = self.products_dir / f"{lot_id}.txt"
        
        try:
            # Читаем существующие товары (если файл есть)
            existing_products = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_products = [line.strip() for line in f if line.strip()]
            
            # Добавляем новые товары
            if at_zero_position:
                # Добавляем в начало (для возврата)
                all_products = products + existing_products
            else:
                # Добавляем в конец
                all_products = existing_products + products
            
            # Сохраняем
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_products))
            
            logger.info(f"➕ Добавлено {len(products)} товар(ов) для лота {lot_id}. Всего: {len(all_products)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении товаров для лота {lot_id}: {e}")
    
    async def deliver_goods(self, order: dict, lot_config: dict) -> dict:
        """
        Выдать товары для заказа
        
        Args:
            order: данные заказа {
                'id': order_id,
                'lot_id': lot_id,
                'lot_title': lot_title,
                'buyer_username': username,
                'amount': quantity
            }
            lot_config: конфигурация лота {
                'response': текст сообщения с $product,
                'productsFileName': имя файла (опционально),
                'disableMultiDelivery': отключить мульти-выдачу (опционально),
                'disableAutoDelivery': отключить авто-выдачу для лота
            }
            
        Returns:
            dict с результатом {
                'delivered': True/False,
                'delivery_text': текст для отправки,
                'goods_delivered': количество выданных товаров,
                'goods_left': количество оставшихся товаров,
                'error': код ошибки (0 = нет ошибки),
                'error_text': текст ошибки
            }
        """
        result = {
            'delivered': False,
            'delivery_text': None,
            'goods_delivered': 0,
            'goods_left': -1,
            'error': 0,
            'error_text': None
        }
        
        # Проверяем глобальный переключатель
        if not BotConfig.AUTO_DELIVERY_ENABLED():
            logger.debug("Авто-выдача отключена глобально")
            return result
        
        # Проверяем отключение для конкретного лота
        if lot_config.get('disableAutoDelivery', False):
            logger.info(f"Для лота \"{order['lot_title']}\" отключена авто-выдача")
            return result
        
        # Получаем текст ответа
        delivery_text = lot_config.get('response', '')
        
        # Определяем количество товаров для выдачи
        amount = 1
        products_file = lot_config.get('productsFileName')
        
        if products_file:
            # Если есть товарный файл, проверяем multi-delivery
            disable_multi = lot_config.get('disableMultiDelivery', False)
            if not disable_multi and order.get('amount'):
                amount = order['amount']
        
        # Получаем товары из файла
        products = []
        goods_left = -1
        
        if products_file:
            lot_id = str(order['lot_id'])
            products, goods_left = self.get_products(lot_id, amount)
            
            if not products:
                # Не удалось получить товары
                error_msg = f"Не удалось получить товары для заказа {order['id']}"
                logger.error(f"❌ {error_msg}")
                result['error'] = 1
                result['error_text'] = error_msg
                
                # Возвращаем товары обратно если они были взяты
                # (в текущей реализации этого не происходит, но для будущего)
                return result
            
            # Заменяем $product в тексте
            product_text = '\n'.join(products)
            delivery_text = delivery_text.replace('$product', product_text)
        
        # Заменяем другие переменные
        delivery_text = delivery_text.replace('$username', order.get('buyer_username', 'Покупатель'))
        delivery_text = delivery_text.replace('$order_id', str(order.get('id', '')))
        
        # Успешная выдача
        result['delivered'] = True
        result['delivery_text'] = delivery_text
        result['goods_delivered'] = amount
        result['goods_left'] = goods_left
        
        logger.info(f"✅ Товар для заказа {order['id']} подготовлен к выдаче")
        
        return result
