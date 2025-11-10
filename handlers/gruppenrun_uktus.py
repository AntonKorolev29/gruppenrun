from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply import main_kb, admin_kb, back_kb, phone_kb, payment_kb
from datetime import datetime, timedelta, date
from utils.database import db
from config import ADMIN_ID, PAYMENT_LINK_UKTUS, PAYMENT_MONTH_LINK_UKTUS
from utils.analytics import analytics
from config import PAYMENT_DETAILS

router = Router()

# ID фото Группенран Трейл
UKTUS_PHOTO_ID = "AgACAgIAAxkBAAIlP2kPFx1Jh0VZ24JYwKSsCTb1kYWCAAL1DGsbmwN5SBojvwUtZ7IZAQADAgADeQADNgQ"

# FSM состояния для Группенран Уктус (Трейл)
class GruppenrunUktusReg(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_payment_type = State()
    waiting_for_payment = State()

    # ✅ НОВЫЕ СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ ДРУГА
    friend_waiting_for_name = State()
    friend_waiting_for_phone = State()
    friend_waiting_for_payment_type = State()
    friend_waiting_for_payment = State()

# Клавиатуры
uktus_main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Зарегистрироваться", callback_data="uktus_register")],
    [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="uktus_about")],
    [InlineKeyboardButton(text="🗺️ Треки", callback_data="uktus_tracks")],
    [InlineKeyboardButton(text="📋 Правила", callback_data="uktus_rules")],
    [InlineKeyboardButton(text="📍 Как найти", callback_data="uktus_location")]
])

payment_type_uktus_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Разовое посещение (300₽)", callback_data="uktus_payment_onetime")],
    [InlineKeyboardButton(text="🎟 Месячный абонемент (1000₽)", callback_data="uktus_payment_monthly")]
])

back_to_uktus_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_uktus_menu")]
])

# ПРЕДЛОЖЕНИЕ ЗАРЕГИСТРИРОВАТЬ ДРУГА
register_friend_uktus_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 Зарегистрировать друга/подругу", callback_data="uktus_register_friend")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="uktus_to_main")]
])

# ===== ГЛАВНОЕ МЕНЮ ГРУППЕНРАН ТРЕЙЛ =====
@router.message(F.text == "⚫ Группенран Трейл")
async def gruppenrun_uktus_main(message: types.Message):
    """Главное меню Группенран Трейл - для ВСЕХ пользователей"""
    main_text = (
        "🏔 <b>ГРУППЕНРАН х ТРЕЙЛ</b>\n\n"
        "Новое направление — трейловые тренировки на Уктусе!\n\n"
        "<b>О локации:</b>\n"
        "Уктус — площадка для трейлового и горного бега в Екатеринбурге с разнообразным рельефом: "
        "от парковых тропинок до каменных россыпей.\n\n"
        "<b>Наша цель:</b>\n"
        "Развитие трейлового направления и повышение уровня трейлраннеров. "
        "Мы создаем треки с работой в горки, техничными участками и скоростными тропами.\n\n"
        "<b>Как тренируемся:</b>\n"
        "Делимся на группы по уровню и подбираем маршруты на 90 минут бега.\n\n"
        "<b>3 уровня сложности:</b>\n"
        "🟢 Light (7-9 км) — для новичков\n"
        "🟡 Middle (9-16 км) — оптимальный баланс\n"
        "🔴 Hard (16+ км) — для подготовленных\n\n"
        "<b>База:</b>\n"
        "Собираемся в домике гриль-парка ГЛК Уктус — можно переодеться в тепле, оставить вещи, "
        "после тренировки попить чай.\n\n"
        "<b>Стоимость:</b>\n"
        "💰 Разовое посещение — 300₽\n"
        "💰 Месячный абонемент — 1000₽\n\n"
        "❗️ Первая тренировка: 08.11.2025"
    )
    
    # ВСЕМ показываем ПОЛЬЗОВАТЕЛЬСКОЕ меню (включая админа)
    await message.answer_photo(
        photo=UKTUS_PHOTO_ID,
        caption=main_text,
        parse_mode="HTML",
        reply_markup=uktus_main_kb
    )

