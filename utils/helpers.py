# Файл: utils/helpers.py
import json
import logging
import os
from datetime import datetime, timedelta, date
from config import DB_FILE, FIRST_GRUPPENRUN_DATE, REFERENCE_GR_DATE, REFERENCE_GR_NUMBER, BREAKFAST_MENU
from utils.database import db

logger = logging.getLogger(__name__)

# --- Функции для работы с JSON-файлом (база данных) ---

def load_data():
    """
    Загружает данные в формате совместимом с остальным кодом
    (Теперь берёт из SQLite вместо JSON через кэширование)
    """
    from utils.cache import data_cache
    return data_cache.get_data(_load_data_from_sqlite)

def _load_data_from_sqlite():
    """Вспомогательная функция для чтения из SQLite"""
    from utils.database import db
    
    all_data = {}
    
    # Загружаем всех пользователей
    users = db.get_all_users()
    
    for user in users:
        user_id = user['user_id']
        
        # Инициализируем пользователя в результате
        all_data[user_id] = {
            "name": user.get("name"),
            "phone": user.get("phone"),
            "username": user.get("username"),
            "bot_version": user.get("bot_version")
        }
        
        # Добавляем Групpenran регистрацию
        gr_reg = db.check_gruppenrun_registration(user_id)
        if gr_reg.get("is_active"):
            all_data[user_id]["gruppenrun"] = {
                "type": gr_reg.get("type"),
                "valid_until": gr_reg.get("valid_until")
            }
        
        # Добавляем Иремель регистрацию
        ir_reg = db.get_iremel_registration(user_id)
        if ir_reg:
            all_data[user_id]["iremel"] = {
                "is_registered": ir_reg.get("is_registered"),
                "waiting_list": ir_reg.get("waiting_list"),
                "payment_type": ir_reg.get("payment_type"),
                "diet_restrictions": ir_reg.get("diet_restrictions"),
                "preferences": ir_reg.get("preferences")
            }
    
    logging.debug(f"✅ load_data: загружены {len(all_data)} пользователей из SQLite")
    return all_data

def save_data(data: dict):
    """
    Сохраняет данные в SQLite (ОБНОВЛЕНО)
    
    Ожидает словарь того же формата как раньше, но теперь сохраняет в БД
    """
    from utils.database import db
    
    for user_id, user_data in data.items():
        try:
            # Сохраняем пользователя
            db.save_user(
                user_id=user_id,
                name=user_data.get("name"),
                phone=user_data.get("phone"),
                username=user_data.get("username"),
                bot_version=user_data.get("bot_version")
            )
            
            # Сохраняем Групpenran
            if "gruppenrun" in user_data:
                gr_data = user_data["gruppenrun"]
                db.save_gruppenrun_registration(
                    user_id=user_id,
                    reg_type=gr_data.get("type", "onetime"),
                    valid_until=gr_data.get("valid_until")
                )
            
            # Сохраняем Иремель
            if "iremel" in user_data:
                ir_data = user_data["iremel"]
                db.save_iremel_registration(
                    user_id=user_id,
                    is_registered=ir_data.get("is_registered", False),
                    waiting_list=ir_data.get("waiting_list", False),
                    payment_type=ir_data.get("payment_type"),
                    diet_restrictions=ir_data.get("diet_restrictions"),
                    preferences=ir_data.get("preferences")
                )
        except Exception as e:
            logging.error(f"❌ Ошибка при сохранении пользователя {user_id}: {e}")
    
    logging.debug(f"💾 save_data: сохранены {len(data)} пользователей в SQLite")
    
    # ✅ ИНВАЛИДИРУЕМ КЭШ ПОСЛЕ СОХРАНЕНИЯ
    from utils.cache import data_cache
    data_cache.invalidate()
    logging.debug("📝 Кэш инвалидирован после сохранения")

# --- Функции для работы с датами и расчётами Группенрана ---

