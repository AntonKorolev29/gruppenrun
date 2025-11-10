from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from utils.helpers import load_data, save_data
from config import ADMIN_ID, PHONE_PAYMENT_INFO, PHOTO_IREMEL_COVER, IREMEL_PAYMENT_50, IREMEL_PAYMENT_100, IREMEL_MAX_PARTICIPANTS
from keyboards.reply import main_kb, admin_kb, back_kb, phone_kb, payment_kb
from utils.analytics import analytics

router = Router()

# FSM состояния
class IremelReg(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_diet_restrictions = State()
    waiting_for_preferences = State()
    waiting_for_payment_option = State()
    waiting_for_payment = State()
    waiting_list_name = State()
    waiting_list_phone = State()

    # ✅ НОВЫЕ СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ ДРУГА
    friend_waiting_for_name = State()
    friend_waiting_for_phone = State()
    friend_waiting_for_diet_restrictions = State()
    friend_waiting_for_preferences = State()
    friend_waiting_for_payment_option = State()
    friend_waiting_for_payment = State()

# Клавиатура для отправки номера телефона
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура с предложением зарегистрировать друга
register_friend_iremel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Зарегистрировать другого человека", callback_data="register_friend_iremel")],
    [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main_menu_iremel")]
])


# ===== УМНАЯ НАВИГАЦИЯ: КНОПКА "НАЗАД" =====
@router.message(F.text == "⬅️ Назад", StateFilter(
    IremelReg.waiting_for_name,
    IremelReg.waiting_for_phone,
    IremelReg.waiting_for_diet_restrictions,
    IremelReg.waiting_for_preferences,
    IremelReg.waiting_for_payment_option,
    IremelReg.waiting_for_payment
))
async def back_button_iremel(message: types.Message, state: FSMContext):
    """Обработчик кнопки Назад во время регистрации Иремель"""
    current_state = await state.get_state()
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    # Если на этапе оплаты - возвращаемся к выбору опции оплаты
    if current_state == "IremelReg:waiting_for_payment":
        payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 50% (3750₽)", callback_data="iremel_pay_50")],
            [InlineKeyboardButton(text="💳 Оплатить 100% (7500₽)", callback_data="iremel_pay_100")]
        ])
        await message.answer(
            "Выбери вариант оплаты:\n\n"
            "💰 Оплатить 50% — внеси предоплату 3750₽ сейчас, остаток до 20 ноября\n"
            "💰 Оплатить 100% — оплати полную стоимость 7500₽ сразу",
            reply_markup=payment_keyboard
        )
        await message.answer("Или нажми кнопку ниже для отмены:", reply_markup=back_kb)
        await state.set_state(IremelReg.waiting_for_payment_option)
        return
    
    # Для остальных состояний - полная отмена
    await state.clear()
    await message.answer(
        "❌ Регистрация на Иремель Кэмп отменена.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )

# ===== ПОЛНАЯ ОТМЕНА РЕГИСТРАЦИИ =====
@router.message(F.text == "❌ Отменить регистрацию", StateFilter(
    IremelReg.waiting_for_name,
    IremelReg.waiting_for_phone,
    IremelReg.waiting_for_diet_restrictions,
    IremelReg.waiting_for_preferences,
    IremelReg.waiting_for_payment_option,
    IremelReg.waiting_for_payment
))
async def cancel_iremel_registration(message: types.Message, state: FSMContext):
    """Полная отмена регистрации на Иремель"""
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    await state.clear()
    await message.answer(
        "❌ Регистрация на Иремель Кэмп отменена.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )

# ===== ГЛАВНОЕ МЕНЮ ИРЕМЕЛЯ =====
@router.message(F.text == "🏔 Иремель Кэмп 2025", StateFilter(None))
async def iremel_menu(message: types.Message):
    """Главное меню кэмпа на Иремель"""
    
    text = (
        "🏔 <b>Кэмп на Иремель 28-30 ноября 2025</b>\n\n"
        
        "В конце ноября мы традиционно отправляемся в любимое и уже такое родное село Тюлюк на мини-кэмп, с забегом на гору Большой Иремель и хребет Зигальга.\n"
        "Только бег, классная компания и море живого общения!\n\n"
        
        "<b>📅 Программа:</b>\n"
        "28 ноября (ПТ) - заезд\n"
        "29 ноября (СБ) - забег или кросс-поход на Большой Иремель (27 км D+1000м), а вечером баня и вкусный ужин от шефа\n"
        "30 ноября (ВС) - забег на хребет Зигальга (13 км D+500м), обед и выезд\n\n"
        
        "<b>🏠 Проживание:</b>\n"
        "Просторный дом со всеми удобствами (туалет, душ) на 30 человек с индивидуальными спальными местами, "
        "огромная гостиная-столовая и баня.\n\n"
        
        "<b>🍽 В стоимость входит:</b>\n"
        "• Проживание с двумя ночевками (28-30 ноября)\n"
        "• Полный пансион: завтрак, обед и ужин + глинтвейн\n"
        "• Баня в пятницу с 15 до 22 часов\n\n"
        
        "<b>💰 Стоимость: 7500₽</b>\n"
        "Можно оплатить сразу 100% или внести предоплату 50% (остаток до 20 ноября)"
    )
    
    menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Зарегистрироваться", callback_data="iremel_register")],
        [InlineKeyboardButton(text="📋 Список участников", callback_data="iremel_participants")]
    ])
    
    try:
        await message.answer_photo(
            photo=PHOTO_IREMEL_COVER,
            caption=text,
            reply_markup=menu_keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка загрузки обложки Иремеля: {e}")
        await message.answer(text, reply_markup=menu_keyboard, parse_mode="HTML")


# ===== РЕГИСТРАЦИЯ НА ИРЕМЕЛЬ =====

@router.callback_query(F.data == "iremel_register", StateFilter(None))
async def iremel_register(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации на Иремель"""
    
    # ✅ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
    import logging
    logging.info(f"🔍 iremel_register вызван пользователем {callback_query.from_user.id}")
    
    # ✅ ОДИН РАЗ ОТВЕТ НА CALLBACK
    await callback_query.answer()
    
    # ✅ ПРОВЕРКА И ОЧИСТКА СОСТОЯНИЯ
    current_state = await state.get_state()
    logging.info(f"🔍 Текущее состояние: {current_state}")
    
    if current_state is not None:
        await state.clear()
        logging.info("🔍 Состояние очищено")
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    user_data = all_data.get(user_id, {})
    
    # Проверка активной регистрации
    iremel_data = user_data.get("iremel", {})
    if iremel_data.get("is_registered"):
        await callback_query.message.answer(
            "✅ Ты уже зарегистрирован на кэмп на Иремель!\n\n"
            "Хочешь зарегистрировать другого человека?",
            reply_markup=register_friend_iremel_kb
        )
        return
    
    # Проверка наличия в листе ожидания
    if iremel_data.get("waiting_list"):
        await callback_query.message.answer(
            "📋 Ты уже в листе ожидания на кэмп на Иремель!\n\n"
            "Хочешь зарегистрировать другого человека?",
            reply_markup=register_friend_iremel_kb
        )
        return
    
    # ПРОВЕРКА КОЛИЧЕСТВА СВОБОДНЫХ МЕСТ
    registered_count = sum(1 for uid, data in all_data.items()
                           if data.get("iremel", {}).get("is_registered"))
    
    logging.info(f"🔍 Зарегистрировано: {registered_count}/{IREMEL_MAX_PARTICIPANTS}")
    
    if registered_count >= IREMEL_MAX_PARTICIPANTS:
        # Места закончились - предлагаем лист ожидания
        waiting_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Записаться в лист ожидания", callback_data="iremel_waiting_list")]
        ])
        await callback_query.message.answer(
            f"😔 К сожалению, все {IREMEL_MAX_PARTICIPANTS} мест на кэмп уже заняты!\n\n"
            f"Но ты можешь записаться в лист ожидания. Если кто-то откажется, "
            f"мы свяжемся с тобой.",
            reply_markup=waiting_keyboard
        )
        return
    
    # Есть свободные места - продолжаем обычную регистрацию
    remaining = IREMEL_MAX_PARTICIPANTS - registered_count
    logging.info(f"🔍 Осталось мест: {remaining}")
    
    # Проверка профиля
    existing_name = user_data.get("name")
    existing_phone = user_data.get("phone")
    
    if existing_name and existing_phone:
        await state.update_data(name=existing_name, phone=existing_phone)
        await callback_query.message.answer(
            f"🏔 Осталось мест: {remaining} из {IREMEL_MAX_PARTICIPANTS}\n\n"
            f"Есть ли у тебя ограничения по питанию или продуктам?\n"
            f"(Например: вегетарианец, аллергия на что-то и т.д.)\n\n"
            f"Напиши свой ответ или отправь \"-\" если ограничений нет.",
            reply_markup=back_kb,
            parse_mode="HTML"
        )
        await state.set_state(IremelReg.waiting_for_diet_restrictions)
        return
    
    # Если профиля нет
    await callback_query.message.answer(
        f"🏔 Осталось мест: {remaining} из {IREMEL_MAX_PARTICIPANTS}\n\n"
        f"Для регистрации введи своё полное имя (Фамилия Имя):",
        reply_markup=back_kb,
        parse_mode="HTML"
    )
    await state.set_state(IremelReg.waiting_for_name)

@router.message(IremelReg.waiting_for_name)
async def iremel_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    
    # ✅ ИМПОРТ ВАЛИДАТОРА
    from utils.validators import validate_name
    
    # ✅ ВАЛИДАЦИЯ ИМЕНИ
    is_valid, result = validate_name(message.text)
    
    if not is_valid:
        # Если невалидно - отправляем сообщение об ошибке и ждём повторного ввода
        await message.answer(result, reply_markup=back_kb)
        return  # Остаёмся в том же состоянии
    
    # Имя валидно - сохраняем отформатированное имя
    formatted_name = result
    await state.update_data(name=formatted_name)
    
    await message.answer(
        f"✅ Отлично, {formatted_name.split()[0]}!\n\n"
        "Теперь нажми кнопку ниже, чтобы отправить свой номер телефона.",
        reply_markup=phone_kb
    )
    await state.set_state(IremelReg.waiting_for_phone)

@router.message(IremelReg.waiting_for_phone, F.text)
async def iremel_phone_text(message: types.Message, state: FSMContext):
    """Обработка ввода телефона текстом (если пользователь не использовал кнопку)"""
    
    from utils.validators import validate_phone
    
    # ✅ ВАЛИДАЦИЯ ТЕЛЕФОНА
    is_valid, result = validate_phone(message.text)
    
    if not is_valid:
        # Если невалидно - отправляем сообщение об ошибке
        await message.answer(result, reply_markup=phone_kb)
        return  # Остаёмся в том же состоянии
    
    # Телефон валиден - сохраняем отформатированный номер
    formatted_phone = result
    await state.update_data(phone=formatted_phone)
    
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Отлично! Теперь выбери тип регистрации:",
        reply_markup=payment_type_kb
    )
    await state.set_state(IremelReg.waiting_for_payment_type)

@router.message(IremelReg.waiting_for_phone, F.contact)
async def iremel_phone(message: types.Message, state: FSMContext):
    """Обработка получения номера телефона"""
   
    if not message.contact:
        await message.answer(
            "Пожалуйста, используй кнопку для отправки номера или введи его вручную.",
            reply_markup=phone_kb
        )
        return
    
    phone = message.contact.phone_number
    
    # ✅ ФОРМАТИРУЕМ ТЕЛЕФОН ИЗ КОНТАКТА
    from utils.validators import validate_phone
    is_valid, formatted_phone = validate_phone(phone)
    
    if not is_valid:
        # На всякий случай, хотя contact обычно валиден
        formatted_phone = phone
    
    await state.update_data(phone=formatted_phone)
    
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Отлично! Теперь выбери тип регистрации:",
        reply_markup=payment_type_kb
    )
    await state.set_state(IremelReg.waiting_for_diet_restrictions)


@router.message(IremelReg.waiting_for_diet_restrictions)
async def iremel_diet_restrictions(message: types.Message, state: FSMContext):
    """Обработка ограничений по питанию"""
        
    # ВАЖНО: Игнорируем кнопку "Назад" - её обработает back_button_iremel
    if message.text == "⬅️ Назад":
        return
  
    diet_restrictions = message.text if message.text != "-" else "Нет"
    await state.update_data(diet_restrictions=diet_restrictions)
    
    await message.answer(
        "Спасибо! Есть ли у тебя какие-то пожелания или комментарии?\n"
        "(Например: не пью глинтвейн, замените на безалкогольный напиток)\n\n"
        "Напиши свой ответ или отправь \"-\" если пожеланий нет.",
        reply_markup=back_kb
    )
    await state.set_state(IremelReg.waiting_for_preferences)


@router.message(IremelReg.waiting_for_preferences)
async def iremel_preferences(message: types.Message, state: FSMContext):
    """Обработка пожеланий"""
    
    if message.text == "⬅️ Назад":
        return
    
    preferences = message.text if message.text != "-" else "Нет"
    await state.update_data(preferences=preferences)
    
    # Переходим к выбору варианта оплаты
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 50% (3750₽)", callback_data="iremel_pay_50")],
        [InlineKeyboardButton(text="💳 Оплатить 100% (7500₽)", callback_data="iremel_pay_100")]
    ])
    
    await message.answer(
        "Отлично! Теперь выбери вариант оплаты:\n\n"
        "💰 <b>Оплатить 50%</b> — внеси предоплату 3750₽ сейчас, остаток до 20 ноября\n"
        "💰 <b>Оплатить 100%</b> — оплати полную стоимость 7500₽ сразу",
        reply_markup=payment_keyboard,
        parse_mode="HTML"
    )
    
    await message.answer(
        "Или нажми кнопку ниже для возврата:",
        reply_markup=back_kb
    )
    
    await state.set_state(IremelReg.waiting_for_payment_option)


# ===== ВЫБОР ВАРИАНТА ОПЛАТЫ =====
@router.callback_query(IremelReg.waiting_for_payment_option)
async def iremel_payment_option(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора варианта оплаты"""
    await callback_query.answer()
    
    payment_option = callback_query.data
    
    if payment_option == "iremel_pay_50":
        price = 3750
        payment_link = IREMEL_PAYMENT_50  # Вместо прямой ссылки
        payment_text = "предоплату 50%"
        payment_type = "prepay"
    else:  # iremel_pay_100
        price = 7500
        payment_link = IREMEL_PAYMENT_100  # Вместо прямой ссылки
        payment_text = "полную оплату"
        payment_type = "full"
    
    await state.update_data(payment_type=payment_type, payment_amount=price)
    
    # ✅ ИСПОЛЬЗУЕМ INLINE-КНОПКУ ТОЛЬКО ДЛЯ ССЫЛКИ НА ОПЛАТУ
    payment_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", url=payment_link)]
    ])

    # ✅ ДОБАВЛЯЕМ REPLY-КЛАВИАТУРУ ДЛЯ ПОДТВЕРЖДЕНИЯ
    await callback_query.message.answer(
        f"Теперь оплати {payment_text} ({price}₽):\n\n"
        f"1️⃣ Нажми кнопку ниже для оплаты через ЮMoney.\n"
        f"2️⃣ После оплаты вернись в бота и нажми кнопку '✅ Я оплатил(а)' внизу экрана.\n\n"
        f"{PHONE_PAYMENT_INFO}",
        reply_markup=payment_link_keyboard
    )
    
    # ✅ ОТПРАВЛЯЕМ REPLY-КЛАВИАТУРУ С ПОДТВЕРЖДЕНИЕМ
    await callback_query.message.answer(
        "После завершения оплаты нажми кнопку ниже:",
        reply_markup=payment_kb  # Это ReplyKeyboard из keyboards/reply.py
    )

    await state.set_state(IremelReg.waiting_for_payment)

# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ =====
@router.callback_query(F.data == "confirm_iremel_payment", IremelReg.waiting_for_payment)
async def iremel_payment_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение оплаты и завершение регистрации"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    reg_data = await state.get_data()
    
    all_data = load_data()
    user_info = all_data.get(user_id, {})
    
    # Сохраняем данные пользователя
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = reg_data.get("phone")
    user_info["username"] = callback_query.from_user.username
    
    user_info["iremel"] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payment_type": reg_data.get("payment_type"),
        "payment_amount": reg_data.get("payment_amount"),
        "diet_restrictions": reg_data.get("diet_restrictions", "Нет"),
        "preferences": reg_data.get("preferences", "Нет")
    }
    
    all_data[user_id] = user_info
    save_data(all_data)

    analytics.track_registration(message.from_user.id, "iremel")
    
    # Уведомление пользователю
    is_admin = user_id == str(ADMIN_ID)
    await callback_query.message.answer(
        "🎉 <b>Ты успешно зарегистрирован на Кэмп на Иремель!</b>\n\n"
        "📅 Даты: 28-30 ноября 2025\n"
        "🏔 Увидимся в горах! Готовься к приключению!\n\n"
        "Если у тебя появятся вопросы, напиши организатору: @AntonKorolev29",
        reply_markup=admin_kb if is_admin else main_kb,
        parse_mode="HTML"
    )

    await callback_query.message.answer(
        "Хочешь зарегистрировать другого человека?",
        reply_markup=register_friend_iremel_kb
    )
    
    # Уведомление админу
    payment_info = "50% (3750₽)" if reg_data.get("payment_type") == "prepay" else "100% (7500₽)"
    admin_text = (
        f"🔔 Новая регистрация на Иремель!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{callback_query.from_user.username if callback_query.from_user.username else 'N/A'}\n"
        f"💰 Вариант оплаты: {payment_info}\n"
        f"🍽 Ограничения: {reg_data.get('diet_restrictions', 'Нет')}\n"
        f"📝 Пожелания: {reg_data.get('preferences', 'Нет')}\n"
        f"ID: {user_id}"
    )
    
    try:
        await callback_query.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")
    
    await state.clear()


