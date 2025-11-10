# Файл: states/registration.py
from aiogram.fsm.state import State, StatesGroup

# --- Состояния FSM (Finite State Machine) для диалогов ---

class ProfileFillState(StatesGroup):
    waiting_for_fullname = State()
    waiting_for_phone = State()

class GruppenrunReg(StatesGroup):
    """Состояния для регистрации на Группенран"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_payment_type = State()
    waiting_for_payment = State()

class KrugosvetkaReg(StatesGroup):
    """Состояния для регистрации на Кругосветку"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_stages = State()
    waiting_for_pace = State()
    waiting_for_payment = State()

class FeedbackState(StatesGroup):
    """Состояние для отправки обратной связи"""
    waiting_for_message = State()

class BreakfastOrder(StatesGroup):
    """Состояния для заказа завтраков"""
    waiting_for_selection = State()
    waiting_for_confirmation = State()

# --- Состояния для работы с профилем пользователя ---

class EditProfile(StatesGroup):
    """Состояния для изменения данных профиля"""
    waiting_for_new_name = State()
    waiting_for_new_phone = State()

class QuickRegistration(StatesGroup):
    """Состояния для быстрой регистрации на основе существующего профиля"""
    confirm_gruppenrun = State()
    confirm_krugosvetka = State()
    selecting_stages = State()  # Только для Кругосветки
    waiting_for_pace = State()   # Только для Кругосветки