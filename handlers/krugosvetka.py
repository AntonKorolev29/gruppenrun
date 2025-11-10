from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from keyboards.reply import main_kb, admin_kb, back_kb, phone_kb, payment_kb
from utils.helpers import load_data, escape_markdown, save_data
from config import ADMIN_ID, KRUGOSVETKA_PAYMENT_LINK, KRUGOSVETKA_SUPPORT_PAYMENT_LINK, PHONE_PAYMENT_INFO, TRACK_LINK, KRUGOSVETKA_TABLE_LINK, PHOTO_KRUGOSVETKA_COVER
from datetime import datetime
import logging
from utils.analytics import analytics

router = Router()

# Этапы Кругосветки
krugosvetka_stages = [
    ("1️⃣ Шарташ - Сибирский тракт, 12,7 км", "stage_1"),
    ("2️⃣ Сибирский тракт - Уктус, 10,2 км", "stage_2"),
    ("3️⃣ Уктус - Амундсена, 7,3 км", "stage_3"),
    ("4️⃣ Амундсена - Мега, 8,2 км", "stage_4"),
    ("5️⃣ Мега - Палкинский Торфяник, 8,7 км", "stage_5"),
    ("6️⃣ Палкинский Торфяник - 7 ключей, 13,3 км", "stage_6"),
    ("7️⃣ 7 ключей - 40й км ЕКАД, 7,9 км", "stage_7"),
    ("8️⃣ 40й км ЕКАД - Калиновка, 11,7 км", "stage_8"),
    ("9️⃣ Калиновка - Шарташ, 8,6 км", "stage_9"),
    ("Весь круг 😎", "all_stages")
]

# Главное меню Кругосветки
krugosvetka_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="krugosvetka_register")],
        [InlineKeyboardButton(text="📖 Положение", callback_data="krugosvetka_info")],
        [InlineKeyboardButton(text="🗺 Маршрут", callback_data="krugosvetka_route")],
        [InlineKeyboardButton(text="🏃 Этапы и протяженность", callback_data="krugosvetka_stages_list")],
        [InlineKeyboardButton(text="📊 Таблица этапов", url=KRUGOSVETKA_TABLE_LINK)],
        [InlineKeyboardButton(text="🏞 Фото с Кругосветки 2022", url="https://disk.yandex.ru/d/-TQjIW2IM9hHFA")],
        [InlineKeyboardButton(text="🏞 Фото с Кругосветки 2023", url="https://disk.yandex.ru/d/xBH2591nPm6XeA")],
        [InlineKeyboardButton(text="💬 Задать вопрос", url="https://t.me/AntonKorolev29")]
    ]
)

# Клавиатура для отправки номера телефона
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура подтверждения оплаты
payment_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Я оплатил(а)")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# FSM состояния для регистрации
class KrugosvetkaRegStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_stages = State()
    waiting_for_pace = State()
    waiting_for_payment = State()


