# Файл: keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BREAKFAST_MENU, KRUGOSVETKA_STAGES, KRUGOSVETKA_TABLE_LINK

# --- Inline-клавиатуры (кнопки под сообщениями) ---

# Клавиатура для выбора типа оплаты Группенрана
gruppenrun_payment_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Разовая оплата - 200₽", callback_data="payment_onetime")],
        [InlineKeyboardButton(text="Месячный абонемент - 600₽", callback_data="payment_monthly")]
    ]
)

# Главная клавиатура Кругосветки
krugosvetka_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏃 Зарегистрироваться", callback_data="krugosvetka_register")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="krugosvetka_info")],
        [InlineKeyboardButton(text="🗺️ Маршрут", callback_data="krugosvetka_route")],
        [InlineKeyboardButton(text="📋 Этапы", callback_data="krugosvetka_stages_list")],
        [InlineKeyboardButton(text="📊 Таблица результатов", url=KRUGOSVETKA_TABLE_LINK)],
        [InlineKeyboardButton(text="📹 Видео 2022", url="https://disk.yandex.ru/d/-TQjIW2IM9hHFA")],
        [InlineKeyboardButton(text="📹 Видео 2023", url="https://disk.yandex.ru/d/xBH2591nPm6XeA")],
        [InlineKeyboardButton(text="✍️ Отзывы", url="https://t.me/AntonKorolev29")]
    ]
)

# Клавиатура для профиля пользователя
def generate_profile_keyboard(has_profile=False, is_gruppenrun_active=False, is_krugosvetka_active=False):
    """Генерирует клавиатуру профиля в зависимости от состояния"""
    keyboard = []
    
    if has_profile:
        # Если у пользователя есть сохранённый профиль
        keyboard.append([InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile")])
        
        # Быстрая регистрация, если есть активные мероприятия
        if not is_gruppenrun_active:
            keyboard.append([InlineKeyboardButton(text="🏃 Быстрая регистрация на Группенран", callback_data="quick_gruppenrun")])
        if not is_krugosvetka_active:
            keyboard.append([InlineKeyboardButton(text="🌍 Быстрая регистрация на Кругосветку", callback_data="quick_krugosvetka")])
    else:
        # Если профиля нет
        keyboard.append([InlineKeyboardButton(text="➕ Создать профиль", callback_data="create_profile")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Клавиатура для подтверждения использования сохранённых данных
def generate_quick_registration_keyboard(event_type):
    """Генерирует клавиатуру для подтверждения быстрой регистрации"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, использовать эти данные", callback_data=f"confirm_quick_{event_type}")],
            [InlineKeyboardButton(text="✏️ Изменить данные", callback_data=f"edit_and_register_{event_type}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")]
        ]
    )

# Функция для генерации клавиатуры завтраков
def generate_breakfast_keyboard(selected_items=None):
    """Генерирует клавиатуру для выбора завтраков"""
    if selected_items is None:
        selected_items = {}
    
    keyboard_buttons = []
    
    # Кнопки для каждого блюда
    for item_id, item_data in BREAKFAST_MENU.items():
        count = selected_items.get(item_id, 0)
        emoji = item_data.get("emoji", "🍽️")
        item_name = item_data["name"]
        item_price = item_data["price"]
        
        if count > 0:
            button_text = f"{emoji} {item_name} ({count}шт.) - {item_price}₽"
        else:
            button_text = f"{emoji} {item_name} - {item_price}₽"
        
        keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"bf_{item_id}")])
    
    # Кнопки управления
    control_buttons = []
    if selected_items:  # Если что-то выбрано
        control_buttons.append([
            InlineKeyboardButton(text="➕ Добавить ещё", callback_data="add_more_bf"),
            InlineKeyboardButton(text="➖ Убрать последнее", callback_data="remove_last_bf")
        ])
    
    control_buttons.append([InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_breakfast_order")])
    control_buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_breakfast_order")])
    
    # Объединяем все кнопки
    final_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons + control_buttons)
    return final_keyboard

# Функция для генерации клавиатуры этапов Кругосветки
def generate_stages_keyboard(selected_stages=None):
    """Генерирует клавиатуру для выбора этапов Кругосветки"""
    if selected_stages is None:
        selected_stages = []
    
    keyboard = []
    
    # Кнопки для каждого этапа
    for text, callback_data in KRUGOSVETKA_STAGES:
        if callback_data in selected_stages:
            button_text = f"✅ {text}"
        else:
            button_text = text
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Кнопка завершения выбора
    keyboard.append([InlineKeyboardButton(text="✅ Завершить выбор", callback_data="finish_selection")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)