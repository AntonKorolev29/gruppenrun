#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт миграции данных из JSON в SQLite БД
Используй: python3 migrate_to_sqlite.py
"""

import json
import logging
import sys
from datetime import datetime
from utils.database import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_from_json():
    """Миграция данных из registrations_db.json в SQLite"""
    
    logger.info("=" * 60)
    logger.info("🔄 НАЧАЛО МИГРАЦИИ ДАННЫХ ИЗ JSON В SQLITE")
    logger.info("=" * 60)
    
    # Загружаем данные из JSON
    try:
        with open("registrations_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"✅ Загружен файл registrations_db.json ({len(data)} пользователей)")
    except FileNotFoundError:
        logger.error("❌ Файл registrations_db.json не найден!")
        logger.info("📌 Убедись, что скрипт запущен из папки /root/gruppenrun_bot/")
        return False
    except json.JSONDecodeError:
        logger.error("❌ Ошибка при чтении JSON файла (повреждённый формат)")
        return False
    
    # Счётчики
    migrated_users = 0
    migrated_gruppenrun = 0
    migrated_iremel = 0
    errors = 0
    
    logger.info(f"\n📝 Начинаю миграцию {len(data)} пользователей...\n")
    
    for user_id, user_data in data.items():
        try:
            # ✅ Мигрируем пользователя
            db.save_user(
                user_id=user_id,
                name=user_data.get("name"),
                phone=user_data.get("phone"),
                username=user_data.get("username"),
                bot_version=user_data.get("bot_version", "1.0.0")
            )
            migrated_users += 1
            
            # ✅ Мигрируем Группенран (если есть)
            if "gruppenrun" in user_data and user_data["gruppenrun"]:
                try:
                    gr_data = user_data["gruppenrun"]
                    db.save_gruppenrun_registration(
                        user_id=user_id,
                        reg_type=gr_data.get("type", "onetime"),
                        valid_until=gr_data.get("valid_until")
                    )
                    migrated_gruppenrun += 1
                    logger.debug(f"  ✓ Групpenrun: {user_id}")
                except Exception as e:
                    logger.warning(f"  ⚠ Ошибка Групpenrun для {user_id}: {e}")
            
            # ✅ Мигрируем Иремель (если есть)
            if "iremel" in user_data and user_data["iremel"]:
                try:
                    ir_data = user_data["iremel"]
                    db.save_iremel_registration(
                        user_id=user_id,
                        is_registered=ir_data.get("is_registered", False),
                        waiting_list=ir_data.get("waiting_list", False),
                        payment_type=ir_data.get("payment_type"),
                        diet_restrictions=ir_data.get("diet_restrictions"),
                        preferences=ir_data.get("preferences")
                    )
                    migrated_iremel += 1
                    logger.debug(f"  ✓ Иремель: {user_id}")
                except Exception as e:
                    logger.warning(f"  ⚠ Ошибка Иремель для {user_id}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка миграции пользователя {user_id}: {e}")
            errors += 1
    
    # Итоги миграции
    logger.info("\n" + "=" * 60)
    logger.info("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    logger.info("=" * 60)
    logger.info(f"""
📊 РЕЗУЛЬТАТЫ:
   • Всего пользователей: {migrated_users}
   • Регистраций Групpenран: {migrated_gruppenrun}
   • Регистраций Иремель: {migrated_iremel}
   • Ошибок: {errors}
   
📁 Новые файлы:
   • bot_data.db (SQLite база данных)
   • registrations_db.json (оригинальный файл, сохранён)
    """)
    
    if errors == 0:
        logger.info("✅ Миграция прошла успешно без ошибок!")
        return True
    else:
        logger.warning(f"⚠️ Миграция завершена с {errors} ошибками. Проверь логи выше.")
        return False


if __name__ == "__main__":
    try:
        success = migrate_from_json()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