# ===== ГЛАВНОЕ МЕНЮ КРУГОСВЕТКИ =====
@router.message(F.text == "🗺 Кругосветка 2025", StateFilter(None))
async def krugosvetka_menu(message: types.Message):
    """Главное меню Кругосветки"""
    try:
        await message.answer_photo(
            photo=PHOTO_KRUGOSVETKA_COVER,
            caption=(
                "🌍 <b>Кругосветка Группенран 2025!</b>\n\n"
                "Это дружеская эстафета, где мы пробегаем по лесопаркам вокруг всего Екатеринбурга, "
                "замыкая «зелёное кольцо». Бегите один или несколько этапов в комфортном темпе, "
                "а между ними отдыхайте в нашем Патибасе 🚌."
            ),
            reply_markup=krugosvetka_menu_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        # Если фото не загружается, отправляем без фото
        print(f"Ошибка загрузки обложки Кругосветки: {e}")
        await message.answer(
            "Добро пожаловать на Кругосветку Группенран 2025! ✨\n\n"
            "Это дружеская эстафета, где мы пробегаем по лесопаркам вокруг всего Екатеринбурга, замыкая «зелёное кольцо». "
            "Бегите один или несколько этапов в комфортном темпе, а между ними отдыхайте в нашем Патибасе 🚌.",
            reply_markup=krugosvetka_menu_kb
        )


# ===== ИНФОРМАЦИОННЫЕ ОБРАБОТЧИКИ =====
@router.callback_query(F.data == "krugosvetka_info")
async def krugosvetka_info_handler(callback_query: types.CallbackQuery):
    """Положение о Кругосветке"""
    await callback_query.answer()
    
    info_text = (
        "👋 Положение о «Кругосветке»\n\n"
        "🥳 «Кругосветка» — это наша добрая традиция, приуроченная ко дню рождения Группенрана!\n\n"
        "🌳 Это дружеская эстафета, где мы пробегаем по лесопаркам вокруг всего Екатеринбурга, замыкая «зелёное кольцо».\n\n"
        "Формат мероприятия:\n"
        "🏃 Эстафета в 9 этапов: Протяжённость каждого этапа варьируется.\n"
        "📍 Старт и финиш: Наша База «Мыс Рундук» на Шарташе.\n"
        "🚌 Передвижение: Между этапами участники перемещаются на комфортабельном Патибасе, который служит передвижной базой.\n\n"
        "Участие:\n"
        "• Можно присоединиться к любому этапу.\n"
        "• Можно пробежать как один, так и несколько этапов, вплоть до полного круга.\n"
        "• Количество участников на этапах не ограничено.\n"
        "• Темп: Участники одного этапа бегут вместе, в одном, заранее согласованном темпе.\n\n"
        "Важные моменты:\n"
        "🚰 Настоятельно рекомендуем заранее запастись едой и питьём.\n"
        "• Присоединиться к автобусу или сойти с него можно только в точках смены этапов.\n"
        "⏱️ Местонахождение группы будет транслироваться в чате, но лучше приезжать с запасом по времени, так как возможны небольшие смещения.\n"
        "🎂 На финише всех ждёт большое чаепитие с тортами и вкусностями на нашей основной базе.\n\n"
        "Регистрация:\n"
        "✨ При регистрации вы выбираете желаемые этапы и свой комфортный темп, чтобы мы могли собрать группы."
    )
    
    await callback_query.message.answer(info_text)


@router.callback_query(F.data == "krugosvetka_route")
async def krugosvetka_route_handler(callback_query: types.CallbackQuery):
    """Показ маршрута Кругосветки"""
    await callback_query.answer()
    route_text = (
        "🗺 Маршрут «Кругосветки»\n\n"
        "Полный маршрут забега проходит по «зелёному кольцу» вокруг Екатеринбурга.\n\n"
        "Трек доступен по ссылке ниже:"
    )
    
    route_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗺️ Карта маршрута", 
            url=TRACK_LINK
        )]
    ])
    
    await callback_query.message.answer(route_text, reply_markup=route_keyboard)


@router.callback_query(F.data == "krugosvetka_stages_list")
async def krugosvetka_stages_list_handler(callback_query: types.CallbackQuery):
    """Список всех этапов Кругосветки"""
    await callback_query.answer()
    
    stages_text = (
        "🏃‍♀️ Этапы и протяженность\n\n"
        "1️⃣ Шарташ - Сибирский тракт: 12.7 км\n\n"
        "2️⃣ Сибирский тракт - Уктус: 10.2 км\n\n"
        "3️⃣ Уктус - Амундсена: 7.3 км\n\n"
        "4️⃣ Амундсена - Мега: 8.2 км\n\n"
        "5️⃣ Мега - Палкинский Торфяник: 8.7 км\n\n"
        "6️⃣ Палкинский Торфяник - 7 ключей: 13.3 км\n\n"
        "7️⃣ 7 ключей - 40й км ЕКАД: 7.9 км\n\n"
        "8️⃣ 40й км ЕКАД - Калиновка: 11.7 км\n\n"
        "9️⃣ Калиновка - Шарташ: 8.6 км"
    )
    
    await callback_query.message.answer(stages_text)


