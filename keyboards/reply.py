from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главная клавиатура для обычных пользователей
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚫ Группенран Трейл"), KeyboardButton(text="⚪ Группенран Шарташ")],
        [KeyboardButton(text="🏔 Иремель Кэмп 2025")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="💬 Обратная связь")],
    ],
    resize_keyboard=True
)

# Админская клавиатура (расширенная версия главной)
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚫ Группенран Трейл"), KeyboardButton(text="⚪ Группенран Шарташ")],
        [KeyboardButton(text="🏔 Иремель Кэмп 2025")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="💬 Обратная связь")],
        [KeyboardButton(text="📊 Админ-панель")]
    ],
    resize_keyboard=True
)

# Остальные клавиатуры без изменений...
admin_panel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚪ Группенран Шарташ"), KeyboardButton(text="🍳 Завтраки")],
        [KeyboardButton(text="⚫ Группенран Трейл"), KeyboardButton(text="🏔 Иремель")],
        [KeyboardButton(text="📊 Все регистрации")],
        [KeyboardButton(text="📊 Аналитика")],
        [KeyboardButton(text="⬅️ Назад в главное меню")]
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Назад")]],
    resize_keyboard=True,
    one_time_keyboard=False  # ← важно!
)

phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

payment_confirmation_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Оплатил")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

edit_profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Изменить имя")],
        [KeyboardButton(text="📱 Изменить телефон")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

payment_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Я оплатил(а)")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)
