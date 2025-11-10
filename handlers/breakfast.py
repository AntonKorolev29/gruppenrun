from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.reply import main_kb, admin_kb, back_kb
from utils.helpers import (
    load_data,
    save_data,
    escape_markdown,
    can_user_order_breakfast,
    get_user_profile,
    check_gruppenrun_registration,
)
from states.registration import BreakfastOrder
from config import BREAKFAST_MENU, ADMIN_ID
import logging

router = Router()

def generate_breakfast_keyboard(selected_items):
    """
    Генерирует клавиатуру для заказа завтрака.
    Кнопки с полными названиями блюд по 2 в строке.
    """
    keyboard = []
    row = []
    
    for item_id, item_info in BREAKFAST_MENU.items():
        count = selected_items.get(item_id, 0)
        name = item_info['name']
        price = item_info['price']
        
        # Формируем текст кнопки с полным названием
        if count > 0:
            button_text = f"{name}\n({count} шт.) • {price}₽"
        else:
            button_text = f"{name}\n{price}₽"
        
        row.append(InlineKeyboardButton(text=button_text, callback_data=f"breakfast_{item_id}"))
        
        # По 2 кнопки в строке
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    # Добавляем неполную строку
    if row:
        keyboard.append(row)
    
    # Управляющие кнопки
    keyboard.append([InlineKeyboardButton(text="✅ Завершить заказ", callback_data="finish_breakfast_order")])
    keyboard.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_breakfast_order")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "order_breakfast")
async def start_breakfast_order(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало заказа завтрака"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    
    # Проверяем, может ли пользователь заказать завтрак
    breakfast_check = can_user_order_breakfast(user_id, all_data)
    
    if not breakfast_check.get("can_order", False):
        await callback_query.message.answer(
            "❌ Для заказа завтрака сначала зарегистрируйся на Группенран!"
        )
        return
    
    # Начинаем заказ
    await state.update_data(breakfast_items={})
    await state.set_state(BreakfastOrder.waiting_for_selection)
    
    await callback_query.message.edit_text(
        "🍳 Заказ завтрака\n\n"
        "Выбери блюда. Каждое нажатие +1 порция.",
        reply_markup=generate_breakfast_keyboard({})
    )


@router.callback_query(F.data == "modify_breakfast_order")
async def modify_breakfast_order(callback_query: types.CallbackQuery, state: FSMContext):
    """Изменение существующего заказа завтрака"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    
    # Получаем текущий заказ
    user_data = all_data.get(user_id, {})
    current_order = user_data.get("breakfast_order", {})
    current_items = current_order.get("items", {})
    
    await state.update_data(breakfast_items=current_items)
    await state.set_state(BreakfastOrder.waiting_for_selection)
    
    keyboard = generate_breakfast_keyboard(current_items)
    
    await callback_query.message.edit_text(
        "☕ Изменение заказа. Выбери блюда:", 
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cancel_breakfast_order_from_profile")
async def cancel_breakfast_order_from_profile(callback_query: types.CallbackQuery):
    """Отмена заказа завтрака из профиля"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    all_data = load_data()
    
    if user_id in all_data and "breakfast_order" in all_data[user_id]:
        del all_data[user_id]["breakfast_order"]
        save_data(all_data)
        
        await callback_query.message.edit_text(
            "❌ Заказ завтрака отменён.\nТы можешь оформить новый заказ в любое время."
        )
        
        try:
            profile = get_user_profile(user_id, all_data)
            user_name = profile.get("name", "Неизвестный") if profile else "Неизвестный"
            await callback_query.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❌ Отмена заказа завтрака\n\nПользователь: {user_name}\nID: {user_id}"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу: {e}")
    else:
        await callback_query.message.edit_text("Заказ не найден.")


