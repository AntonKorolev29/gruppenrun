import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

# Импорт конфига и логирования
from config import API_TOKEN, ADMIN_ID, BOT_VERSION
from handlers import common, gruppenrun, gruppenrun_uktus, krugosvetka, breakfast, iremel, fallback
from middlewares.version_check import VersionCheckMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from utils.helpers import load_data, save_data, cleanup_expired_onetime_registrations

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные
bot: Bot = None
dp: Dispatcher = None
storage: MemoryStorage = None

async def on_startup(dp):
    """Выполняется при запуске бота"""
    logger.info("Бот запущен. Выполняю очистку истёкших регистраций...")
    
    from utils.database import db
    from datetime import datetime
    
    # ===== ОЧИСТКА ШАРТАШ =====
    all_data = load_data()
    cleanup_expired_onetime_registrations(all_data)
    
    # ===== ОЧИСТКА ТРЕЙЛ =====
    # Очистка в воскресенье 00:00 (после субботней тренировки)
    today = datetime.now()
    if today.weekday() == 6:  # 6 = Воскресенье
        logger.info("🗑️ Очистка регистраций Трейл...")
    
        all_users = db.get_all_users()
        for user in all_users:
            user_id = user['user_id']
            reg = db.check_gruppenrun_registration(user_id, location='uktus')
        
            if reg.get('is_active') and reg.get('type') == 'onetime':
                db.unregister_gruppenrun(user_id, location='uktus')
                logger.info(f"🗑️ Трейл: {user_id} - регистрация удалена")

# ==================== ЕЖЕДНЕВНЫЙ ОТЧЁТ ====================

async def send_daily_report(bot: Bot):
    """Отправляет ежедневный отчёт админу в 9:00"""
    import asyncio
    from datetime import datetime, time
    from utils.analytics import analytics
    
    while True:
        try:
            now = datetime.now()
            target_time = time(9, 0)  # 9:00 утра
            
            # Если текущее время после 9:00, отправляем
            if now.time() >= target_time:
                report = analytics.get_stats_report()
                await bot.send_message(ADMIN_ID, report, parse_mode="HTML")
                logger.info("📊 Ежедневный отчёт отправлен админу")
                
                # Ждём 24 часа до следующего отчёта
                await asyncio.sleep(86400)
            else:
                # Ждём 1 час и проверим снова
                await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке отчёта: {e}")
            # Ждём 1 час и попробуем снова
            await asyncio.sleep(3600)

# ===== ФУНКЦИЯ ОЧИСТКИ ТРЕЙЛ =====
async def clear_uktus_registrations():
    """Очищает разовые регистрации Трейл в воскресенье 00:00"""
    import sqlite3
    logger.info("🗑️ Очистка регистраций Трейл...")
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Удаляем разовые регистрации
    cursor.execute("DELETE FROM gruppenrun_registrations WHERE location = 'uktus' AND type = 'onetime'")
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"Очистка Трейл завершена. Удалено: {deleted}")

async def main():
    """Основная функция бота"""
    global bot, dp, storage
    
    logger.info("Запуск бота...")
    
    # Инициализация хранилища FSM
    storage = MemoryStorage()
    
    # Создание объектов бота и диспетчера
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Подключение middleware
    dp.message.middleware(VersionCheckMiddleware())
    dp.callback_query.middleware(VersionCheckMiddleware())
    
    # ✅ Rate Limiting - защита от спама
    dp.message.middleware(RateLimitMiddleware(rate_limit=0.5))
    dp.callback_query.middleware(RateLimitMiddleware(rate_limit=0.3))
    
    # Подключение обработчика ошибок
    @dp.error()
    async def error_handler(event: ErrorEvent):
        """Глобальный обработчик ошибок"""
        
        # Логируем ошибку
        logger.error(f"❌ Ошибка в боте: {event.exception}", exc_info=True)
        
        # Формируем сообщение об ошибке
        error_msg = (
            f"⚠️ <b>Ошибка в боте</b>\n\n"
            f"<b>Тип:</b> {type(event.exception).__name__}\n"
            f"<b>Сообщение:</b> {str(event.exception)}\n\n"
            f"<code>{traceback.format_exc()[-500:]}</code>"  # Последние 500 символов traceback
        )
        
        # Отправляем админу уведомление
        try:
            if event.update and event.update.message:
                await event.update.message.reply(error_msg, parse_mode="HTML")
            elif event.update:
                await event.update.bot.send_message(
                    ADMIN_ID,
                    error_msg,
                    parse_mode="HTML"
                )
            else:
                logger.error(f"⚠️ Не удалось отправить уведомление: event.update = None")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления админу: {e}")
    
    # Подключение роутеров (наших "модулей" с обработчиками)
    dp.include_router(common.router)
    dp.include_router(gruppenrun.router)
    dp.include_router(gruppenrun_uktus.router)
    dp.include_router(krugosvetka.router)
    dp.include_router(breakfast.router)
    dp.include_router(iremel.router)
    dp.include_router(fallback.router)
    
    # Удаление webhook (на случай, если использовался ранее)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Проверяем подключение к Telegram API
    try:
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username}")
        logger.info(f"Имя бота: {bot_info.first_name}")
    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram API: {e}")
        return
    
    # ✅ ВЫЗЫВАЕМ ОЧИСТКУ ПРИ СТАРТЕ
    await on_startup(dp)
    
    # ✅ Запускаем отправку ежедневного отчёта в фоне
    asyncio.create_task(send_daily_report(bot))  
    logger.info("📊 Система ежедневных отчётов запущена")

    # Запуск поллинга (бесконечное получение обновлений)
    try:
        logger.info("Начинаем получение обновлений...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершаем работу...")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        logger.info("Закрываем соединение с ботом...")
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    """Точка входа в программу"""
    try:
        # Запуск асинхронной функции
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
