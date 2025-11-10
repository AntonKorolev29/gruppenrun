from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from keyboards.reply import main_kb, admin_kb, back_kb, phone_kb, payment_kb
from datetime import datetime, timedelta, date
from utils.helpers import load_data, save_data, get_next_sunday, get_current_gruppenrun_number
from config import ADMIN_ID, PAYMENT_LINK, PAYMENT_MONTH_LINK, PHONE_PAYMENT_INFO, PHOTO_GRUPPENRUN_COVER
from utils.analytics import analytics
from config import PAYMENT_DETAILS


router = Router()

# FSM состояния
class GruppenrunReg(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_payment_type = State()
    waiting_for_payment = State()
    
    # ✅ НОВЫЕ СОСТОЯНИЯ ДЛЯ РЕГИСТРАЦИИ ДРУГА
    friend_waiting_for_name = State()
    friend_waiting_for_phone = State()
    friend_waiting_for_payment_type = State()
    friend_waiting_for_payment = State()

# Клавиатура для отправки номера телефона
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура выбора типа оплаты
payment_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💰 Разовая регистрация (200₽)", callback_data="payment_onetime")],
        [InlineKeyboardButton(text="🎟 Месячный абонемент (600₽)", callback_data="payment_monthly")]
    ]
)

# Клавиатура с предложением зарегистрировать друга
register_friend_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Зарегистрировать друга/подругу", callback_data="register_friend_gruppenrun")],
    [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main_menu")]
])


# ===== РЕГИСТРАЦИЯ НА ГРУППЕНРАН =====
@router.message(F.text == "⚪ Группенран Шарташ", StateFilter(None))
async def gruppenrun_register(message: types.Message, state: FSMContext):
    """Показывает информацию о Группенран Шарташ (независимо от регистрации)"""
    
    await message.answer_photo(
        photo=PHOTO_GRUPPENRUN_COVER,
        caption=GRUPPENRUN_MAIN_TEXT,
        parse_mode="HTML",
        reply_markup=shartas_main_kb
    )


