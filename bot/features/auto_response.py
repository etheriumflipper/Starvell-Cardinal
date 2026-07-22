"""
Система автоматических ответов на подтверждение заказа и отзывы
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Set, Optional, Any

from bot.core.config import BotConfig, get_config_manager
from bot.core.services import StarvellService
from bot.core.storage import Database

logger = logging.getLogger("AutoResponse")

# Москва = UTC+3 (как в плагине auto_review_comment)
_MSK = timezone(timedelta(hours=3))


class AutoResponseService:
    """Сервис автоматических ответов"""
    
    def __init__(self, starvell: StarvellService, db: Database):
        self.starvell = starvell
        self.db = db
        
        # Отслеживание уже обработанных заказов
        self._confirmed_orders: Set[str] = set()
        self._reviewed_orders: Set[str] = set()
        
    async def start(self):
        """Запуск сервиса"""
        # Загружаем все текущие заказы как уже обработанные
        # Это предотвращает отправку автоответов на старые заказы при первом запуске
        await self._initialize_processed_orders()
        logger.info("Сервис автоответов запущен")
        
    async def stop(self):
        """Остановка сервиса"""
        logger.info("Сервис автоответов остановлен")
    
    async def _initialize_processed_orders(self):
        """
        Инициализация: загружаем все текущие заказы как уже обработанные
        Это предотвращает отправку автоответов на старые заказы при включении функции
        """
        try:
            logger.info("Инициализация автоответов: загрузка существующих заказов...")
            
            # Получаем все заказы
            orders = await self.starvell.get_orders()
            
            for order in orders:
                order_id = order.get("id")
                if not order_id:
                    continue
                
                status = str(order.get("status", "")).upper()
                review = order.get("review")
                
                # Добавляем завершённые заказы в обработанные
                if status == "COMPLETED":
                    self._confirmed_orders.add(order_id)
                
                # Добавляем заказы с отзывами в обработанные
                if review:
                    self._reviewed_orders.add(order_id)
            
            logger.info(f"Загружено {len(self._confirmed_orders)} завершённых заказов и {len(self._reviewed_orders)} отзывов")
            logger.info("✅ Автоответы будут отправляться только на новые заказы")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации обработанных заказов: {e}", exc_info=True)
        
    async def check_and_respond(self):
        """
        Проверить заказы и отправить автоответы где необходимо
        """
        try:
            # Проверяем, включены ли автоответы
            order_confirm_enabled = BotConfig.ORDER_CONFIRM_RESPONSE_ENABLED()
            review_response_enabled = BotConfig.REVIEW_RESPONSE_ENABLED()
            
            if not order_confirm_enabled and not review_response_enabled:
                return
            
            # Получаем все заказы
            orders = await self.starvell.get_orders()
            
            for order in orders:
                order_id = order.get("id")
                if not order_id:
                    continue
                
                # Проверяем ответ на подтверждение заказа
                if order_confirm_enabled:
                    await self._check_order_confirmation(order)
                
                # Проверяем ответ на отзыв
                if review_response_enabled:
                    await self._check_review_response(order)
                    
        except Exception as e:
            logger.error(f"Ошибка при проверке автоответов: {e}", exc_info=True)
            
    async def _check_order_confirmation(self, order: Dict):
        """
        Проверить, нужно ли отправить ответ на подтверждение заказа
        """
        order_id = order.get("id")
        status = str(order.get("status", "")).upper()
        
        # Заказ должен быть завершён (COMPLETED)
        if status != "COMPLETED":
            return
        
        # Проверяем, не отправляли ли уже ответ
        if order_id in self._confirmed_orders:
            return
        
        # Проверяем черный список (по buyer ID если есть)
        buyer_id = order.get("buyerId") or order.get("buyer_id")
        if buyer_id:
            config = get_config_manager()
            blacklist_section = f"Blacklist.{buyer_id}"
            if config._config.has_section(blacklist_section):
                logger.debug(f"Автоответ на заказ {order_id[:8]} пропущен (покупатель {buyer_id} в ЧС)")
                self._confirmed_orders.add(order_id)  # Помечаем как обработанный
                return
        
        try:
            # Получаем детали заказа для получения chat_id
            order_details = await self.starvell.get_order_details(order_id)
            
            # Извлекаем chat_id
            chat_id = None
            page_props = order_details.get("pageProps", {})
            
            # Пробуем разные варианты
            if "chat" in page_props and isinstance(page_props["chat"], dict):
                chat_id = page_props["chat"].get("id")
            elif "chatId" in order:
                chat_id = order.get("chatId")
            elif "chat_id" in order:
                chat_id = order.get("chat_id")
                
            if not chat_id:
                logger.warning(f"Не удалось найти chat_id для заказа {order_id}")
                # Помечаем как обработанный, чтобы не спамить логи
                self._confirmed_orders.add(order_id)
                return
            
            # Отправляем ответ
            response_text = BotConfig.ORDER_CONFIRM_RESPONSE_TEXT()
            await self.starvell.send_message(chat_id, response_text)
            
            # Помечаем как обработанный
            self._confirmed_orders.add(order_id)
            
            logger.info(f"✅ Отправлен автоответ на подтверждение заказа {order_id[:8]}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа на подтверждение заказа {order_id}: {e}")
            # Не добавляем в обработанные, чтобы попробовать ещё раз

    def _format_review_reply(self, template: str) -> str:
        """Подставить {date} (МСК) и безопасный format без KeyError."""
        date_str = datetime.now(_MSK).strftime("%d.%m.%Y %H:%M")
        try:
            return template.format(date=date_str)
        except (KeyError, ValueError, IndexError):
            return template.replace("{date}", date_str)

    def _extract_review(self, order: Dict, page_props: Dict) -> Optional[Dict[str, Any]]:
        """Достать объект отзыва из списка заказов или деталей."""
        review = page_props.get("review")
        if isinstance(review, dict) and review.get("id"):
            return review
        review = order.get("review")
        if isinstance(review, dict) and review.get("id"):
            return review
        return None
            
    async def _check_review_response(self, order: Dict):
        """
        Проверить, нужно ли опубликовать ответ продавца на отзыв
        (через /api/review-responses/create — как в плагине auto_review_comment).
        """
        order_id = order.get("id")
        
        # Есть ли намёк на отзыв в списке заказов
        review_hint = order.get("review")
        if not review_hint:
            return
        
        # Проверяем, не отправляли ли уже ответ
        if order_id in self._reviewed_orders:
            return
        
        # Проверяем черный список (по buyer ID если есть)
        buyer_id = order.get("buyerId") or order.get("buyer_id")
        if buyer_id:
            config = get_config_manager()
            blacklist_section = f"Blacklist.{buyer_id}"
            if config._config.has_section(blacklist_section):
                logger.debug(f"Автоответ на отзыв заказа {order_id[:8]} пропущен (покупатель {buyer_id} в ЧС)")
                self._reviewed_orders.add(order_id)
                return
        
        try:
            if not self.starvell.api:
                logger.warning("API не инициализирован для ответа на отзыв")
                return

            order_details = await self.starvell.get_order_details(order_id)
            page_props = order_details.get("pageProps", {}) or {}
            review = self._extract_review(order, page_props)

            if not review:
                logger.debug(f"Отзыв для заказа {order_id[:8]} ещё не доступен в деталях")
                return

            review_id = str(review.get("id"))
            if review.get("sellerReply") or review.get("seller_reply"):
                logger.info(f"⏭ Заказ {order_id[:8]}: ответ на отзыв уже есть")
                self._reviewed_orders.add(order_id)
                return

            rating = review.get("rating", "N/A")
            reply_text = self._format_review_reply(BotConfig.REVIEW_RESPONSE_TEXT())

            result = await self.starvell.api.create_review_response(
                review_id=review_id,
                text=reply_text,
                order_id=order_id,
            )

            self._reviewed_orders.add(order_id)
            if isinstance(result, dict) and result.get("already_replied"):
                logger.info(f"⏭ Отзыв {review_id}: ответ уже был на сайте")
            else:
                logger.info(
                    f"⭐ Опубликован ответ на отзыв (рейтинг: {rating}) "
                    f"для заказа {order_id[:8]}"
                )
            
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа на отзыв для заказа {order_id}: {e}")
            # Не добавляем в обработанные, чтобы попробовать ещё раз