def get_sunday_date(target_date=None):
    """
    Возвращает ближайшее воскресенье от указанной даты.
    Если target_date=None, то от сегодняшней даты.
    """
    if target_date is None:
        target_date = datetime.today().date()
    
    # Количество дней до воскресенья (6 - текущий день недели)
    days_until_sunday = (6 - target_date.weekday()) % 7
    
    return target_date + timedelta(days=days_until_sunday)

def get_next_sunday(from_date=None):
    """
    Возвращает следующее воскресенье в формате строки DD.MM.YYYY.
    Если from_date=None, то от сегодняшней даты.
    
    ВАЖНО: До понедельника 00:00 возвращает текущее воскресенье.
    С понедельника 00:00 - следующее воскресенье.
    """
    if from_date is None:
        from_date = datetime.today().date()
    
    # Если сегодня воскресенье (weekday = 6)
    if from_date.weekday() == 6:
        # Возвращаем сегодняшнее воскресенье
        return from_date.strftime("%d.%m.%Y")
    
    # Для остальных дней недели - ищем следующее воскресенье
    days_ahead = 6 - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    
    return (from_date + timedelta(days=days_ahead)).strftime("%d.%m.%Y")

def get_current_gruppenrun_number(for_date=None):
    """
    Вычисляет номер Группенрана для указанной даты.
    Использует референсную точку для точных расчётов.
    """
    if for_date is None:
        for_date = get_sunday_date(datetime.today().date())
    
    # Референсное воскресенье
    reference_sunday = get_sunday_date(REFERENCE_GR_DATE)
    
    # Разница в неделях
    delta_weeks = (for_date - reference_sunday).days // 7
    
    # Текущий номер Группенрана
    current_gr_number = REFERENCE_GR_NUMBER + delta_weeks
    return current_gr_number

def get_next_saturday():
    """Возвращает дату следующей субботы"""
    today = datetime.now().date()
    days_until_saturday = (5 - today.weekday()) % 7  # 5 = суббота
    if days_until_saturday == 0:
        days_until_saturday = 7
    next_saturday = today + timedelta(days=days_until_saturday)
    return next_saturday


def get_current_uktus_number():
    """
    Вычисляет текущий номер Группенран Трейл на основе эталонной даты.
    Тренировки проходят каждую субботу.
    """
    from config import REFERENCE_UKTUS_DATE, REFERENCE_UKTUS_NUMBER
    
    next_saturday = get_next_saturday()
    weeks_passed = (next_saturday - REFERENCE_UKTUS_DATE).days // 7
    current_number = REFERENCE_UKTUS_NUMBER + weeks_passed
    
    return current_number

# --- Функции для работы с пользователями ---

def get_user_profile(user_id, all_data):
    """Получает профиль пользователя из базы данных"""
    user_data = all_data.get(str(user_id), {})
    
    if not user_data.get("name") or not user_data.get("phone"):
        return None
    
    return {
        "name": user_data.get("name"),
        "phone": user_data.get("phone"),
        "username": user_data.get("username")
    }

def save_user_profile(user_id, name, phone, username, all_data):
    """Сохраняет или обновляет профиль пользователя"""
    user_id_str = str(user_id)
    
    if user_id_str not in all_data:
        all_data[user_id_str] = {}
    
    all_data[user_id_str].update({
        "name": name,
        "phone": phone,
        "username": username
    })
    
    save_data(all_data)
    return all_data[user_id_str]