@router.callback_query(F.data == "gruppenrun_register")
async def gruppenrun_register(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации на Группенран (после нажатия кнопки "Зарегистрироваться")"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    
    # Получаем дату и номер ближайшего Группенрана
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    
    user_data = all_data.get(user_id, {})
    gruppenrun_data = user_data.get("gruppenrun", {})
    
    # Проверка активной регистрации
    if gruppenrun_data.get("is_registered"):
        reg_type = gruppenrun_data.get("type", "onetime")
        
        if reg_type == "monthly":
            valid_until = gruppenrun_data.get("valid_until")
            if valid_until:
                try:
                    valid_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
                    if datetime.now().date() <= valid_date:
                        await callback_query.message.answer(
                            f"✅ У тебя уже есть активный месячный абонемент!\n\n"
                            f"Действителен до: {valid_date.strftime('%d.%m.%Y')}\n\n"
                            f"Ближайший Группенран: №{next_gruppenrun_number} ({next_gruppenrun_date_str})\n"
                            f"Хочешь зарегистрировать друга/подругу?",
                            reply_markup=register_friend_kb
                        )
                        return
                except:
                    pass
        else:
            reg_date = gruppenrun_data.get("registration_for_date")
            if reg_date == next_gruppenrun_date_str:
                await callback_query.message.answer(
                    f"✅ Ты уже зарегистрирован на Группенран №{next_gruppenrun_number} ({next_gruppenrun_date_str})!\n"
                    f"Хочешь зарегистрировать друга/подругу?",
                    reply_markup=register_friend_kb
                )
                return
    
    # ПРОВЕРКА ПРОФИЛЯ: если есть имя и телефон - пропускаем их запрос
    existing_name = user_data.get("name")
    existing_phone = user_data.get("phone")
    
    if existing_name and existing_phone:
        # Сохраняем данные в state
        await state.update_data(name=existing_name, phone=existing_phone)
        
        # Сразу переходим к выбору типа оплаты
        await callback_query.message.answer(
            "Отлично! Теперь выбери тип регистрации:",
            reply_markup=payment_type_kb
        )
        await state.set_state(GruppenrunReg.waiting_for_payment_type)
        return
    
    # Начало новой регистрации - ОТПРАВЛЯЕМ ФОТО-ОБЛОЖКУ
    try:
        await callback_query.message.answer_photo(
            photo=PHOTO_GRUPPENRUN_COVER,
            caption=(
                f"🏃 Регистрация на Группенран №{next_gruppenrun_number}\n"
                f"📅 Дата: {next_gruppenrun_date_str}\n\n"
                f"Введи свои Фамилию и Имя (они сохранятся в твоем профиле и в следующий раз их не нужно будет вводить заново):"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        # Если фото не загружается, отправляем текст без фото
        print(f"Ошибка загрузки обложки Группенрана: {e}")
        await callback_query.message.answer(
            f"Регистрация на Группенран №{next_gruppenrun_number}\n"
            f"📅 Дата: {next_gruppenrun_date_str}\n\n"
            f"Введи свои Фамилию и Имя:"
        )
    
    await state.set_state(GruppenrunReg.waiting_for_name)

@router.message(GruppenrunReg.waiting_for_name)
async def gruppenrun_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени с валидацией"""
    
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
    await state.set_state(GruppenrunReg.waiting_for_phone)

@router.message(GruppenrunReg.waiting_for_phone, F.text)
async def gruppenrun_phone_text(message: types.Message, state: FSMContext):
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
    await state.set_state(GruppenrunReg.waiting_for_payment_type)

@router.message(GruppenrunReg.waiting_for_phone, F.contact)
async def gruppenrun_phone(message: types.Message, state: FSMContext):
    """Обработка получения номера телефона"""

    if not message.contact:
        await message.answer(
            "Пожалуйста, используй кнопку для отправки номера или введи его вручную.",
            reply_markup=phone_kb
        )
        return    

    phone=message.contact.phone_number
    
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
    await state.set_state(GruppenrunReg.waiting_for_payment_type)


# ===== ВЫБОР ТИПА ОПЛАТЫ =====
@router.callback_query(GruppenrunReg.waiting_for_payment_type)
async def gruppenrun_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа оплаты"""
    await callback_query.answer()
    payment_type = callback_query.data
    await state.update_data(payment_type=payment_type)
    
    if payment_type == "payment_onetime":
        payment_link = PAYMENT_LINK
        price = 200
        payment_text = "разовую оплату"
    else:  # payment_monthly
        payment_link = PAYMENT_MONTH_LINK
        price = 600
        payment_text = "месячный абонемент"
    
    # ✅ СОЗДАЁМ INLINE-КЛАВИАТУРУ С КЛИКАБЕЛЬНОЙ ССЫЛКОЙ
    payment_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", url=payment_link)]
    ])
    
    # Отправляем сообщение с INLINE-кнопкой для оплаты
    await callback_query.message.answer(
        f"💳 Оплата {payment_text} ({price}₽)\n\n"
        f"1️⃣ Нажми кнопку ниже для оплаты через ЮMoney.\n"
        f"2️⃣ После оплаты вернись в бота и нажми '✅ Я оплатил(а)' внизу экрана.\n\n"
        f"{PHONE_PAYMENT_INFO}",
        parse_mode="HTML",
        reply_markup=payment_link_keyboard  # ← INLINE-кнопка с ссылкой
    )
    
    # ✅ ОТДЕЛЬНО ОТПРАВЛЯЕМ REPLY-КЛАВИАТУРУ С ПОДТВЕРЖДЕНИЕМ
    await callback_query.message.answer(
        "После завершения оплаты нажми кнопку ниже:",
        reply_markup=payment_kb  # ← REPLY-кнопка "✅ Я оплатил(а)"
    )
    
    await state.set_state(GruppenrunReg.waiting_for_payment)

# ===== ОТМЕНА РЕГИСТРАЦИИ =====
@router.callback_query(F.data == "cancel_registration")
async def cancel_registration_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик отмены регистрации"""
    await callback_query.answer()
    await state.clear()
    
    user_id = str(callback_query.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    await callback_query.message.edit_text(
        "❌ Регистрация отменена.\n\n"
        "Ты можешь начать регистрацию снова в любое время!"
    )
    
    await callback_query.message.answer(
        "Главное меню:",
        reply_markup=admin_kb if is_admin else main_kb
    )

# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ЧЕРЕЗ INLINE КНОПКУ =====
@router.callback_query(F.data == "confirm_payment", GruppenrunReg.waiting_for_payment)
async def gruppenrun_payment_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение оплаты через inline кнопку"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    reg_data = await state.get_data()
    
    all_data = load_data()
    user_info = all_data.get(user_id, {})
    
    reg_type = reg_data.get("payment_type", "onetime")
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    
    # Сохраняем данные пользователя
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = reg_data.get("phone")
    user_info["username"] = callback_query.from_user.username
    
    user_info["gruppenrun"] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "monthly" if reg_type == "payment_monthly" else "onetime",
        "valid_until": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") if reg_type == "payment_monthly" else None,
        "registration_for_date": next_gruppenrun_date_str if reg_type == "payment_onetime" else None,
        "gruppenrun_number": next_gruppenrun_number if reg_type == "payment_onetime" else None
    }
    
    all_data[user_id] = user_info
    save_data(all_data)

    analytics.track_registration(message.from_user.id, "gruppenrun")
    
    # Формируем сообщение пользователю
    reg_info_text = f"Группенран №{next_gruppenrun_number} ({next_gruppenrun_date_str})"
    if reg_type == "payment_monthly":
        valid_until_str = user_info["gruppenrun"]["valid_until"]
        if valid_until_str:
            reg_info_text = f"Месячный абонемент! Действителен до {datetime.strptime(valid_until_str, '%Y-%m-%d').strftime('%d.%m.%Y')}"

    is_admin = user_id == str(ADMIN_ID)
    
    await callback_query.message.edit_text(
        f"🎉 Регистрация завершена!\n"
        f"{reg_info_text}.\n\n"
        f"Увидимся на пробежке! 🏃‍♂️"
    )
    
    # Предложение заказать завтрак
    await callback_query.message.answer(
        "Хочешь заказать завтрак после пробежки?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Да, заказать завтрак", callback_data="order_breakfast")],
            [InlineKeyboardButton(text="❌ Нет, спасибо", callback_data="skip_breakfast")]
        ])
    )
    
    # Уведомление администратору
    admin_text = (
        f"🔔 Новая регистрация на Группенран!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{callback_query.from_user.username if callback_query.from_user.username else 'N/A'}\n"
        f"{'📅 Месячный абонемент' if reg_type == 'payment_monthly' else f'📅 Разовая регистрация на №{next_gruppenrun_number}'}\n"
        f"ID: {user_id}"
    )
    
    try:
        await callback_query.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления администратору: {e}")
    
    await state.clear()


# ===== ОБРАБОТЧИК ОТКАЗА ОТ ЗАВТРАКА =====
@router.callback_query(F.data == "skip_breakfast")
async def skip_breakfast_handler(callback_query: types.CallbackQuery):
    """Обработчик отказа от заказа завтрака"""
    await callback_query.answer()
    await callback_query.message.edit_text("Хорошо! Увидимся на пробежке! 🏃")

# ===== ОБРАБОТЧИК REPLY-КНОПКИ "Я ОПЛАТИЛ(А)" =====
@router.message(F.text == "✅ Я оплатил(а)", GruppenrunReg.waiting_for_payment)
async def gruppenrun_payment_confirm_reply(message: types.Message, state: FSMContext):
    """Подтверждение оплаты через Reply-кнопку"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    
    all_data = load_data()
    user_info = all_data.get(user_id, {})
    
    reg_type = reg_data.get("payment_type", "onetime")
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    
    # Сохраняем данные пользователя
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = reg_data.get("phone")
    user_info["username"] = message.from_user.username
    
    from datetime import date, timedelta
    
    user_info["gruppenrun"] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "monthly" if reg_type == "payment_monthly" else "onetime",
        "valid_until": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") if reg_type == "payment_monthly" else None,
        "registration_for_date": next_gruppenrun_date_str if reg_type == "payment_onetime" else None,
        "gruppenrun_number": next_gruppenrun_number if reg_type == "payment_onetime" else None
    }
    
    all_data[user_id] = user_info
    save_data(all_data)
    
    # Формируем сообщение пользователю
    reg_info_text = f"Группенран №{next_gruppenrun_number} ({next_gruppenrun_date_str})"
    if reg_type == "payment_monthly":
        valid_until_str = user_info["gruppenrun"]["valid_until"]
        if valid_until_str:
            reg_info_text = f"Месячный абонемент! Действителен до {datetime.strptime(valid_until_str, '%Y-%m-%d').strftime('%d.%m.%Y')}"

    is_admin = user_id == str(ADMIN_ID)
    
    await message.answer(
        f"🎉 Регистрация завершена!\n"
        f"{reg_info_text}.\n\n"
        f"Увидимся на пробежке! 🏃♂️",
        reply_markup=admin_kb if is_admin else main_kb
    )

    # ✅ ПРЕДЛОЖЕНИЕ ЗАРЕГИСТРИРОВАТЬ ДРУГА
    await message.answer(
        "Хочешь зарегистрировать ещё кого-то (друга/подругу)?",
        reply_markup=register_friend_kb
    )

    
    # Предложение заказать завтрак
    await message.answer(
        "Хочешь заказать завтрак после пробежки?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Да, заказать завтрак", callback_data="order_breakfast")],
            [InlineKeyboardButton(text="❌ Нет, спасибо", callback_data="skip_breakfast")]
        ])
    )
    
    # Уведомление администратору
    admin_text = (
        f"🔔 Новая регистрация на Группенран!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"{'📅 Месячный абонемент' if reg_type == 'payment_monthly' else f'📅 Разовая регистрация на №{next_gruppenrun_number}'}\n"
        f"ID: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления администратору: {e}")
    
    await state.clear()