# ===== РЕГИСТРАЦИЯ НА КРУГОСВЕТКУ =====
@router.callback_query(F.data == "krugosvetka_register")
async def krugosvetka_register_start(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации на Кругосветку"""
    await callback_query.answer()
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    user_data = all_data.get(user_id, {})

    # Проверка, зарегистрирован ли уже пользователь
    if user_data.get("krugosvetka", {}).get('is_registered'):
        # Получаем информацию о регистрации
        krugosvetka_data = user_data.get("krugosvetka", {})
        stages_ids = krugosvetka_data.get("stages_ids", [])
        pace = krugosvetka_data.get("pace", "Не указан")
        
        # Формируем текст о выбранных этапах
        if "all_stages" in stages_ids:
            stages_text = "Весь круг"
        elif stages_ids:
            stage_numbers = []
            for stage_id in stages_ids:
                if stage_id.startswith("stage_"):
                    stage_num = stage_id.replace("stage_", "")
                    stage_numbers.append(stage_num)
            stages_text = f"Этапы: {', '.join(sorted(stage_numbers))}"
        else:
            stages_text = "Этапы не выбраны"
        
        # Сообщение с информацией о регистрации (в нужном порядке)
        message_text = (
            f"✅ Ты уже зарегистрирован на Кругосветку 2025!\n\n"
            f"📋 {stages_text}\n"
            f"⏱ Темп: {pace}\n\n"
            f"Если хочешь изменить этапы или темп, используй кнопки ниже или открой раздел «Мой профиль».\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Оплата участия:\n"
            f"• Стартовый взнос — 1500 ₽\n"
            f"{KRUGOSVETKA_PAYMENT_LINK}\n\n"
            f"• С поддержкой сообщества — 2000 ₽\n"
            f"{KRUGOSVETKA_SUPPORT_PAYMENT_LINK}\n"
            f"{PHONE_PAYMENT_INFO}"
        )
        
        # Кнопки для быстрого изменения
        quick_change_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Изменить этапы", callback_data="change_krugosvetka_stages")],
            [InlineKeyboardButton(text="✏️ Изменить темп", callback_data="change_krugosvetka_pace")]
        ])
        
        await callback_query.message.answer(message_text, reply_markup=quick_change_keyboard)
        return

    # Если не зарегистрирован - начинаем регистрацию
    await callback_query.message.answer(
        "Отлично! Давай начнём регистрацию.\n\n"
        "Введи свои Фамилию и Имя:"
    )
    await state.set_state(KrugosvetkaRegStates.waiting_for_name)

# ===== ИЗМЕНЕНИЕ ЭТАПОВ =====
@router.callback_query(F.data == "change_krugosvetka_stages")
async def change_krugosvetka_stages_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Изменение выбранных этапов Кругосветки"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    
    # Получаем текущие выбранные этапы
    krugosvetka_data = all_data.get(user_id, {}).get("krugosvetka", {})
    current_stages = krugosvetka_data.get("stages_ids", [])
    
    # Сохраняем текущие этапы в state
    await state.update_data(selected_stages=current_stages)
    
    # Генерируем клавиатуру с текущим выбором
    keyboard = generate_stages_keyboard(current_stages)
    
    await callback_query.message.answer(
        "🔄 Изменение этапов Кругосветки\n\n"
        "Нажимай на кнопки, чтобы добавить или убрать этапы из списка.",
        reply_markup=keyboard
    )
    
    await state.set_state(KrugosvetkaRegStates.waiting_for_stages)


# ===== ИЗМЕНЕНИЕ ТЕМПА =====
@router.callback_query(F.data == "change_krugosvetka_pace")
async def change_krugosvetka_pace_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Изменение темпа для Кругосветки"""
    await callback_query.answer()
    
    await callback_query.message.answer(
        "⏱ Укажи свой комфортный темп бега (например, 5:30 или 6:00):"
    )
    
    await state.set_state(KrugosvetkaRegStates.waiting_for_pace)


@router.message(KrugosvetkaRegStates.waiting_for_name)
async def krugosvetka_name(message: types.Message, state: FSMContext):
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
    await state.set_state(KrugosvetkaRegStates.waiting_for_phone)

@router.message(KrugosvetkaRegStates.waiting_for_phone, F.text)
async def krugosvetka_phone_text(message: types.Message, state: FSMContext):
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
    
    # ✅ ПЕРЕХОД К ВЫБОРУ ЭТАПОВ
    data = await state.get_data()
    selected_stages = data.get("selected_stages", [])
    keyboard = generate_stages_keyboard(selected_stages)
    
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Отлично! Теперь выбери этапы, на которые хочешь зарегистрироваться:",
        reply_markup=keyboard
    )
    await state.set_state(KrugosvetkaRegStates.waiting_for_stages)

