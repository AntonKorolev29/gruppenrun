# Файл: utils/analytics.py
# -*- coding: utf-8 -*-

"""
Система аналитики и мониторинга бота
"""

import logging
import json
from datetime import datetime, date
from utils.database import db

logger = logging.getLogger(__name__)


class Analytics:
    """Класс для работы с аналитикой бота"""
    
    @staticmethod
    def track_button_click(user_id: str, button_name: str, context: dict = None):
        """Отследить клик на кнопку"""
        try:
            db.track_event(
                user_id=str(user_id),
                event_name=f"button:{button_name}",
                event_data={"button": button_name, **(context or {})}
            )
            logger.info(f"🔘 Клик на кнопку '{button_name}' от {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отслеживании клика: {e}")
    
    @staticmethod
    def track_registration(user_id: str, service: str):
        """Отследить регистрацию"""
        try:
            db.track_event(
                user_id=str(user_id),
                event_name=f"registration:{service}",
                event_data={"service": service}
            )
            logger.info(f"📝 Регистрация на {service} от {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отслеживании регистрации: {e}")
    
    @staticmethod
    def track_command(user_id: str, command: str):
        """Отследить команду"""
        try:
            db.track_event(
                user_id=str(user_id),
                event_name=f"command:{command}",
                event_data={"command": command}
            )
            logger.info(f"⚙️ Команда /{command} от {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отслеживании команды: {e}")
    
    @staticmethod
    def get_stats_report() -> str:
        """Получить красиво отформатированный отчёт"""
        try:
            stats = db.get_daily_stats()
            popular = db.get_popular_events(limit=5)
            
            report = (
                f"📊 <b>ЕЖЕДНЕВНЫЙ ОТЧЁТ БОТА</b>\n"
                f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"👥 <b>Пользователи:</b>\n"
                f"  • Новых сегодня: <b>{stats.get('new_users', 0)}</b>\n"
                f"  • Всего в системе: <b>{stats.get('total_users', 0)}</b>\n\n"
                f"📝 <b>Регистрации сегодня:</b>\n"
                f"  • Групpenран: <b>{stats.get('gruppenrun_regs', 0)}</b>\n"
                f"  • Иремель: <b>{stats.get('iremel_regs', 0)}</b>\n\n"
                f"🔝 <b>Популярные события:</b>\n"
            )
            
            if popular:
                for event, count in sorted(popular.items(), key=lambda x: x[1], reverse=True)[:5]:
                    # Красивое имя события
                    event_name = event.replace("button:", "🔘 ").replace("registration:", "📝 ").replace("command:", "⚙️ ")
                    report += f"  • {event_name}: <b>{count}</b>\n"
            else:
                report += "  • События не отслеживались\n"
            
            report += f"\n✅ <i>Сгенерировано автоматически</i>"
            
            return report
        except Exception as e:
            logger.error(f"Ошибка при формировании отчёта: {e}")
            return f"❌ Ошибка при генерации отчёта: {e}"


# Глобальный экземпляр
analytics = Analytics()