# ===== УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК КНОПКИ "НАЗАД" =====
@router.message(F.text == "⬅️ Назад", StateFilter(
    GruppenrunReg.waiting_for_name,
    GruppenrunReg.waiting_for_phone,
    GruppenrunReg.waiting_for_payment_type,
    GruppenrunReg.waiting_for_payment
))
async def back_button_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Назад во время регистрации"""
    current_state = await state.get_state()
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    # Если на этапе оплаты - возвращаемся к выбору типа
    if current_state == "GruppenrunReg:waiting_for_payment":
        await message.answer(
            "Возвращаемся к выбору типа регистрации.\n\n"
            "Выбери тип регистрации:",
            reply_markup=payment_type_kb
        )
        await state.set_state(GruppenrunReg.waiting_for_payment_type)
        return
    
    # Для остальных состояний - полная отмена
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )

# ===== РЕГИСТРАЦИЯ ДРУГА =====

@router.callback_query(F.data == "register_friend_gruppenrun")
async def gruppenrun_register_friend_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации друга на Группенран"""
    await callback_query.answer()
    await callback_query.message.answer(
        "👥 Регистрация друга/подруги\n\n"
        "Введи имя и фамилию участника:",
        reply_markup=back_kb
    )
    await state.set_state(GruppenrunReg.friend_waiting_for_name)


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_from_friend(callback_query: types.CallbackQuery, state: FSMContext):
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
@router.message(GruppenrunReg.friend_waiting_for_name, F.text)
async def gruppenrun_friend_name(message: types.Message, state: FSMContext):
    """Запрос имени друга с валидацией"""
    
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
    await state.set_state(GruppenrunReg.friend_waiting_for_phone)