def check_gruppenrun_registration(user_id, all_data):
    """Проверяет регистрацию пользователя на Группенран"""
    user_data = all_data.get(user_id, {})
    gruppenrun_data = user_data.get("gruppenrun", {})
    
    if not gruppenrun_data.get("is_registered"):
        return {"is_active": False, "type": None}
    
    reg_type = gruppenrun_data.get("type", "onetime")
    
    if reg_type == "monthly":
        valid_until = gruppenrun_data.get("valid_until")
        if valid_until:
            try:
                valid_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
                if datetime.now().date() <= valid_date:
                    return {
                        "is_active": True,
                        "type": "monthly",
                        "details": f"Месячный абонемент (до {valid_date.strftime('%d.%m.%Y')})"
                    }
            except:
                pass
    else:  # onetime
        reg_date = gruppenrun_data.get("registration_for_date")
        next_gruppenrun_date_str = get_next_sunday()
        
        if reg_date == next_gruppenrun_date_str:
            return {
                "is_active": True,
                "type": "onetime",
                "details": f"Разовая регистрация на {reg_date}"
            }
        else:
            # АВТООЧИСТКА: Если дата регистрации прошла - очищаем регистрацию И завтрак
            if "gruppenrun" in all_data[user_id]:
                all_data[user_id]["gruppenrun"]["is_registered"] = False
            if "breakfast_order" in all_data[user_id]:
                del all_data[user_id]["breakfast_order"]
            save_data(all_data)
    
    return {"is_active": False, "type": None}

def check_krugosvetka_registration(user_id, all_data):
    """Проверяет активную регистрацию на Кругосветку"""
    user_data = all_data.get(str(user_id), {})
    krugosvetka_data = user_data.get("krugosvetka", {})
    
    return krugosvetka_data.get("is_registered", False)

# --- Вспомогательные функции ---

