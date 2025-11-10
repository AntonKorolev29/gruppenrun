from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import types
from typing import Callable, Dict, Any, Awaitable
from config import BOT_VERSION
from utils.helpers import load_data, save_data

class VersionCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = str(event.from_user.id)
        all_data = load_data()
        user_data = all_data.get(user_id, {})
        
        # Проверяем версию пользователя
        user_version = user_data.get("bot_version", "0.0.0")
        
        if user_version != BOT_VERSION:
            # Обновляем версию и сбрасываем состояние
            state = data.get("state")
            if state:
                await state.clear()
            
            # Сохраняем новую версию
            if user_id not in all_data:
                all_data[user_id] = {}
            all_data[user_id]["bot_version"] = BOT_VERSION
            save_data(all_data)
            
            # Отправляем уведомление пользователю
            if isinstance(event, Message):
                await event.answer(
                    "🔄 Бот был обновлён!\n\n"
                    "Все функции теперь работают корректно. "
                    "Используй команду /start для продолжения работы.",
                    reply_markup=types.ReplyKeyboardRemove()
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("🔄 Бот обновлён! Используй /start", show_alert=True)
            
            return  # Прерываем обработку
        
        # Если версия совпадает - продолжаем обработку
        return await handler(event, data)