@router.message(KrugosvetkaRegStates.waiting_for_phone, F.contact)
async def krugosvetka_phone(message: types.Message, state: FSMContext):
    """Обработка получения номера телефона через кнопку"""
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
    
    # Переход к выбору этапов
    data = await state.get_data()
    selected_stages = data.get("selected_stages", [])
    keyboard = generate_stages_keyboard(selected_stages)
    
    await message.answer(
        f"✅ Номер телефона сохранён: {formatted_phone}\n\n"
        "Отлично! Теперь выбери этапы:",
        reply_markup=keyboard
    )
    await state.set_state(KrugosvetkaRegStates.waiting_for_stages)


def generate_stages_keyboard(selected_stages: list):
    """Генерирует клавиатуру для выбора этапов"""
    keyboard = []
    for text, callback_data in krugosvetka_stages:
        button_text = f"✅ {text}" if callback_data in selected_stages else text
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="🏁 Подтвердить выбор", callback_data="finish_selection")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(KrugosvetkaRegStates.waiting_for_stages)
async def krugosvetka_stage_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора этапов"""
    user_data = await state.get_data()
    selected_stages_ids = user_data.get("selected_stages", [])
    data = callback_query.data

    # Обработка выбора "Весь круг"
    if data == "all_stages":
        if "all_stages" in selected_stages_ids:
            selected_stages_ids = []
        else:
            selected_stages_ids = [stage[1] for stage in krugosvetka_stages if stage[1] != "all_stages"]
            selected_stages_ids.append("all_stages")
    
    # Подтверждение выбора
    elif data == "finish_selection":
        if not selected_stages_ids:
            await callback_query.answer("Пожалуйста, выбери хотя бы один этап.", show_alert=True)
            return

        stages_for_text = [stage for stage in krugosvetka_stages if stage[1] in selected_stages_ids and stage[1] != "all_stages"]
        selected_stages_names = [stage[0] for stage in stages_for_text]

        if "all_stages" in selected_stages_ids:
            selected_stages_names = ["Весь круг 😎"]

        await state.update_data(selected_stages_text=", ".join(selected_stages_names))
        await state.update_data(selected_stages=selected_stages_ids)
        
        # Проверяем, это новая регистрация или изменение этапов
        user_id = str(callback_query.from_user.id)
        all_data = load_data()
        is_registered = all_data.get(user_id, {}).get("krugosvetka", {}).get("is_registered", False)
        
        if is_registered:
            # Изменение существующих этапов
            all_data[user_id]["krugosvetka"]["stages"] = ", ".join(selected_stages_names)
            all_data[user_id]["krugosvetka"]["stages_ids"] = selected_stages_ids
            save_data(all_data)
            
            await callback_query.message.delete()
            await callback_query.message.answer(
                f"✅ Этапы успешно изменены!\n\n"
                f"Выбранные этапы: {', '.join(selected_stages_names)}"
            )
            await state.clear()
        else:
            # Продолжение новой регистрации
            await callback_query.message.delete()
            await callback_query.message.answer(
                "Спасибо! Теперь укажи свой комфортный темп бега (например, 5:30 или 6:00)."
            )
            await state.set_state(KrugosvetkaRegStates.waiting_for_pace)
        return
    
    # Обработка выбора отдельного этапа
    else:
        stage_id = data
        if stage_id in selected_stages_ids:
            selected_stages_ids.remove(stage_id)
            if "all_stages" in selected_stages_ids:
                selected_stages_ids.remove("all_stages")
        else:
            selected_stages_ids.append(stage_id)
            # Проверка: если выбраны все этапы, автоматически добавляем "Весь круг"
            all_regular_stages = {stage[1] for stage in krugosvetka_stages if stage[1] != "all_stages"}
            if all(s_id in selected_stages_ids for s_id in all_regular_stages) and "all_stages" not in selected_stages_ids:
                selected_stages_ids.append("all_stages")

        await state.update_data(selected_stages=selected_stages_ids)
        new_keyboard = generate_stages_keyboard(selected_stages_ids)

        try:
            await callback_query.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logging.warning(f"Ошибка при редактировании клавиатуры Кругосветки: {e}")
        
        await callback_query.answer()


@router.message(KrugosvetkaRegStates.waiting_for_pace)
async def krugosvetka_pace(message: types.Message, state: FSMContext):
    """Обработка ввода темпа"""
    await state.update_data(pace=message.text)
    reg_data = await state.get_data()
    
    user_id = str(message.from_user.id)
    all_data = load_data()
    is_registered = all_data.get(user_id, {}).get("krugosvetka", {}).get("is_registered", False)
    
    if is_registered:
        # Изменение темпа для существующей регистрации
        all_data[user_id]["krugosvetka"]["pace"] = message.text
        save_data(all_data)
        
        await message.answer(f"✅ Темп успешно изменён!\n\nНовый темп: {message.text}")
        await state.clear()
    else:
        # Новая регистрация - продолжаем процесс
        stages_text = reg_data.get("selected_stages_text")
        
        await message.answer(
            f"Ты выбрал следующие этапы: {stages_text}.\n"
            f"Твой комфортный темп: {message.text}.\n\n"
            f"Отлично! Выбери вариант оплаты:\n\n"
            f"💰 Стартовый взнос — 1500 ₽\n"
            f"➡️ {KRUGOSVETKA_PAYMENT_LINK}\n\n"
            f"❤️ Взнос с поддержкой сообщества — 2000 ₽\n"
            f"➡️ {KRUGOSVETKA_SUPPORT_PAYMENT_LINK}\n\n"
            f"{PHONE_PAYMENT_INFO}\n\n"
            f"После оплаты обязательно нажми кнопку «Я оплатил(а)» ниже.",
            reply_markup=payment_kb
        )
        await state.set_state(KrugosvetkaRegStates.waiting_for_payment)


@router.message(KrugosvetkaRegStates.waiting_for_payment, F.text == "✅ Я оплатил(а)")
async def krugosvetka_payment(message: types.Message, state: FSMContext):
    """Подтверждение оплаты и завершение регистрации"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    all_data = load_data()
    user_info = all_data.get(user_id, {})

    # Сохраняем данные пользователя
    user_info['name'] = reg_data.get("name")
    user_info['phone'] = reg_data.get("phone")
    user_info['username'] = message.from_user.username
    user_info['krugosvetka'] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stages": reg_data.get("selected_stages_text"),
        "stages_ids": reg_data.get("selected_stages"),
        "pace": reg_data.get("pace"),
    }

    all_data[user_id] = user_info
    save_data(all_data)

    analytics.track_registration(message.from_user.id, "krugosvetka")

    await message.answer("🎉 Регистрация на Кругосветку прошла успешно!\n\nДо встречи на старте! 🏃‍♂️")

    # Уведомление администратору
    admin_text = (
        f"✅ Новая регистрация на Кругосветку!\n\n"
        f"👤 ФИО: {reg_data.get('name')}\n"
        f"📞 Телефон: {reg_data.get('phone')}\n"
        f"Telegram: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"🏃 Этапы: {reg_data.get('selected_stages_text')}\n"
        f"⏱ Темп: {reg_data.get('pace')}\n"
        f"🆔 ID: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления администратору: {e}")

    await state.clear()