def escape_markdown(text):
    """Экранирует специальные символы для MarkdownV2"""
    if text is None:
        return ""
    
    escape_chars = ['\\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

def format_user_info_for_admin(user_data, reg_data=None):
    """Форматирует информацию о пользователе для отправки админу"""
    name = escape_markdown(user_data.get("name", "Не указано"))
    phone = escape_markdown(user_data.get("phone", "Не указано"))
    username = escape_markdown(user_data.get("username", "Не указан"))
    
    info_parts = [
        f"👤 Имя: {name}",
        f"📱 Телефон: {phone}",
        f"💬 Telegram: @{username}" if username != "Не указан" else f"💬 Telegram: {username}"
    ]
    
    if reg_data:
        if reg_data.get("selected_stages_text"):
            stages = escape_markdown(reg_data.get("selected_stages_text", ""))
            info_parts.append(f"🏃 Этапы: {stages}")
        if reg_data.get("pace"):
            pace = escape_markdown(reg_data.get("pace", ""))
            info_parts.append(f"⏱️ Темп: {pace}")
    
    return "\n".join(info_parts)

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАВТРАКАМИ ===

def get_user_breakfast_order(user_id, all_data):
    """Получает текущий заказ завтрака пользователя"""
    user_data = all_data.get(str(user_id), {})
    return user_data.get("breakfast_order", {})

def save_user_breakfast_order(user_id, breakfast_items, all_data):
    """Сохраняет заказ завтрака пользователя"""
    user_id_str = str(user_id)
    
    if user_id_str not in all_data:
        all_data[user_id_str] = {}
    
    # Подсчитываем total_price внутри функции
    total_price = 0
    for item_id, count in breakfast_items.items():
        price = BREAKFAST_MENU.get(item_id, {}).get("price", 0)
        total_price += price * count
    
    all_data[user_id_str]["breakfast_order"] = {
        "items": breakfast_items,
        "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": total_price
    }
    
    save_data(all_data)
    return all_data[user_id_str]["breakfast_order"]

def clear_user_breakfast_order(user_id, all_data):
    """Очищает заказ завтрака пользователя"""
    user_id_str = str(user_id)
    
    if user_id_str in all_data and "breakfast_order" in all_data[user_id_str]:
        del all_data[user_id_str]["breakfast_order"]
        save_data(all_data)
        return True
    return False

def can_user_order_breakfast(user_id, all_data):
    """
    Проверяет, может ли пользователь заказать завтрак
    """
    registration_status = check_gruppenrun_registration(user_id, all_data)
    existing_order = get_user_breakfast_order(user_id, all_data)
    
    # Если нет активной регистрации - нельзя заказать
    if not registration_status["is_active"]:
        return {
            "can_order": False,
            "reason": "no_active_registration", 
            "existing_order": existing_order
        }
    
    # Если есть активная регистрация - можно заказывать
    return {
        "can_order": True,
        "reason": "has_active_registration",
        "existing_order": existing_order
    }

# === ФУНКЦИЯ ДЛЯ ОЧИСТКИ ИСТЁКШИХ РЕГИСТРАЦИЙ ===

def cleanup_expired_onetime_registrations(all_data):
    """
    Очищает истёкшие разовые регистрации и заказы завтраков
    Вызывается при каждой проверке регистрации
    """
    data_changed = False
    current_date = date.today()
    
    for user_id, user_info in all_data.items():
        gruppenrun_data = user_info.get("gruppenrun", {})
        
        if gruppenrun_data.get("is_registered", False):
            reg_type = gruppenrun_data.get("type", "onetime")
            
            # Обработка разовых регистраций
            if reg_type == "onetime":
                reg_date_str = gruppenrun_data.get("registration_for_date")
                if reg_date_str:
                    try:
                        reg_date = datetime.strptime(reg_date_str, "%d.%m.%Y").date()
                        
                        # Если дата Группенрана прошла (сегодня понедельник или позже после воскресенья)
                        days_since_gruppenrun = (current_date - reg_date).days
                        
                        # Очищаем регистрацию, если прошло больше суток после даты мероприятия
                        if days_since_gruppenrun >= 1:
                            logging.info(f"Очистка истёкшей разовой регистрации для пользователя {user_id} (дата: {reg_date_str})")
                            
                            # Очищаем регистрацию на Группенран
                            user_info["gruppenrun"]["is_registered"] = False
                            user_info["gruppenrun"]["registration_for_date"] = None
                            user_info["gruppenrun"]["gruppenrun_number"] = None
                            
                            # Очищаем заказ завтраков, связанный с этой регистрацией
                            if "breakfast_order" in user_info:
                                logging.info(f"Очистка заказа завтрака для пользователя {user_id}")
                                del user_info["breakfast_order"]
                            
                            data_changed = True
                    except ValueError:
                        logging.warning(f"Неверный формат даты регистрации для пользователя {user_id}: {reg_date_str}")
                        
            # Обработка месячных абонементов
            elif reg_type == "monthly":
                valid_until_str = gruppenrun_data.get("valid_until")
                if valid_until_str:
                    try:
                        valid_until_date = datetime.strptime(valid_until_str, "%Y-%m-%d").date()
                        if current_date > valid_until_date:
                            logging.info(f"Очистка истёкшего месячного абонемента для пользователя {user_id}")
                            user_info["gruppenrun"]["is_registered"] = False
                            user_info["gruppenrun"]["valid_until"] = None
                            data_changed = True
                    except ValueError:
                        logging.warning(f"Неверный формат даты valid_until для пользователя {user_id}: {valid_until_str}")
    
    if data_changed:
        save_data(all_data)
        logging.info("База данных обновлена - удалены истёкшие регистрации")
    
    return all_data

async def delete_last_admin_message(message, state, bot):
    """Удаляет последнее сообщение админ-панели"""
    data = await state.get_data()
    last_admin_message_id = data.get("last_admin_message_id")
    
    if last_admin_message_id:
        try:
            await bot.delete_message(message.chat.id, last_admin_message_id)
        except Exception:
            pass  # Игнорируем ошибки (сообщение уже удалено или недоступно)


async def save_admin_message_id(state, message_id):
    """Сохраняет ID последнего сообщения админ-панели"""
    await state.update_data(last_admin_message_id=message_id)

def format_profile_display(user_id):
    """
    Форматирует отображение профиля пользователя с датой и номером ГР
    Разные номера для Шарташа и Трейла
    """
    from utils.database import db
    from config import (
        REFERENCE_GR_DATE, REFERENCE_GR_NUMBER,
        REFERENCE_TRAIL_DATE, REFERENCE_TRAIL_NUMBER
    )
    from datetime import date, timedelta
    
    user_data = db.get_user(user_id)
    if not user_data:
        return "❌ Профиль не найден"
    
    profile_text = "👤 МОЙ ПРОФИЛЬ\n"
    profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    profile_text += "📌 ДАННЫЕ\n"
    profile_text += f"• Имя: {user_data.get('name', 'Не указано')}\n"
    profile_text += f"• Номер: {user_data.get('phone', 'Не указано')}\n"
    profile_text += "\n"
    
    def get_next_gr_number_and_date(ref_date, ref_number, target_weekday):
        """
        Вычисляет номер и дату следующего ГР
        target_weekday: 6 = воскресенье (Шарташ), 4 = пятница (Трейл)
        """
        try:
            today = date.today()
            
            # Находим следующий день недели
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0:  # День уже произошел на этой неделе
                days_ahead += 7
            
            next_event = today + timedelta(days=days_ahead)
            
            # Вычисляем номер
            weeks_diff = (next_event - ref_date).days // 7
            event_number = ref_number + weeks_diff
            event_date = next_event.strftime('%d.%m.%Y')
            
            return event_number, event_date
        except Exception as e:
            logger.error(f"Ошибка при вычислении номера: {e}")
            return None, None
    
    # 2. ГРУППЕНРАН ШАРТАШ (воскресенье = 6)
    shartas_reg = db.check_gruppenrun_registration(user_id, location='shartas')
    if shartas_reg and shartas_reg.get('is_active'):
        gr_num, gr_date = get_next_gr_number_and_date(REFERENCE_GR_DATE, REFERENCE_GR_NUMBER, 6)
        profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        profile_text += "⛰️ ГРУППЕНРАН ШАРТАШ\n"
        if gr_num and gr_date:
            profile_text += f"🔢 №{gr_num} | 📅 {gr_date}\n"
        reg_type = shartas_reg.get('type')
        if reg_type == 'monthly':
            profile_text += "📅 Тип: Месячный абонемент\n"
            profile_text += f"⏰ Действителен до: {shartas_reg.get('valid_until')}\n"
        else:
            profile_text += "📅 Тип: Разовое посещение (200₽)\n"
        profile_text += "✅ Оплачено\n"
        profile_text += "\n"
    
    # 3. ГРУППЕНРАН ТРЕЙЛ (пятница = 4)
    uktus_reg = db.check_gruppenrun_registration(user_id, location='uktus')
    if uktus_reg and uktus_reg.get('is_active'):
        trail_num, trail_date = get_next_gr_number_and_date(REFERENCE_TRAIL_DATE, REFERENCE_TRAIL_NUMBER, 4)
        profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        profile_text += "⛰️ ГРУППЕНРАН ТРЕЙЛ (УКТУС)\n"
        if trail_num and trail_date:
            profile_text += f"🔢 №{trail_num} | 📅 {trail_date}\n"
        reg_type = uktus_reg.get('type')
        if reg_type == 'monthly':
            profile_text += "📅 Тип: Месячный абонемент\n"
            profile_text += f"⏰ Действителен до: {uktus_reg.get('valid_until')}\n"
        else:
            profile_text += "📅 Тип: Разовое посещение (300₽)\n"
        profile_text += "✅ Оплачено\n"
        profile_text += "\n"
    
    # 4. ИРЕМЕЛЬ КЭМП
    iremel_reg = db.get_iremel_registration(user_id)
    if iremel_reg and iremel_reg.get('is_registered'):
        profile_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        profile_text += "🏔 ИРЕМЕЛЬ КЭМП 2025\n"
        payment = iremel_reg.get('payment_type', 'Не указана')
        if payment == '50':
            profile_text += "💰 Оплата: 50%\n"
        elif payment == '100':
            profile_text += "💰 Оплата: 100%\n"
        profile_text += "✅ Зарегистрирован\n"
    
    return profile_text.strip()