# ===== ТЕЛЕФОН ДРУГА =====
@router.message(GruppenrunReg.friend_waiting_for_phone, F.text)
async def gruppenrun_friend_phone(message: types.Message, state: FSMContext):
    """Запрос телефона друга с валидацией"""
    
    if message.text == "⬅️ Назад":
        await message.answer("Введи имя и фамилию участника:", reply_markup=back_kb)
        await state.set_state(GruppenrunReg.friend_waiting_for_name)
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
    await state.set_state(GruppenrunReg.friend_waiting_for_payment_type)

# ===== ВЫБОР ТИПА ОПЛАТЫ ДЛЯ ДРУГА =====
@router.callback_query(GruppenrunReg.friend_waiting_for_payment_type)
async def gruppenrun_friend_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа оплаты для друга"""
    await callback_query.answer()
    
    if callback_query.data == "back_from_friend_payment":
        await callback_query.message.answer(
            "Введи номер телефона участника:",
            reply_markup=back_kb
        )
        await state.set_state(GruppenrunReg.friend_waiting_for_phone)
        return
    
    payment_type = callback_query.data
    await state.update_data(friend_payment_type=payment_type)
    
    if payment_type == "friend_payment_onetime":
        payment_link = PAYMENT_LINK
        price = 200
        payment_text = "разовую оплату"
    else:  # friend_payment_monthly
        payment_link = PAYMENT_MONTH_LINK
        price = 600
        payment_text = "месячный абонемент"
    
    # Кликабельная ссылка на оплату
    payment_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", url=payment_link)]
    ])
    
    await callback_query.message.answer(
        f"💳 Оплата {payment_text} ({price}₽) за друга\n\n"
        f"1️⃣ Нажми кнопку ниже для оплаты через ЮMoney.\n"
        f"2️⃣ После оплаты вернись в бота и нажми '✅ Я оплатил(а)' внизу экрана.\n\n"
        f"{PAYMENT_DETAILS}",
        parse_mode="HTML",
        reply_markup=payment_link_keyboard
    )
    
    await callback_query.message.answer(
        "После завершения оплаты нажми кнопку ниже:",
        reply_markup=payment_kb
    )
    
    await state.set_state(GruppenrunReg.friend_waiting_for_payment)


# ===== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ЗА ДРУГА =====
@router.message(F.text == "✅ Я оплатил(а)", GruppenrunReg.friend_waiting_for_payment)
async def gruppenrun_friend_payment_confirm(message: types.Message, state: FSMContext):
    """Подтверждение оплаты за друга"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    all_data = load_data()
    
    # Получаем данные регистратора
    registrator_name = all_data.get(user_id, {}).get("name", "Неизвестно")
    
    # Создаём уникальный ID для друга
    friend_phone = reg_data.get("friend_phone", "")
    friend_id = f"friend_{abs(hash(friend_phone)) % 1000000}"
    
    # Определяем тип оплаты
    payment_type = reg_data.get("friend_payment_type", "friend_payment_onetime")
    reg_type = "monthly" if "monthly" in payment_type else "onetime"
    
    next_gruppenrun_date_str = get_next_sunday()
    next_gruppenrun_date_obj = datetime.strptime(next_gruppenrun_date_str, "%d.%m.%Y").date()
    next_gruppenrun_number = get_current_gruppenrun_number(next_gruppenrun_date_obj)
    
    # Сохраняем данные друга
    all_data[friend_id] = {
        "name": reg_data.get("friend_name"),
        "phone": reg_data.get("friend_phone"),
        "registered_by": user_id,
        "registered_by_name": registrator_name,
        "username": None,  # У друга нет telegram username
        "gruppenrun": {
            "is_registered": True,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": reg_type,
            "valid_until": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") if reg_type == "monthly" else None,
            "registration_for_date": next_gruppenrun_date_str if reg_type == "onetime" else None,
            "gruppenrun_number": next_gruppenrun_number if reg_type == "onetime" else None
        }
    }
    
    save_data(all_data)
    
    # Уведомление пользователю
    is_admin = user_id == str(ADMIN_ID)
    reg_info = f"Месячный абонемент" if reg_type == "monthly" else f"Группенран №{next_gruppenrun_number}"
    
    await message.answer(
        f"✅ {reg_data.get('friend_name')} успешно зарегистрирован(а)!\n"
        f"📅 {reg_info}\n\n"
        "Хочешь зарегистрировать ещё кого-то?",
        reply_markup=register_friend_kb
    )