# ===== КНОПКА "НАЗАД" ИЗ ПРОЦЕССА ОПЛАТЫ =====
@router.callback_query(F.data == "back_from_iremel_payment")
async def back_from_iremel_payment(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат из процесса оплаты к выбору варианта"""
    await callback_query.answer()
    
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 50% (3750₽)", callback_data="iremel_pay_50")],
        [InlineKeyboardButton(text="💳 Оплатить 100% (7500₽)", callback_data="iremel_pay_100")]
    ])
    
    await callback_query.message.edit_text(
        "Выбери вариант оплаты:\n\n"
        "💰 <b>Оплатить 50%</b> — внеси предоплату 3750₽ сейчас, остаток до 20 ноября\n"
        "💰 <b>Оплатить 100%</b> — оплати полную стоимость 7500₽ сразу",
        reply_markup=payment_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(IremelReg.waiting_for_payment_option)

# ===== ЛИСТ ОЖИДАНИЯ =====
@router.callback_query(F.data == "iremel_waiting_list")
async def iremel_waiting_list_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало записи в лист ожидания"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    user_data = all_data.get(user_id, {})
    
    # Проверка профиля
    existing_name = user_data.get("name")
    existing_phone = user_data.get("phone")
    
    if existing_name and existing_phone:
        # Сохраняем в лист ожидания сразу
        await state.update_data(name=existing_name, phone=existing_phone)
        
        if user_id not in all_data:
            all_data[user_id] = {}
        
        all_data[user_id]["iremel"] = {
            "waiting_list": True,
            "waiting_list_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_data(all_data)
        
        # Уведомление админу
        admin_text = (
            f"📋 Новая запись в лист ожидания Иремель!\n\n"
            f"👤 {existing_name}\n"
            f"📞 {existing_phone}\n"
            f"Telegram: @{callback_query.from_user.username if callback_query.from_user.username else 'N/A'}\n"
            f"ID: {user_id}"
        )
        
        try:
            await callback_query.bot.send_message(ADMIN_ID, admin_text)
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
        
        await callback_query.message.answer(
            "✅ Ты добавлен в лист ожидания!\n\n"
            "Если освободится место, мы обязательно с тобой свяжемся.",
            reply_markup=admin_kb if user_id == str(ADMIN_ID) else main_kb
        )
        await state.clear()
        return
    
    # Если профиля нет - запрашиваем данные
    await callback_query.message.answer(
        "Для записи в лист ожидания введи своё полное имя (Фамилия Имя):",
        reply_markup=back_kb
    )
    await state.set_state(IremelReg.waiting_list_name)


@router.message(IremelReg.waiting_list_name)
async def iremel_waiting_list_name(message: types.Message, state: FSMContext):
    """Обработка имени для листа ожидания"""
    
    if message.text == "⬅️ Назад":
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        "Спасибо! Теперь нажми кнопку ниже, чтобы отправить свой номер телефона.",
        reply_markup=phone_kb
    )
    await state.set_state(IremelReg.waiting_list_phone)


@router.message(IremelReg.waiting_list_phone, F.contact)
async def iremel_waiting_list_phone(message: types.Message, state: FSMContext):
    """Обработка телефона для листа ожидания"""
    if not message.contact:
        await message.answer("Пожалуйста, используй кнопку для отправки номера.", reply_markup=phone_kb)
        return
    
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    
    all_data = load_data()
    user_info = all_data.get(user_id, {})
    
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = message.contact.phone_number
    user_info["username"] = message.from_user.username
    
    user_info["iremel"] = {
        "waiting_list": True,
        "waiting_list_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    all_data[user_id] = user_info
    save_data(all_data)
    
    # Уведомление админу
    admin_text = (
        f"📋 Новая запись в лист ожидания Иремель!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {message.contact.phone_number}\n"
        f"Telegram: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"ID: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")
    
    is_admin = user_id == str(ADMIN_ID)
    await message.answer(
        "✅ Ты добавлен в лист ожидания!\n\n"
        "Если освободится место, мы обязательно с тобой свяжемся.",
        reply_markup=admin_kb if is_admin else main_kb
    )
    await state.clear()

@router.callback_query(F.data == "iremel_participants")
async def show_iremel_participants(callback_query: types.CallbackQuery):
    """Показать список участников кэмпа"""
    await callback_query.answer()
    
    all_data = load_data()
    participants = []
    waiting_list = []
    
    for user_id, user_data in all_data.items():
        iremel_data = user_data.get("iremel", {})
        name = user_data.get("name", "Неизвестно")
        
        if iremel_data.get("is_registered"):
            participants.append(name)
        elif iremel_data.get("waiting_list"):
            waiting_list.append(name)
    
    text = f"🏔 <b>Участники кэмпа на Иремель</b>\n\n"
    text += f"✅ Зарегистрировано: {len(participants)} из {IREMEL_MAX_PARTICIPANTS}\n\n"
    
    if participants:
        for i, p in enumerate(participants, 1):
            text += f"{i}. {p}\n"
    else:
        text += "Пока никто не зарегистрировался.\n"
    
    if waiting_list:
        text += f"\n\n📋 <b>Лист ожидания ({len(waiting_list)}):</b>\n"
        for i, p in enumerate(waiting_list, 1):
            text += f"{i}. {p}\n"
    
    await callback_query.message.answer(text, parse_mode="HTML")

# ===== ОБРАБОТЧИК REPLY-КНОПКИ "Я ОПЛАТИЛ(А)" =====
@router.message(F.text == "✅ Я оплатил(а)", StateFilter(IremelReg.waiting_for_payment))
async def iremel_payment_confirm_reply(message: types.Message, state: FSMContext):
    """Подтверждение оплаты через Reply-кнопку"""
    await iremel_payment_confirm_logic(message, state)

# Вынесем логику в отдельную функцию для переиспользования
async def iremel_payment_confirm_logic(message_or_callback, state: FSMContext):
    """Общая логика подтверждения оплаты"""
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.answer()
        message = message_or_callback.message
        user = message_or_callback.from_user
        bot = message_or_callback.bot
    else:
        message = message_or_callback
        user = message.from_user
        bot = message.bot
    
    user_id = str(user.id)
    reg_data = await state.get_data()
    all_data = load_data()
    user_info = all_data.get(user_id, {})

    # Сохраняем данные
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = reg_data.get("phone")
    user_info["username"] = user.username
    user_info["iremel"] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payment_type": reg_data.get("payment_type"),
        "payment_amount": reg_data.get("payment_amount"),
        "diet_restrictions": reg_data.get("diet_restrictions", "Нет"),
        "preferences": reg_data.get("preferences", "Нет")
    }

    all_data[user_id] = user_info
    save_data(all_data)

    # Уведомление пользователю
    is_admin = user_id == str(ADMIN_ID)
    await message.answer(
        "🎉 Ты успешно зарегистрирован на Кэмп на Иремель!\n\n"
        "📅 Даты: 28-30 ноября 2025\n"
        "🏔 Увидимся в горах! Готовься к приключению!\n\n"
        "Если у тебя появятся вопросы, напиши организатору: @AntonKorolev29",
        reply_markup=admin_kb if is_admin else main_kb,
        parse_mode="HTML"
    )

    await message.answer(
        "Хочешь зарегистрировать другого человека?",
        reply_markup=register_friend_iremel_kb
    )


    # Уведомление админу
    payment_info = "50% (3750₽)" if reg_data.get("payment_type") == "prepay" else "100% (7500₽)"
    admin_text = (
        f"🔔 Новая регистрация на Иремель!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{user.username if user.username else 'N/A'}\n"
        f"💰 Вариант оплаты: {payment_info}\n"
        f"🍽 Ограничения: {reg_data.get('diet_restrictions', 'Нет')}\n"
        f"📝 Пожелания: {reg_data.get('preferences', 'Нет')}\n"
        f"ID: {user_id}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")

    await state.clear()

# Обновляем обработчик callback для использования общей логики
@router.callback_query(F.data == "confirm_iremel_payment", IremelReg.waiting_for_payment)
async def iremel_payment_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение оплаты через InlineButton"""
    await iremel_payment_confirm_logic(callback_query, state)

# ===== РЕГИСТРАЦИЯ ДРУГА НА ИРЕМЕЛЬ =====

@router.callback_query(F.data == "register_friend_iremel")
async def iremel_register_friend_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации друга на Иремель"""
    await callback_query.answer()
    await callback_query.message.answer(
        "👥 Регистрация другого человека на Иремель Кэмп\n\n"
        "Введи имя и фамилию участника:",
        reply_markup=back_kb
    )
    await state.set_state(IremelReg.friend_waiting_for_name)


@router.callback_query(F.data == "back_to_main_menu_iremel")
async def back_to_main_from_friend_iremel(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await callback_query.answer()
    await state.clear()
    user_id = str(callback_query.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    await callback_query.message.edit_text("Возвращаю в главное меню.")
    await callback_query.message.answer(
        "Главное меню:",
        reply_markup=admin_kb if is_admin else main_kb
    )


# ===== ИМЯ ДРУГА =====
@router.message(IremelReg.friend_waiting_for_name, F.text)
async def iremel_friend_name(message: types.Message, state: FSMContext):
    """Запрос имени друга"""
   
    if message.text == "⬅️ Назад":
        await state.clear()
        is_admin = str(message.from_user.id) == str(ADMIN_ID)
        await message.answer("Регистрация отменена.", reply_markup=admin_kb if is_admin else main_kb)
        return
    
    # ✅ ВАЛИДАЦИЯ ИМЕНИ ДРУГА
    from utils.validators import validate_name
    is_valid, result = validate_name(message.text)
    
    if not is_valid:
        await message.answer(result, reply_markup=back_kb)
        return
    
    friend_name = result  # Отформатированное имя
    await state.update_data(friend_name=friend_name)
    
    await message.answer(
        f"✅ Имя участника: {friend_name}\n\n"
        "Теперь введи номер телефона участника:\n"
        "(например: +7 999 123 45 67)",
        reply_markup=back_kb
    )
    await state.set_state(IremelReg.friend_waiting_for_phone)


# ===== ТЕЛЕФОН ДРУГА =====
@router.message(IremelReg.friend_waiting_for_phone, F.text)
async def iremel_friend_phone(message: types.Message, state: FSMContext):
    """Запрос телефона друга"""
    
    if message.text == "⬅️ Назад":
        await message.answer("Введи имя и фамилию участника:", reply_markup=back_kb)
        await state.set_state(IremelReg.friend_waiting_for_name)
        return
    
    # ✅ ВАЛИДАЦИЯ ТЕЛЕФОНА ДРУГА
    from utils.validators import validate_phone
    is_valid, result = validate_phone(message.text)
    
    if not is_valid:
        await message.answer(result, reply_markup=back_kb)
        return
    
    friend_phone = result  # Отформатированный номер
    await state.update_data(friend_phone=friend_phone)
    
    # Клавиатура выбора оплаты для друга
    friend_payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Разовая регистрация (200₽)", callback_data="friend_payment_onetime")],
        [InlineKeyboardButton(text="🎟 Месячный абонемент (600₽)", callback_data="friend_payment_monthly")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_from_friend_payment")]
    ])
    
    reg_data = await state.get_data()
    await message.answer(
        f"✅ Участник:\n"
        f"👤 {reg_data.get('friend_name')}\n"
        f"📞 {friend_phone}\n\n"
        "Выбери тип оплаты:",
        reply_markup=friend_payment_kb
    )
    await state.set_state(IremelReg.friend_waiting_for_payment_option)


# ===== ВЫБОР ВАРИАНТА ОПЛАТЫ =====
@router.callback_query(IremelReg.friend_waiting_for_payment_option)
async def iremel_friend_payment_option(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора варианта оплаты для друга"""
    await callback_query.answer()
    
    if callback_query.data == "back_from_friend_iremel_payment":
        await callback_query.message.answer(
            "Есть ли особые пожелания?",
            reply_markup=back_kb
        )
        await state.set_state(IremelReg.friend_waiting_for_preferences)
        return
    
    payment_option = callback_query.data
    
    if payment_option == "friend_iremel_pay_50":
        price = 3750
        payment_link = IREMEL_PAYMENT_50
        payment_text = "предоплату 50%"
        payment_type = "prepay"
    else:  # friend_iremel_pay_100
        price = 7500
        payment_link = IREMEL_PAYMENT_100
        payment_text = "полную оплату"
        payment_type = "full"
    
    await state.update_data(friend_payment_type=payment_type, friend_payment_amount=price)
    
    # Кликабельная ссылка на оплату
    payment_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", url=payment_link)]
    ])
    
    await callback_query.message.answer(
        f"💳 Оплата {payment_text} ({price}₽) за другого человека\n\n"
        f"1️⃣ Нажми кнопку ниже для оплаты через ЮMoney.\n"
        f"2️⃣ После оплаты вернись в бота и нажми '✅ Я оплатил(а)' внизу экрана.\n\n"
        f"{PHONE_PAYMENT_INFO}",
        reply_markup=payment_link_keyboard
    )
    
    await callback_query.message.answer(
        "После завершения оплаты нажми кнопку ниже:",
        reply_markup=payment_kb
    )
    
    await state.set_state(IremelReg.friend_waiting_for_payment)


# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ЗА ДРУГА =====
@router.message(F.text == "✅ Я оплатил(а)", IremelReg.friend_waiting_for_payment)
async def iremel_friend_payment_confirm(message: types.Message, state: FSMContext):
    """Подтверждение оплаты за друга на Иремель"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    all_data = load_data()
    
    # Получаем данные регистратора
    registrator_name = all_data.get(user_id, {}).get("name", "Неизвестно")
    
    # Создаём уникальный ID для друга
    friend_phone = reg_data.get("friend_phone", "")
    friend_id = f"friend_iremel_{abs(hash(friend_phone)) % 1000000}"
    
    # Сохраняем данные друга
    all_data[friend_id] = {
        "name": reg_data.get("friend_name"),
        "phone": reg_data.get("friend_phone"),
        "registered_by": user_id,
        "registered_by_name": registrator_name,
        "username": None,
        "iremel": {
            "is_registered": True,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payment_type": reg_data.get("friend_payment_type"),
            "payment_amount": reg_data.get("friend_payment_amount"),
            "diet_restrictions": reg_data.get("friend_diet", "Нет"),
            "preferences": reg_data.get("friend_preferences", "Нет")
        }
    }
    
    save_data(all_data)
    
    # Уведомление пользователю
    is_admin = user_id == str(ADMIN_ID)
    payment_info = "50% (3750₽)" if reg_data.get("friend_payment_type") == "prepay" else "100% (7500₽)"
    
    await message.answer(
        f"✅ {reg_data.get('friend_name')} успешно зарегистрирован(а) на Иремель Кэмп!\n"
        f"💰 Оплата: {payment_info}\n\n"
        "Хочешь зарегистрировать ещё кого-то?",
        reply_markup=register_friend_iremel_kb
    )
    
    # Уведомление админу
    admin_text = (
        f"🔔 Новая регистрация на Иремель (через друга)!\n\n"
        f"👤 {reg_data.get('friend_name')}\n"
        f"📞 {reg_data.get('friend_phone')}\n"
        f"💰 Вариант оплаты: {payment_info}\n"
        f"🍽 Ограничения: {reg_data.get('friend_diet', 'Нет')}\n"
        f"📝 Пожелания: {reg_data.get('friend_preferences', 'Нет')}\n"
        f"🙋 Зарегистрировал: {registrator_name} (@{message.from_user.username if message.from_user.username else 'N/A'})\n"
        f"ID регистратора: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")
    
    await state.clear()