# ===== ОБРАБОТЧИК REPLY-КНОПКИ "Я ОПЛАТИЛ(А)" =====
@router.message(F.text == "✅ Я оплатил(а)", KrugosvetkaRegStates.waiting_for_payment)
async def krugosvetka_payment_confirm_reply(message: types.Message, state: FSMContext):
    """Подтверждение оплаты через Reply-кнопку"""
    user_id = str(message.from_user.id)
    reg_data = await state.get_data()
    
    all_data = load_data()
    user_info = all_data.get(user_id, {})
    
    # Сохраняем данные
    user_info["name"] = reg_data.get("name")
    user_info["phone"] = reg_data.get("phone")
    user_info["username"] = message.from_user.username
    
    user_info["krugosvetka"] = {
        "is_registered": True,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stages_ids": reg_data.get("stages_ids", []),
        "pace": reg_data.get("pace", "Неизвестно")
    }
    
    all_data[user_id] = user_info
    save_data(all_data)
    
    # Уведомление пользователю
    is_admin = user_id == str(ADMIN_ID)
    await message.answer(
        "🎉 Регистрация на Кругосветку завершена!\n\n"
        "Увидимся на старте! 🌍",
        reply_markup=admin_kb if is_admin else main_kb
    )
    
    # Уведомление админу
    stages_text = "Весь круг" if "all_stages" in reg_data.get("stages_ids", []) else ", ".join(reg_data.get("stages_ids", []))
    admin_text = (
        f"🔔 Новая регистрация на Кругосветку!\n\n"
        f"👤 {reg_data.get('name')}\n"
        f"📞 {reg_data.get('phone')}\n"
        f"Telegram: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"🏁 Этапы: {stages_text}\n"
        f"⏱ Темп: {reg_data.get('pace')}\n"
        f"ID: {user_id}"
    )
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")
    
    await state.clear()