@router.callback_query(F.data == "cancel_breakfast_order", BreakfastOrder.waiting_for_selection)
async def cancel_breakfast_order_during_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена заказа завтрака во время выбора блюд"""
    await callback_query.answer()
    await callback_query.message.edit_text("❌ Заказ завтрака отменён.")
    await state.clear()


@router.callback_query(F.data.startswith("breakfast_"), BreakfastOrder.waiting_for_selection)
async def add_breakfast_item(callback_query: types.CallbackQuery, state: FSMContext):
    """Добавление блюда в заказ"""
    await callback_query.answer("✅ Добавлено")
    
    item_id = callback_query.data.replace("breakfast_", "")
    
    # Получаем текущий заказ
    data = await state.get_data()
    breakfast_items = data.get("breakfast_items", {})
    
    # Увеличиваем количество
    breakfast_items[item_id] = breakfast_items.get(item_id, 0) + 1
    await state.update_data(breakfast_items=breakfast_items)
    
    # Обновляем клавиатуру
    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=generate_breakfast_keyboard(breakfast_items)
        )
    except Exception as e:
        logging.error(f"Ошибка обновления клавиатуры: {e}")


@router.callback_query(F.data == "finish_breakfast_order", BreakfastOrder.waiting_for_selection)
async def finish_breakfast_order(callback_query: types.CallbackQuery, state: FSMContext):
    """Завершение и подтверждение заказа"""
    await callback_query.answer()
    
    user_id = str(callback_query.from_user.id)
    data = await state.get_data()
    breakfast_items = data.get("breakfast_items", {})
    
    if not breakfast_items:
        await callback_query.message.edit_text("❌ Ничего не выбрано. Заказ отменён.")
        await state.clear()
        return
    
    all_data = load_data()
    
    # Проверяем регистрацию на Группенран
    if not check_gruppenrun_registration(user_id, all_data)["is_active"]:
        await callback_query.message.answer(
            "❗ Для заказа завтрака нужно быть зарегистрированным на Группенран."
        )
        await state.clear()
        return
    
    # Формируем итоговый заказ
    order_text = "🍳 Твой заказ:\n\n"
    total_price = 0
    
    for item_id, count in breakfast_items.items():
        item_info = BREAKFAST_MENU.get(item_id)
        if item_info:
            name = item_info['name']
            price = item_info['price']
            item_total = price * count
            total_price += item_total
            order_text += f"• {name} x{count} — {item_total}₽\n"
    
    order_text += f"\n💰 Итого: {total_price}₽"
    
    # Сохраняем заказ в данных пользователя
    if user_id not in all_data:
        all_data[user_id] = {}
    
    all_data[user_id]["breakfast_order"] = {
        "items": breakfast_items,
        "total_price": total_price,
        "order_date": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_data(all_data)
    
    await callback_query.message.edit_text(
        f"{order_text}\n\n✅ Заказ принят! Увидимся на пробежке!"
    )
    
    # Уведомление администратору
    user_profile = get_user_profile(user_id, all_data)
    user_name = user_profile.get('name', 'Неизвестно') if user_profile else 'Неизвестно'
    user_phone = user_profile.get('phone', 'Неизвестно') if user_profile else 'Неизвестно'
    username = callback_query.from_user.username or 'N/A'
    
    admin_message = (
        f"🍳 Новый заказ завтрака!\n\n"
        f"👤 {user_name}\n"
        f"📞 {user_phone}\n"
        f"Telegram: @{username}\n\n"
        f"{order_text}\n\n"
        f"ID: {user_id}"
    )
    
    try:
        await callback_query.bot.send_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления администратору: {e}")
    
    await state.clear()

# ===== КНОПКА "НАЗАД" ДЛЯ ЗАКАЗА ЗАВТРАКОВ =====
@router.message(F.text == "⬅️ Назад", StateFilter(BreakfastOrder.waiting_for_selection))
async def back_button_breakfast(message: types.Message, state: FSMContext):
    """Отмена заказа завтрака через кнопку Назад"""
    user_id = str(message.from_user.id)
    is_admin = user_id == str(ADMIN_ID)
    
    await state.clear()
    await message.answer(
        "❌ Заказ завтрака отменён.\n\n"
        "Возвращаю тебя в главное меню.",
        reply_markup=admin_kb if is_admin else main_kb
    )