# ===== РЕГИСТРАЦИЯ =====
@router.callback_query(F.data == "uktus_register")
async def uktus_register_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации"""
    await callback_query.answer()
    user_id = str(callback_query.from_user.id)
    user = db.get_user(user_id)
    
    # Проверка активной регистрации на Уктус
    if user:
        uktus_reg = db.check_gruppenrun_registration(user_id, location='uktus')
        if uktus_reg.get("is_active"):
            await callback_query.message.answer(
                f"✅ Ты уже зарегистрирован на Группенран Трейл!"
            )
            return
    
    # ПРОВЕРКА ПРОФИЛЯ
    if user and user.get("name") and user.get("phone"):
        await state.update_data(name=user["name"], phone=user["phone"])
        await callback_query.message.answer(
            "🏔 Группенран Уктус - 3 уровня сложности:\n\n"
            "🟢 Light (7-9 км) — для новичков\n"
            "🟡 Middle (9-16 км) — оптимальный баланс\n"
            "🔴 Hard (16+ км) — для подготовленных\n\n"
            "Выбери удобный для себя уровень!\n\n"
            "Теперь выбери тип регистрации:",
            reply_markup=payment_type_uktus_kb
        )
        await state.set_state(GruppenrunUktusReg.waiting_for_payment_type)
        return
    
    # Начало новой регистрации
    await callback_query.message.answer(
        "🏔 Регистрация на Группенран Трейл\n\n"
        "Введи свои Фамилию и Имя:"
    )
    await state.set_state(GruppenrunUktusReg.waiting_for_name)

@router.message(GruppenrunUktusReg.waiting_for_name)
async def gruppenrun_uktus_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    from utils.validators import validate_name
    is_valid, result = validate_name(message.text)
    if not is_valid:
        await message.answer(result, reply_markup=back_kb)
        return
    
    formatted_name = result
    await state.update_data(name=formatted_name)
    await message.answer(
        f"✅ Отлично, {formatted_name.split()[0]}!\n\n"
        "Теперь нажми кнопку ниже, чтобы отправить свой номер телефона.",
        reply_markup=phone_kb
    )
    await state.set_state(GruppenrunUktusReg.waiting_for_phone)

@router.message(GruppenrunUktusReg.waiting_for_phone, F.text)
async def gruppenrun_uktus_phone_text(message: types.Message, state: FSMContext):
    """Обработка ввода телефона текстом"""
    from utils.validators import validate_phone
    is_valid, result = validate_phone(message.text)
    if not is_valid:
        await message.answer(result, reply_markup=phone_kb)
        return
    
    formatted_phone = result
    await state.update_data(phone=formatted_phone)
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Теперь выбери тип регистрации:",
        reply_markup=payment_type_uktus_kb
    )
    await state.set_state(GruppenrunUktusReg.waiting_for_payment_type)

@router.message(GruppenrunUktusReg.waiting_for_phone, F.contact)
async def gruppenrun_uktus_phone(message: types.Message, state: FSMContext):
    """Обработка получения номера телефона"""
    if not message.contact:
        await message.answer(
            "Пожалуйста, используй кнопку для отправки номера или введи его вручную.",
            reply_markup=phone_kb
        )
        return
    
    phone = message.contact.phone_number
    from utils.validators import validate_phone
    is_valid, formatted_phone = validate_phone(phone)
    await state.update_data(phone=formatted_phone)
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Теперь выбери тип регистрации:",
        reply_markup=payment_type_uktus_kb
    )
    await state.set_state(GruppenrunUktusReg.waiting_for_payment_type)

# ===== ВЫБОР ТИПА ОПЛАТЫ =====
@router.callback_query(F.data.in_(["uktus_payment_onetime", "uktus_payment_monthly"]), GruppenrunUktusReg.waiting_for_payment_type)
async def gruppenrun_uktus_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа оплаты"""
    await callback_query.answer()
    payment_type = callback_query.data
    await state.update_data(payment_type=payment_type)

    if payment_type == "uktus_payment_onetime":
        payment_link = PAYMENT_LINK_UKTUS
        price = 300
        payment_text = "разовое посещение"
    else:  # uktus_payment_monthly
        payment_link = PAYMENT_MONTH_LINK_UKTUS
        price = 1000
        payment_text = "месячный абонемент"

    # ОБЪЕДИНЁННОЕ СООБЩЕНИЕ
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", url=payment_link)]
    ])

    await callback_query.message.answer(
        f"💳 <b>Оплата {payment_text} ({price}₽)</b>\n\n"
        f"1️⃣ 🔗 Нажми кнопку ниже для оплаты через ЮMoney.\n\n"
        f"🏦 <b>Прямой перевод:</b>\n"
        f"• +7 (922) 608-01-01\n"
        f"• OzonБанк\n"
        f"• Антон Александрович К.\n\n"
        f"2️⃣ После оплаты вернись в бота и нажми '✅ Я оплатил(а)' внизу экрана.",
        parse_mode="HTML",
        reply_markup=payment_keyboard
    )

    # КНОПКА "Я ОПЛАТИЛ"
    await callback_query.message.answer(
        f"После перевода нажми кнопку ниже:",
        parse_mode="HTML",
        reply_markup=payment_kb
    )
    
    await state.set_state(GruppenrunUktusReg.waiting_for_payment)
    return

# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ =====
@router.message(F.text == "✅ Я оплатил(а)", GruppenrunUktusReg.waiting_for_payment)
async def gruppenrun_uktus_payment_confirm(message: types.Message, state: FSMContext):
    """Подтверждение оплаты"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    payment_type = reg_data.get("payment_type", "uktus_payment_onetime")
    reg_type = "monthly" if "monthly" in payment_type else "onetime"
    
    # Сохраняем пользователя в единую базу
    db.save_user(
        user_id=user_id,
        name=reg_data.get("name"),
        phone=reg_data.get("phone"),
        username=message.from_user.username
    )
    
    # Сохраняем регистрацию на Уктус
    valid_until = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") if reg_type == "monthly" else None
    db.save_gruppenrun_registration(user_id, reg_type, valid_until, location='uktus')
    
    # Формируем сообщение для пользователя
    reg_info_text = "Уровень подготовки: выбираешь сам в день тренировки!\n"
    if reg_type == "monthly" and valid_until:
        reg_info_text = f"Месячный абонемент! Действителен до {datetime.strptime(valid_until, '%Y-%m-%d').strftime('%d.%m.%Y')}"
    
    is_admin = user_id == str(ADMIN_ID)
    
    await message.answer(
        f"🎉 <b>Регистрация завершена!</b>\n\n"
        f"{reg_info_text}\n\n"
        f"Увидимся на Уктусе! 🏔️",
        parse_mode="HTML",
        reply_markup=register_friend_uktus_kb
    )
    
    # Уведомление администратору
    admin_text = (
        f"🔔 Новая регистрация на Группенран Трейл!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"{'📅 Месячный абонемент' if reg_type == 'monthly' else '📅 Разовое посещение'}\n"
        f"ID: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления администратору: {e}")
    
    analytics.track_registration(message.from_user.id, "gruppenrun_uktus")
    db.track_event(user_id, "registered_uktus", {"type": reg_type})
    
    await state.clear()

# ===== ИНФОРМАЦИОННЫЕ РАЗДЕЛЫ =====
@router.callback_query(F.data == "uktus_about")
async def uktus_about_callback(callback_query: types.CallbackQuery):
    """О проекте"""
    await callback_query.answer()
    
    text = (
        "🏔️ <b>О проекте ГРУППЕНРАН х ТРЕЙЛ</b>\n\n"
        "Мы хотим внести свой вклад в развитие трейлового бега в Екатеринбурге и поднять общий уровень трейлраннеров.\n\n"
        "<b>Наша миссия:</b>\n"
        "• Делиться богатым опытом в трейле\n"
        "• Учить пользоваться треками в часах и ориентироваться\n"
        "• Помогать обкатать экипировку и питание\n"
        "• Подготовить вас к любым условиям\n\n"
        "<b>Что мы создаём:</b>\n"
        "Треки, которые включают работу в горки, технические участки и скоростные тропы — "
        "всё, что нужно для настоящего развития в трейлраннинге.\n\n"
        "<b>Если ты новичок в трейле:</b>\n"
        "Не волнуйся! Мы познакомим тебя с прекрасным миром трейлраннинга и 100% влюбим тебя в него ❤️🔥"
    )
    
    # ✅ ПРАВИЛЬНО - используем text
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=back_to_uktus_kb)

@router.callback_query(F.data == "uktus_tracks")
async def uktus_tracks_callback(callback_query: types.CallbackQuery):
    """Треки"""
    await callback_query.answer()
    
    text = (
        "🗺️ <b>ДОСТУПНЫЕ ТРЕКИ</b>\n\n"
        "Мы готовим треки с учётом особенностей трейлраннинга.\n\n"
        "<b>🟢 Light (7-9 км)</b>\n"
        "Дистанция: для новичков в трейле\n"
        "Просмотр трека: https://mapmagic.app/map?routes=6jgvvL9\n\n"
        "<b>🟡 Middle (9-16 км)</b>\n"
        "Дистанция: оптимальный баланс нагрузки\n"
        "Просмотр трека: https://mapmagic.app/map?routes=0yBY786\n\n"
        "<b>🔴 Hard (16+ км)</b>\n"
        "Дистанция: для подготовленных бегунов\n"
        "Просмотр трека: https://mapmagic.app/map?routes=9L3jYD6\n\n"
        "<b>Что включают маршруты:</b>\n"
        "• Подъемы разной крутизны\n"
        "• Технические участки с камнями\n"
        "• Скоростные тропы\n"
        "• Панорамные точки для отдыха"
    )
    
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=back_to_uktus_kb)

@router.callback_query(F.data == "uktus_rules")
async def uktus_rules_callback(callback_query: types.CallbackQuery):
    """Правила"""
    await callback_query.answer()
    
    text = (
        "📋 <b>ПРАВИЛА УЧАСТИЯ</b>\n\n"
        "<b>Обязательно с собой:</b>\n"
        "• Заряженный телефон с геолокацией\n"
        "• Вода/изотоник (минимум 0,5л)\n"
        "• Базовые навыки ориентирования\n"
        "• Ответственность за свою безопасность\n\n"
        "<b>Рекомендуется:</b>\n"
        "• Трейловые кроссовки с протектором для лучшего сцепления\n"
        "• Ветровка на случай изменения погоды\n"
        "• Минимальный запас еды (гель, батончик)\n"
        "• Фонарик в осенне-зимний период\n\n"
        "<b>Формат тренировок:</b>\n"
        "• Старт групповой с базы\n"
        "• Разделение на группы по уровню подготовки\n"
        "• Маршруты рассчитаны на 90 минут бега\n"
        "• Контрольные точки для сбора группы\n"
        "• Финиш на базе с возможностью попить чай и пообщаться"
    )
    
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=back_to_uktus_kb)

@router.callback_query(F.data == "uktus_location")
async def uktus_location_callback(callback_query: types.CallbackQuery):
    """Как найти"""
    await callback_query.answer()
    
    text = (
        "📍 КАК НАС НАЙТИ\n\n"
        "Локация:\n"
        "ГЛК Уктус, гриль-парк «Белкино»\n\n"
        "Адрес:\n"
        "ул. Зимняя 27, Екатеринбург\n" 
        "Координаты: 56.774588, 60.645524\n\n"
        "Карта:\n"
        "https://yandex.ru/maps/-/CLvo6WOR\n\n"
        "Как добраться:\n"
        "🚗 На машине: припарковаться можно на парковке ГЛК\n"
        "🚌 Общественный транспорт: ост. Уктус, от неё 15 минут пешком\n\n"
        "Что вас ждёт:\n"
        "✅ Тепло и комфорт перед и после тренировки\n"
        "✅ Место для переодевания\n"
        "✅ Возможность оставить вещи\n"
        "✅ Чай и общение после тренировки"
    )
    
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=back_to_uktus_kb)

# ===== НАЗАД В ГЛАВНОЕ МЕНЮ =====
@router.callback_query(F.data == "back_to_uktus_menu")
async def back_to_uktus_menu(callback_query: types.CallbackQuery):
    """Назад в главное меню Уктуса"""
    await callback_query.answer()
    
    main_text = (
        "🏔 <b>ГРУППЕНРАН х ТРЕЙЛ</b>\n\n"
        "Новое направление — трейловые тренировки на Уктусе!\n\n"
        "<b>О локации:</b>\n"
        "Уктус — площадка для трейлового и горного бега в Екатеринбурге с разнообразным рельефом: "
        "от парковых тропинок до каменных россыпей.\n\n"
        "<b>Наша цель:</b>\n"
        "Развитие трейлового направления и повышение уровня трейлраннеров. "
        "Мы создаем треки с работой в горки, техничными участками и скоростными тропами.\n\n"
        "<b>Как тренируемся:</b>\n"
        "Делимся на группы по уровню и подбираем маршруты на 90 минут бега.\n\n"
        "<b>3 уровня сложности:</b>\n"
        "🟢 Light (7-9 км) — для новичков\n"
        "🟡 Middle (9-16 км) — оптимальный баланс\n"
        "🔴 Hard (16+ км) — для подготовленных\n\n"
        "<b>База:</b>\n"
        "Собираемся в домике гриль-парка ГЛК Уктус — можно переодеться в тепле, оставить вещи, "
        "после тренировки попить чай.\n\n"
        "<b>Стоимость:</b>\n"
        "💰 Разовое посещение — 300₽\n"
        "💰 Месячный абонемент — 1000₽"
    )
    
    # ✅ ПРАВИЛЬНО - используем main_text и uktus_main_kb
    await callback_query.message.answer(main_text, parse_mode="HTML", reply_markup=uktus_main_kb)

# ===== ОБРАБОТЧИК КНОПКИ НАЗАД =====
@router.message(F.text == "⬅️ Назад", StateFilter(
    GruppenrunUktusReg.waiting_for_name,
    GruppenrunUktusReg.waiting_for_phone,
    GruppenrunUktusReg.waiting_for_payment_type,
    GruppenrunUktusReg.waiting_for_payment
))
async def back_button_uktus(message: types.Message, state: FSMContext):
    """Обработчик кнопки Назад"""
    current_state = await state.get_state()
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    if current_state == "GruppenrunUktusReg:waiting_for_payment":
        await message.answer(
            "Возвращаемся к выбору типа регистрации.\n\n"
            "Выбери тип регистрации:",
            reply_markup=payment_type_uktus_kb
        )
        await state.set_state(GruppenrunUktusReg.waiting_for_payment_type)
        return
    
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )

# ==========================
# ✅ РЕГИСТРАЦИЯ ДРУГА
# ==========================
@router.callback_query(F.data == "uktus_register_friend")
async def uktus_register_friend_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало регистрации друга"""
    user_id = callback.from_user.id
    
    await callback.message.answer(
        "👥 **Регистрация друга/подруги на Группенран Трейл**\n\n"
        "Пожалуйста, введите **имя и фамилию** друга/подруги:",
        parse_mode="Markdown"
    )
    await state.set_state(GruppenrunUktusReg.friend_waiting_for_name)
    await callback.answer()
    analytics.log_event(user_id, "uktus_register_friend_start")

