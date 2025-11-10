from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов (rate limiting)
    
    Защищает бота от спама и флуда со стороны пользователей
    """
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Args:
            rate_limit: Минимальный интервал между запросами в секундах
                       (по умолчанию 0.5 секунды = 2 запроса в секунду максимум)
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timers: Dict[int, datetime] = {}
        self.spam_warnings: Dict[int, int] = {}  # Счётчик предупреждений
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = datetime.now()
        
        # Проверяем время последнего запроса от пользователя
        if user_id in self.user_timers:
            time_passed = (now - self.user_timers[user_id]).total_seconds()
            
            if time_passed < self.rate_limit:
                # Слишком быстро - засчитываем нарушение
                self.spam_warnings[user_id] = self.spam_warnings.get(user_id, 0) + 1
                
                logger.warning(
                    f"⏱ Rate limit для пользователя {user_id} "
                    f"({event.from_user.username or 'no username'}). "
                    f"Нарушений: {self.spam_warnings[user_id]}"
                )
                
                # Отправляем разные сообщения в зависимости от типа события
                if isinstance(event, CallbackQuery):
                    # Для callback просто показываем уведомление
                    await event.answer("⏱ Подожди немного", show_alert=False)
                
                elif isinstance(event, Message):
                    # Для сообщений отправляем предупреждение только раз в 5 секунд
                    last_warning_time = getattr(self, f'_last_warning_{user_id}', None)
                    
                    if last_warning_time is None or (now - last_warning_time).total_seconds() > 5:
                        setattr(self, f'_last_warning_{user_id}', now)
                        
                        warnings_count = self.spam_warnings[user_id]
                        
                        if warnings_count <= 3:
                            await event.answer("⏱ Не так быстро! Подожди секунду.")
                        elif warnings_count <= 6:
                            await event.answer(
                                "⚠️ Слишком много запросов!\n"
                                "Подожди несколько секунд перед следующим действием."
                            )
                        else:
                            # При частом спаме можем временно игнорировать
                            logger.warning(f"🚨 Пользователь {user_id} превысил лимит спама")
                
                return  # Прерываем обработку — игнорируем запрос
        
        # Обновляем время последнего запроса
        self.user_timers[user_id] = now
        
        # Сбрасываем счётчик предупреждений, если пользователь "успокоился"
        if user_id in self.spam_warnings and self.spam_warnings[user_id] > 0:
            # Уменьшаем счётчик при каждом нормальном запросе
            self.spam_warnings[user_id] = max(0, self.spam_warnings[user_id] - 1)
        
        # Очистка старых записей (старше 2 минут)
        cutoff_time = now - timedelta(minutes=2)
        self.user_timers = {
            uid: time 
            for uid, time in self.user_timers.items() 
            if time > cutoff_time
        }
        
        # Пропускаем запрос к основному обработчику
        return await handler(event, data)
