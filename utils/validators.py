import re
from typing import Tuple

def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Валидация и форматирование номера телефона
    
    Возвращает:
        (True, отформатированный_номер) если валидно
        (False, сообщение_об_ошибке) если невалидно
    """
    # Убираем все символы кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Паттерны для разных форматов
    patterns = [
        (r'^\+?7(\d{10})$', r'+7 (\1[:3]) \1[3:6]-\1[6:8]-\1[8:]'),  # +79991234567
        (r'^8(\d{10})$', r'+7 (\1[:3]) \1[3:6]-\1[6:8]-\1[8:]'),     # 89991234567
        (r'^\+?7(\d{3})(\d{3})(\d{2})(\d{2})$', r'+7 (\1) \2-\3-\4'), # Уже разделённый
    ]
    
    for pattern, format_template in patterns:
        match = re.match(pattern, cleaned)
        if match:
            # Форматируем в вид: +7 (999) 123-45-67
            digits = ''.join(re.findall(r'\d', cleaned))
            if len(digits) == 11 and digits[0] in ['7', '8']:
                formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
                return True, formatted
    
    return False, (
        "❌ Неверный формат номера телефона.\n\n"
        "Правильные форматы:\n"
        "• +7 (999) 123-45-67\n"
        "• 8 999 123 45 67\n"
        "• 79991234567"
    )


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Валидация имени пользователя
    
    Возвращает:
        (True, очищенное_имя) если валидно
        (False, сообщение_об_ошибке) если невалидно
    """
    name = name.strip()
    
    if len(name) < 2:
        return False, "❌ Имя слишком короткое (минимум 2 символа)"
    
    if len(name) > 100:
        return False, "❌ Имя слишком длинное (максимум 100 символов)"
    
    # Проверка на допустимые символы (кириллица, латиница, пробелы, дефисы)
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', name):
        return False, (
            "❌ Имя должно содержать только буквы, пробелы и дефисы.\n"
            "Без цифр и спецсимволов."
        )
    
    # Проверка на минимум 2 слова (Имя Фамилия)
    words = name.split()
    if len(words) < 2:
        return False, "❌ Укажи Имя и Фамилию (минимум 2 слова)"
    
    return True, name.title()  # Возвращаем с заглавными буквами