@router.message(GruppenrunUktusReg.friend_waiting_for_name)
async def uktus_friend_name(message: types.Message, state: FSMContext):
    """Получение имени друга"""
    friend_name = message.text.strip()
    
    if len(friend_name) < 2:
        await message.answer("⚠️ Имя должно содержать минимум 2 символа. Попробуйте ещё раз:")
        return
    
    await state.update_data(friend_name=friend_name)
    await message.answer(
        f"✅ Имя: {friend_name}\n\n"
        "📱 Теперь введите **номер телефона** друга/подруги\n\n"
        "Формат: +79123456789",
        parse_mode="Markdown"
    )
    await state.set_state(GruppenrunUktusReg.friend_waiting_for_phone)

@router.message(GruppenrunUktusReg.friend_waiting_for_phone)
async def uktus_friend_phone(message: types.Message, state: FSMContext):
    """Получение телефона друга"""
    phone = message.text.strip()
    
    # Валидация телефона
    if not phone.startswith('+') or len(phone) < 11:
        await message.answer("⚠️ Неверный формат телефона. Введите в формате: +79123456789")
        return
    
    await state.update_data(friend_phone=phone)
    
    # Предлагаем выбрать тип оплаты
    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Разовая (300₽)", callback_data="uktus_friend_pay_onetime")],
        [InlineKeyboardButton(text="📅 Месячная (1000₽)", callback_data="uktus_friend_pay_monthly")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="uktus_friend_cancel")]
    ])
    
    await message.answer(
        "💳 **Выберите тип оплаты для друга/подруги:**\n\n"
        "📝 **Разовая (300₽)** — до конца недели\n"
        "📅 **Месячная (1000₽)** — на 4 тренировки",
        reply_markup=payment_kb,
        parse_mode="Markdown"
    )
    await state.set_state(GruppenrunUktusReg.friend_waiting_for_payment_type)