# ===== УМНАЯ НАВИГАЦИЯ: КНОПКА "НАЗАД" =====
@router.message(F.text == "⬅️ Назад", StateFilter(
    KrugosvetkaRegStates.waiting_for_name,
    KrugosvetkaRegStates.waiting_for_phone,
    KrugosvetkaRegStates.waiting_for_stages,
    KrugosvetkaRegStates.waiting_for_pace,
    KrugosvetkaRegStates.waiting_for_payment
))
async def back_button_krugosvetka(message: types.Message, state: FSMContext):
    """Умная навигация назад в регистрации Кругосветки"""
    current_state = await state.get_state()
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    # Если на этапе оплаты - возвращаемся к вводу темпа
    if current_state == "KrugosvetkaRegStates:waiting_for_payment":
        await message.answer(
            "Возвращаемся к выбору темпа.\n\n"
            "Укажи комфортный для тебя темп бега (мин/км): 5:30, 6:00 и т.д.",
            reply_markup=back_kb
        )
        await state.set_state(KrugosvetkaRegStates.waiting_for_pace)
        return
    
    # Если на этапе темпа - возвращаемся к выбору этапов
    elif current_state == "KrugosvetkaRegStates:waiting_for_pace":
        data = await state.get_data()
        selected_stages = data.get("selected_stages", [])
        keyboard = generate_stages_keyboard(selected_stages)
        
        await message.answer(
            "Возвращаемся к выбору этапов.\n\n"
            "Выбери этапы, на которые хочешь зарегистрироваться:",
            reply_markup=keyboard
        )
        await state.set_state(KrugosvetkaRegStates.waiting_for_stages)
        return
    
    # Если на этапе выбора этапов - возвращаемся к телефону
    elif current_state == "KrugosvetkaRegStates:waiting_for_stages":
        await message.answer(
            "Возвращаемся к вводу номера телефона.\n\n"
            "Отправь свой контакт, нажав кнопку ниже 👇",
            reply_markup=phone_kb
        )
        await state.set_state(KrugosvetkaRegStates.waiting_for_phone)
        return
    
    # Если на этапе телефона - возвращаемся к имени
    elif current_state == "KrugosvetkaRegStates:waiting_for_phone":
        await message.answer(
            "Возвращаемся к вводу имени.\n\n"
            "Напиши своё имя:",
            reply_markup=back_kb
        )
        await state.set_state(KrugosvetkaRegStates.waiting_for_name)
        return
    
    # Если на этапе имени или остальных - полная отмена
    await state.clear()
    await message.answer(
        "❌ Регистрация на Кругосветку отменена.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )

