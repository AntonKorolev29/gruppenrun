from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from keyboards.reply import main_kb, admin_kb, back_kb, phone_kb, payment_kb, admin_panel_kb
from states.registration import FeedbackState, ProfileFillState
from utils.helpers import (
    get_next_sunday,
    get_current_gruppenrun_number,
    get_next_saturday,
    get_current_uktus_number,
    load_data,
    get_user_profile,
    check_gruppenrun_registration,
    check_krugosvetka_registration,
    escape_markdown,
    can_user_order_breakfast,
    save_data,
    delete_last_admin_message,
    save_admin_message_id
)

from config import ADMIN_ID, BREAKFAST_MENU, PHOTO_HOW_TO_GET_COVER, IREMEL_MAX_PARTICIPANTS
from utils.analytics import analytics

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    username = message.from_user.first_name or "участник"
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    next_uktus_date = get_next_saturday()
    next_uktus_number = get_current_uktus_number()
    next_uktus_date_str = next_uktus_date.strftime("%d.%m.%Y")
    
    welcome_text = (
        f"👋 Привет, {username}!\n"
        f"Это Бот бегового сообщества Группенран.\n"
        f"Здесь ты можешь зарегистрироваться на наши регулярные пробежки на Шарташе и Уктусе, "
        f"а так же на другие наши мероприятия и события.\n\n"
        f" Наши направления:\n"
        f"⛰️ Группенран Трейл\n"
        f"Трейловые тренировки на Уктусе по субботам\n"
        f"Следующий: №{next_uktus_number}, {next_uktus_date_str}\n\n"
        f"🏃 Группенран Шарташ\n"
        f"Классические длительные пробежки по воскресеньям\n"
        f"Следующий: №{next_gruppenrun_number}, {next_gruppenrun_date_str}\n\n"
        f"Специальные события:\n"
        f"🏔 \"Иремель Кэмп 2025\", 28-30 ноября 2025\n"
        f"❄️ \"Шарташская Карусель 2026\", 1-2 января 2026"
    )
    
    # Проверяем, админ ли пользователь
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer(welcome_text, reply_markup=admin_kb)
    else:
        await message.answer(welcome_text, reply_markup=main_kb)
    
    analytics.track_command(message.from_user.id, "start")

@router.message(F.text == "👤 Мой профиль", StateFilter(None))
async def show_profile(message: types.Message, state: FSMContext):
    """Отображает профиль пользователя с новой структурой"""
    from utils.helpers import format_profile_display
    
    user_id = str(message.from_user.id)
    all_data = load_data()
    profile = get_user_profile(user_id, all_data)
    
    if not profile or not profile.get("name"):
        await message.answer(
            "Пожалуйста, введи своё полное имя (фамилия и имя):",
            reply_markup=back_kb
        )
        await state.set_state(ProfileFillState.waiting_for_fullname)
        return
    
    # ✅ ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ С РАЗДЕЛЕНИЕМ ПО ЛОКАЦИИ
    profile_text = format_profile_display(user_id)
    
    await message.answer(profile_text, parse_mode="HTML")


@router.message(ProfileFillState.waiting_for_fullname)
async def process_fullname(message: types.Message, state: FSMContext):
    fullname = message.text.strip()
    if len(fullname.split()) < 2:
        await message.answer("Пожалуйста, введите полное имя, включая фамилию и имя.")
        return
    
    await state.update_data(fullname=fullname)
    await message.answer(
        "Спасибо! Теперь нажмите кнопку ниже, чтобы отправить ваш номер телефона:",
        reply_markup=phone_kb
    )
    await state.set_state(ProfileFillState.waiting_for_phone)

@router.message(ProfileFillState.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"
    
    data = await state.get_data()
    fullname = data.get("fullname")
    user_id = str(message.from_user.id)
    all_data = load_data()
    
    if user_id not in all_data:
        all_data[user_id] = {}
    
    all_data[user_id]["name"] = fullname
    all_data[user_id]["phone"] = phone
    all_data[user_id]["username"] = message.from_user.username
    save_data(all_data)
    
    await message.answer(
        f"Ваш профиль сохранён:\n\nИмя: {fullname}\nТелефон: {phone}",
        reply_markup=main_kb
    )
    await state.clear()

@router.message(ProfileFillState.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, нажмите кнопку \"📱 Отправить номер телефона\" для отправки номера.",
        reply_markup=phone_kb
    )

@router.message(F.text == "💬 Обратная связь", StateFilter(None))
async def feedback_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Напишите ваше сообщение, предложение или вопрос. "
        "Также можете написать напрямую организатору: @AntonKorolev29",
        reply_markup=back_kb
    )
    await state.set_state(FeedbackState.waiting_for_message)

@router.message(FeedbackState.waiting_for_message)
async def process_feedback(message: types.Message, state: FSMContext):
    """Обработка сообщения обратной связи"""
    
    # Если нажал "Назад" - выход без отправки
    if message.text == "⬅️ Назад":
        await state.clear()
        if str(message.from_user.id) == str(ADMIN_ID):
            await message.answer("Главное меню:", reply_markup=admin_kb)
        else:
            await message.answer("Главное меню:", reply_markup=main_kb)
        return
    
    try:
        user_info_str = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        feedback_text = f"💬 Обратная связь:\n{message.text}"
        full_message = f"{user_info_str}\n\n{feedback_text}"
        
        await message.bot.send_message(chat_id=ADMIN_ID, text=full_message)
        await message.answer("Спасибо! Ваше сообщение отправлено.", reply_markup=main_kb)
    except Exception:
        await message.answer("Произошла ошибка при отправке сообщения. Попробуйте позже.", reply_markup=main_kb)
    finally:
        await state.clear()

@router.message(F.text == "📍 Как добраться", StateFilter(None))
async def how_to_get(message: types.Message):
    """Обработчик кнопки 'Как добраться'"""
    text = (
        "📍 КАК ДОБРАТЬСЯ\n\n"
        "⛰️ ГРУППЕНРАН ТРЕЙЛ - СУББОТА\n"
        "ГЛК Уктус, гриль-парк «Белкино»\n"
        "ул. Зимняя 27, Екатеринбург\n"
        "Координаты: 56.774588, 60.645524\n"
        "🔗 https://yandex.ru/maps/-/CLvo6WOR\n\n"
        
        "🚌 Общественный транспорт:\n"
        "От остановки Уктус — 15 минут пешком\n\n"
        
        "💳 Платная парковка горнолыжного комплекса\n"
        "🚗 Либо машину можно оставить у шлагбаума у лесной дороги\n\n"
        
        "─────────────────────────────\n\n"
        
        "🏃 ГРУППЕНРАН ШАРТАШ - ВОСКРЕСЕНЬЕ\n"
        "Парк Шарташские Каменные палатки\n"
        "База: оз. Шарташ, «Мыс Рундук», ул. Отдыха 25\n\n"
        
        "🚌 На общественном транспорте:\n"
        "Остановка Дачная, от неё ~1 км пешком\n\n"
        
        "🚗 На машине:\n"
        "Парковка на территории базы и рядом с ней\n\n"
        
        "⏱️ Рекомендуем приходить за 15–20 минут до старта"
    )
    
    # Кнопки со ссылками на карты
    location_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗺 Уктус на Яндекс Картах",
            url="https://yandex.ru/maps/-/CLvo6WOR"
        )],
        [InlineKeyboardButton(
            text="🗺 Шарташ на Яндекс Картах",
            url="https://yandex.ru/maps/54/yekaterinburg/?ll=60.691136%2C56.865335&mode=poi&poi%5Bpoint%5D=60.691830%2C56.865204&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D1321450878&z=18.36"
        )]
    ])
    
    try:
        await message.answer_photo(
            photo=PHOTO_HOW_TO_GET_COVER,
            caption=text,
            reply_markup=location_keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка загрузки обложки 'Как добраться': {e}")
        await message.answer(text, reply_markup=location_keyboard, parse_mode="HTML")

    # Отправляем локации
    await message.answer_location(latitude=56.865204, longitude=60.691830)  # Шарташ
    await message.answer_location(latitude=56.774588, longitude=60.645524)  # Уктус


@router.message(F.photo)
async def get_photo_file_id(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.reply(f"📸 ID фотографии:\n\n`{file_id}`\n\nСкопируй этот ID в config.py")

# ===== АДМИНСКИЕ КОМАНДЫ =====

@router.message(Command("registrations"))
async def show_registrations(message: types.Message):
    """Показывает списки регистраций (только для админа)"""
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("❌ Эта команда доступна только администратору.")
        return
    
    all_data = load_data()
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    
    # ===== ГРУППЕНРАН ШАРТАШ =====
    gruppenrun_shartas_list = []
    for user_id, user_data in all_data.items():
        gruppenrun_data = user_data.get("gruppenrun", {})
        if gruppenrun_data.get("is_registered"):
            reg_type = gruppenrun_data.get("type", "onetime")
            is_active = False
        
            if reg_type == "monthly":
                valid_until = gruppenrun_data.get("valid_until")
                if valid_until:
                    try:
                        valid_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
                        if datetime.now().date() <= valid_date:
                            is_active = True
                    except:
                        pass
            else:  # onetime
                reg_date = gruppenrun_data.get("registration_for_date")
                if reg_date == next_gruppenrun_date_str:
                    is_active = True
        
            if is_active:
                name = user_data.get("name", "Неизвестно")
                phone = user_data.get("phone", "Нет")
                username = user_data.get("username", "Нет")
                gruppenrun_shartas_list.append(f"{name} | @{username} | {phone}")

    # ===== ГРУППЕНРАН ТРЕЙЛ =====
    from utils.database import db
    gruppenrun_uktus_list = []
    all_users = db.get_all_users()

    # Дата следующей тренировки Трейл (вручную или из конфига)
    next_uktus_date = get_next_saturday()
    next_uktus_number = get_current_uktus_number()
    next_uktus_date_str = next_uktus_date.strftime("%d.%m.%Y")

    for user in all_users:
        user_id = user['user_id']
        reg = db.check_gruppenrun_registration(user_id, location='uktus')
        if reg.get('is_active'):
            name = user.get('name', 'Неизвестно')
            phone = user.get('phone', 'Нет')
            username = user.get('username', 'Нет')
            gruppenrun_uktus_list.append(f"{name} | @{username} | {phone}")
 
    # ===== КРУГОСВЕТКА =====
    krugosvetka_list = []
    
    for user_id, user_data in all_data.items():
        krugosvetka_data = user_data.get("krugosvetka", {})
        
        if krugosvetka_data.get("is_registered"):
            name = user_data.get("name", "Неизвестно")
            phone = user_data.get("phone", "Нет")
            username = user_data.get("username", "Нет")
            pace = krugosvetka_data.get("pace", "Нет")
            
            # Формируем этапы
            stages_ids = krugosvetka_data.get("stages_ids", [])
            
            if "all_stages" in stages_ids:
                stages_text = "Весь круг"
            else:
                # Извлекаем только номера этапов (1, 2, 3...)
                stage_numbers = []
                for stage_id in stages_ids:
                    if stage_id.startswith("stage_"):
                        stage_num = stage_id.replace("stage_", "")
                        stage_numbers.append(stage_num)
                
                stages_text = ", ".join(sorted(stage_numbers))
            
            krugosvetka_list.append(f"{name} | Этапы: {stages_text} | Темп: {pace} | @{username}")
    
   # ===== ФОРМИРУЕМ ОТВЕТ =====
    response = f"📊 РЕГИСТРАЦИИ\n\n"

    # Группенран Шарташ
    response += f"⚪ Группенран Шарташ №{next_gruppenrun_number}             ({next_gruppenrun_date_str})\n"
    response += f"Всего участников: {len(gruppenrun_shartas_list)}\n\n"
    if gruppenrun_shartas_list:
        for i, participant in enumerate(gruppenrun_shartas_list, 1):
            response += f"{i}. {participant}\n"
    else:
        response += "Нет регистраций.\n"

    # Группенран Трейл
    response += f"\n\n⛰️ Группенран Трейл №{next_uktus_number} ({next_uktus_date_str})\n"
    response += f"Всего участников: {len(gruppenrun_uktus_list)}\n\n"
    if gruppenrun_uktus_list:
        for i, participant in enumerate(gruppenrun_uktus_list, 1):
            response += f"{i}. {participant}\n"
    else:
        response += "Нет регистраций.\n"
  
    # Кругосветка
    response += f"\n\n🌍 Кругосветка 2025\n"
    response += f"Всего участников: {len(krugosvetka_list)}\n\n"
    
    if krugosvetka_list:
        for i, participant in enumerate(krugosvetka_list, 1):
            response += f"{i}. {participant}\n"
    else:
        response += "Нет регистраций.\n"
    
    # Если сообщение слишком длинное, разбиваем на части
    if len(response) > 4000:
        # Отправляем Группенран отдельно
        msg1 = f"📊 РЕГИСТРАЦИИ\n\n🏃♂️ Группенран №{next_gruppenrun_number} ({next_gruppenrun_date_str})\nВсего: {len(gruppenrun_list)}\n\n"
        if gruppenrun_list:
            for i, p in enumerate(gruppenrun_list, 1):
                msg1 += f"{i}. {p}\n"
        
        await message.answer(msg1)
        
        # Завтраки
        msg2 = f"🍳 Предзаказ завтраков\nВсего: {len(breakfast_list)}\n\n"
        if breakfast_list:
            for i, o in enumerate(breakfast_list, 1):
                msg2 += f"{i}. {o}\n"
        
        await message.answer(msg2)
        
        # Кругосветка
        msg3 = f"🌍 Кругосветка 2025\nВсего: {len(krugosvetka_list)}\n\n"
        if krugosvetka_list:
            for i, p in enumerate(krugosvetka_list, 1):
                msg3 += f"{i}. {p}\n"
        
        await message.answer(msg3)
    else:
        await message.answer(response)

@router.message(F.text == "⬅️ Назад", StateFilter(None))
async def back_to_main(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("Главное меню:", reply_markup=admin_kb)
    else:
        await message.answer("Главное меню:", reply_markup=main_kb)
    await state.clear()


# ===== АДМИН-ПАНЕЛЬ =====

@router.message(F.text == "📊 Админ-панель", StateFilter(None))
async def admin_panel(message: types.Message, state: FSMContext):
    """Открывает админ-панель"""
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("❌ Эта функция доступна только администратору.")
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    sent_message = await message.answer(
        "📊 **Админ-панель**\n\n"
        "Выбери раздел для просмотра списков участников:",
        reply_markup=admin_panel_kb
    )
    
    # Сохраняем ID нового сообщения
    await save_admin_message_id(state, sent_message.message_id)

@router.message(F.text == "⬅️ Назад в главное меню", StateFilter(None))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат из админ-панели в главное меню"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    await message.answer(
        "Главное меню:",
        reply_markup=admin_kb
    )
    
    # Очищаем ID (мы вышли из админ-панели)
    await state.update_data(last_admin_message_id=None)

@router.message(F.text == "⚫ Группенран Трейл", StateFilter(None))
async def show_uktus_list(message: types.Message, state: FSMContext):
    """Показывает список участников Группенран Трейл"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    from utils.database import db
    
    # Получаем регистрации Трейл (location='uktus')
    uktus_list = []
    
    all_users = db.get_all_users()
    for user in all_users:
        user_id = user['user_id']
        reg = db.check_gruppenrun_registration(user_id, location='uktus')
        
        if reg.get('is_active'):
            name = user.get('name', 'Неизвестно')
            phone = user.get('phone', 'Нет')
            username = user.get('username', 'Нет')
            reg_type = reg.get('type', 'onetime')
            type_text = "Месячный" if reg_type == 'monthly' else "Разовый"
            uktus_list.append(f"{name} | {type_text} | @{username} | {phone}")
    
    next_uktus_date = get_next_saturday()
    next_uktus_number = get_current_uktus_number()
    next_uktus_date_str = next_uktus_date.strftime("%d.%m.%Y")

    response = f"⛰️ **Группенран Трейл №{next_uktus_number}**\n"
    response += f"📅 Следующая тренировка: {next_uktus_date_str}\n"
    response += f"👥 Всего участников: {len(uktus_list)}\n\n"
    
    if uktus_list:
        for i, participant in enumerate(uktus_list, 1):
            response += f"{i}. {participant}\n"
    else:
        response += "Нет регистраций."
    
    sent_message = await message.answer(
        response,
        reply_markup=admin_panel_kb
    )
    await save_admin_message_id(state, sent_message.message_id)

@router.message(F.text == "🍳 Завтраки", StateFilter(None))
async def show_breakfast_list(message: types.Message, state: FSMContext):
    """Показывает список заказов завтраков"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    all_data = load_data()
    
    breakfast_list = []
    
    for user_id, user_data in all_data.items():
        breakfast_order = user_data.get("breakfast_order", {})
        
        if breakfast_order.get("items"):
            name = user_data.get("name", "Неизвестно")
            items_text = []
            
            for item_id, count in breakfast_order["items"].items():
                item_info = BREAKFAST_MENU.get(item_id, {})
                item_name = item_info.get("name", item_id)
                items_text.append(f"{item_name} x{count}")
            
            total = breakfast_order.get("total_price", 0)
            breakfast_list.append(f"{name} | {', '.join(items_text)} | {total}₽")
    
    response = f"🍳 **Предзаказ завтраков**\n"
    response += f"📦 Всего заказов: {len(breakfast_list)}\n\n"
    
    if breakfast_list:
        for i, order in enumerate(breakfast_list, 1):
            response += f"{i}. {order}\n"
    else:
        response += "Нет заказов."
    
    sent_message = await message.answer(
        response,
        reply_markup=admin_panel_kb
    )
    
    await save_admin_message_id(state, sent_message.message_id)

@router.message(F.text == "🌍 Кругосветка", StateFilter(None))
async def show_krugosvetka_list(message: types.Message, state: FSMContext):
    """Показывает список участников Кругосветки"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    all_data = load_data()
    
    krugosvetka_list = []
    
    for user_id, user_data in all_data.items():
        krugosvetka_data = user_data.get("krugosvetka", {})
        
        if krugosvetka_data.get("is_registered"):
            name = user_data.get("name", "Неизвестно")
            phone = user_data.get("phone", "Нет")
            username = user_data.get("username", "Нет")
            pace = krugosvetka_data.get("pace", "Нет")
            
            stages_ids = krugosvetka_data.get("stages_ids", [])
            
            if "all_stages" in stages_ids:
                stages_text = "Весь круг"
            else:
                stage_numbers = []
                for stage_id in stages_ids:
                    if stage_id.startswith("stage_"):
                        stage_num = stage_id.replace("stage_", "")
                        stage_numbers.append(stage_num)
                
                stages_text = ", ".join(sorted(stage_numbers))
            
            krugosvetka_list.append(f"{name} | Этапы: {stages_text} | Темп: {pace} | @{username}")
    
    response = f"🌍 **Кругосветка 2025**\n"
    response += f"👥 Всего участников: {len(krugosvetka_list)}\n\n"
    
    if krugosvetka_list:
        for i, participant in enumerate(krugosvetka_list, 1):
            response += f"{i}. {participant}\n"
    else:
        response += "Нет регистраций."
    
    sent_message = await message.answer(
        response,
        reply_markup=admin_panel_kb
    )
    
    await save_admin_message_id(state, sent_message.message_id)

@router.message(F.text == "🏔 Иремель", StateFilter(None))
async def show_iremel_list(message: types.Message, state: FSMContext):
    """Показывает список участников Иремель Кэмпа"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    all_data = load_data()
    
    iremel_list = []
    waiting_list = []
    
    for user_id, user_data in all_data.items():
        iremel_data = user_data.get("iremel", {})
        
        name = user_data.get("name", "Неизвестно")
        phone = user_data.get("phone", "Нет")
        username = user_data.get("username", "Нет")
        
        if iremel_data.get("is_registered"):
            payment_type = iremel_data.get("payment_type", "full")
            payment_text = "50%" if payment_type == "prepay" else "100%"
            diet = iremel_data.get("diet_restrictions", "Нет")
            preferences = iremel_data.get("preferences", "Нет")
            
            iremel_list.append(
                f"{name} | Оплата: {payment_text} | Диета: {diet} | @{username} | {phone}"
            )
        elif iremel_data.get("waiting_list"):
            waiting_list.append(f"{name} | @{username} | {phone}")
    
    response = f"🏔 Иремель Кэмп 2025\n"
    response += f"📅 28-30 ноября 2025\n"
    response += f"👥 Зарегистрировано: {len(iremel_list)} из {IREMEL_MAX_PARTICIPANTS}\n"
    response += f"⏳ В листе ожидания: {len(waiting_list)}\n\n"
    
    if iremel_list:
        response += "✅ УЧАСТНИКИ:\n"
        for i, participant in enumerate(iremel_list, 1):
            response += f"{i}. {participant}\n"
    
    if waiting_list:
        response += "\n⏳ ЛИСТ ОЖИДАНИЯ:\n"
        for i, participant in enumerate(waiting_list, 1):
            response += f"{i}. {participant}\n"
    
    if not iremel_list and not waiting_list:
        response += "Нет регистраций."
    
    sent_message = await message.answer(
        response,
        reply_markup=admin_panel_kb
    )
    
    await save_admin_message_id(state, sent_message.message_id)

@router.message(F.text == "📊 Все регистрации", StateFilter(None))
async def show_all_registrations(message: types.Message, state: FSMContext):
    """Показывает сводку по всем регистрациям (аналог команды /registrations)"""
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    
    # Удаляем предыдущее сообщение
    await delete_last_admin_message(message, state, message.bot)
    
    # Вызываем существующую функцию
    await show_registrations(message)

@router.message(Command("admin_stats"))
async def admin_stats(message: types.Message):
    """Команда для администратора - просмотр статистики"""
    
    # Проверка что это админ
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    # Получаем отчёт
    report = analytics.get_stats_report()
    await message.answer(report, parse_mode="HTML")
    
    logger.info(f"📊 Админ {message.from_user.id} запросил статистику")

@router.message(F.text == "📊 Аналитика", StateFilter(None))
async def show_analytics(message: types.Message, state: FSMContext):
    """Показывает аналитику (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        return
    
    # Удаляем предыдущее сообщение админа
    await delete_last_admin_message(message, state, message.bot)
    
    # Получаем отчёт аналитики
    report = analytics.get_stats_report()
    
    # Отправляем отчёт с админ-панелью
    sent_message = await message.answer(
        report,
        parse_mode="HTML",
        reply_markup=admin_panel_kb
    )
    
    # Сохраняем ID нового сообщения
    await save_admin_message_id(state, sent_message.message_id)