# ===== ИНФОРМАЦИЯ О ГРУППЕНРАН ШАРТАШ =====

# Текст для краткого сообщения в главном меню
GRUPPENRUN_MAIN_TEXT = (
    "<b>Группенран Шарташ</b>\n\n"
    "Мы бегаем длительные тренировки, разбиваясь на группы по темпу, в соответствии с личными планами и уровнем подготовки.\n\n"
    "🏃 Группы формируются по темпу бега:\n"
    "4:30 мин/км — быстрые\n"
    "5:00-5:30 мин/км — динамичные\n"
    "6:00-6:30 мин/км — средние\n"
    "7:00+ мин/км — комфортные\n\n"
    "🗺️ Маршруты и расстояния\n"
    "Классический маршрут = 14,4 км\n"
    "4,7 км по асфальту до лесного круга\n"
    "+ 5 км круг по грунту (можно несколько)\n"
    "+ 4,7 км обратно до базы\n"
    "Добавляя 1-2 круга по лесу, можно пробежать 20-25 км\n\n"
    "🏘️ База и комфорт\n"
    "• Можно переодеться в тепле, оставить вещи\n"
    "• Позавтракать после тренировки в кафе\n"
    "• Пообщаться с единомышленниками и найти друзей"
)

# Полный текст для кнопки "Подробнее"
GRUPPENRUN_FULL_TEXT = (
    "🏃 ГРУППЕНРАН ШАРТАШ\n\n"
    
    "💪 Что такое Группенран?\n"
    "Группенран — это то место, где можно найти компанию на любой темп и километраж. "
    "Неважно, быстро ты бегаешь или медленно, на 10 км или на 25 км — для тебя найдется группа по душе и по возможностям.\n\n"
    
    "📖 История\n"
    "Группенран появился в 2019 году с простой, но мощной идеей — бегать длительные тренировки в группе, "
    "тянуться друг за другом и поддерживать мотивацию. \n"
    "Постепенно, с ростом количества желающих разного уровня подготовки, мы выделили разные группы по темпу, "
    "чтобы каждый мог найти свою компанию.\n\n"
    
    "🏃 Группы формируются по темпу бега и стартуют друг за другом:\n"
    "4:30 мин/км — быстрые\n"
    "5:00-5:30 мин/км — динамичные\n"
    "6:00-6:30 мин/км — средние\n"
    "7:00+ мин/км — комфортные\n\n"
    
    "🗺️ Маршруты и расстояния\n"
    "Наш классический маршрут составляет 14,5 км\n"
    "4,7 км по асфальту \n"
    "+ 5 км круг по грунту (лес) \n"
    "+ 4,7 км обратно до базы\n\n"
    
    "Сколько кругов пробежать, решает каждый сам.\n"
    "Это зависит от твоего индивидуального плана подготовки: 10 - 15 - 20 - 25...\n"
    "Полная свобода выбора — никакого давления!\n\n"
    
    "🏘️ База и комфорт\n"
    "На территории базы «Мыс Рундук» (оз. Шарташ, ул. Отдыха 25) ты найдешь всё необходимое:\n"
    "✅ Переодеться в тепле, оставить вещи\n"
    "✅ Позавтракать после тренировки в кафе\n"
    "✅ Посидеть, отдышаться, восстановиться\n"
    "✅ Пообщаться с единомышленниками и завести новых друзей\n\n"
    
    "👨‍👩‍👧‍👦 Детское комьюнити\n"
    "На территории базы целый новый мир для детей:\n"
    "🛝 Детская площадка\n"
    "🎪 Безлимитные батуты в летний сезон\n"
    "🚧 Огороженная территория — безопасно и спокойно\n\n"
    
    "Пока вы бежите свой маршрут, дети играют в безопасной, организованной среде. "
    "Отличное решение для семей, где хочется и спортом заняться, и с детьми время провести!"
)