@router.callback_query(F.data == "uktus_friend_pay_onetime")
async def uktus_friend_payment_onetime(callback: types.CallbackQuery, state: FSMContext):
    """Разовая оплата для друга"""
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    friend_name = data.get('friend_name')
    friend_phone = data.get('friend_phone')
    
    # Создаём временный ID для друга (на основе телефона)
    friend_temp_id = f"friend_{friend_phone}"
    
    # Регистрируем друга
    valid_until = None
    db.save_gruppenrun_registration(friend_temp_id, 'onetime', valid_until, location='uktus')
    
    # Сохраняем данные друга
    db.save_user(
        user_id=friend_temp_id,
        name=friend_name,
        phone=friend_phone,
        username=None
    )
    
    is_admin = user_id == str(ADMIN_ID)
    
    await callback.message.answer(
        f"✅ **{friend_name} зарегистрирован(а)!**\n\n"
        f"⛰️ Группенран Трейл\n"
        f"💰 Разовая оплата: 300₽\n"
        f"📱 Телефон: {friend_phone}\n\n"
        f"📲 **Способы оплаты:**\n"
        f"{PAYMENT_DETAILS}",
        reply_markup=admin_kb if is_admin else main_kb,
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer("✅ Друг зарегистрирован!", show_alert=True)
    analytics.log_event(user_id, "uktus_friend_registered_onetime")

@router.callback_query(F.data == "uktus_friend_pay_monthly")
async def uktus_friend_payment_monthly(callback: types.CallbackQuery, state: FSMContext):
    """Месячная оплата для друга"""
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    friend_name = data.get('friend_name')
    friend_phone = data.get('friend_phone')
    
    # Создаём временный ID для друга
    friend_temp_id = f"friend_{friend_phone}"
    
    # Регистрируем друга
    valid_until = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    db.save_gruppenrun_registration(friend_temp_id, 'monthly', valid_until, location='uktus')
    
    # Сохраняем данные друга
    db.save_user(
        user_id=friend_temp_id,
        name=friend_name,
        phone=friend_phone,
        username=None
    )
    
    is_admin = user_id == str(ADMIN_ID)
    
    await callback.message.answer(
        f"✅ **{friend_name} зарегистрирован(а)!**\n\n"
        f"⛰️ Группенран Трейл\n"
        f"💰 Месячная подписка: 1000₽\n"
        f"📱 Телефон: {friend_phone}\n\n"
        f"📲 **Способы оплаты:**\n"
        f"{PAYMENT_DETAILS}",
        reply_markup=admin_kb if is_admin else main_kb,
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer("✅ Друг зарегистрирован!", show_alert=True)
    analytics.log_event(user_id, "uktus_friend_registered_monthly")

@router.callback_query(F.data == "uktus_friend_cancel")
async def uktus_friend_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена регистрации друга"""
    user_id = str(callback.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    await callback.message.answer(
        "❌ Регистрация друга отменена.",
        reply_markup=admin_kb if is_admin else main_kb
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "uktus_to_main")
async def uktus_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    user_id = str(callback.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    await state.clear()
    
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=admin_kb if is_admin else main_kb
    )
    await callback.answer()