shartas_main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Зарегистрироваться", callback_data="gruppenrun_register")],
    [InlineKeyboardButton(text="📖 О проекте", callback_data="shartas_about")],
    [InlineKeyboardButton(text="📍 Как добраться", callback_data="shartas_location")],
    
])

shartas_back_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shartas_menu")],
])


@router.callback_query(F.data == "shartas_about")
async def shartas_about_callback(callback_query: types.CallbackQuery):
    """Полная информация о Группенран (БЕЗ фото)"""
    await callback_query.answer()
    
    shartas_back_kb_only = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shartas_menu")],
    ])
    
    await callback_query.message.answer(
        text=GRUPPENRUN_FULL_TEXT,
        parse_mode="HTML",
        reply_markup=shartas_back_kb_only
    )


@router.callback_query(F.data == "shartas_location")
async def shartas_location_callback(callback_query: types.CallbackQuery):
    """Информация о том, как добраться (БЕЗ фото)"""
    await callback_query.answer()
    
    location_text = (
        "📍 КАК ДОБРАТЬСЯ\n\n"
        "Парк Шарташские Каменные палатки\n"
        "База: оз. Шарташ, «Мыс Рундук», ул. Отдыха 25\n\n"
        "🚌 На общественном транспорте:\n"
        "Остановка Дачная, от неё ~1 км пешком\n\n"
        "🚗 На машине:\n"
        "Парковка на территории базы и рядом с ней\n\n"
        "⏱️ Рекомендуем приходить за 15–20 минут до старта"
    )
    
    location_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗺 Шарташ на Яндекс Картах",
            url="https://yandex.ru/maps/54/yekaterinburg/?ll=60.691136%2C56.865335&mode=poi&poi%5Bpoint%5D=60.691830%2C56.865204&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D1321450878&z=18.36"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shartas_menu")],
    ])
    
    await callback_query.message.answer(
        text=location_text,
        parse_mode="HTML",
        reply_markup=location_keyboard
    )

@router.callback_query(F.data == "back_to_shartas_menu")
async def back_to_shartas_menu(callback_query: types.CallbackQuery):
    """Возврат в главное меню с фото"""
    await callback_query.answer()
    
    await callback_query.message.answer_photo(
        photo=PHOTO_GRUPPENRUN_COVER,
        caption=GRUPPENRUN_MAIN_TEXT,
        parse_mode="HTML",
        reply_markup=shartas_main_kb
    )