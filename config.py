import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# --- Основные настройки ---
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Проверяем, что переменные загрузились
if not API_TOKEN or not ADMIN_ID:
    raise ValueError("Ошибка: переменные BOT_TOKEN и ADMIN_ID должны быть в файле .env")

ADMIN_ID = int(ADMIN_ID)

# --- Ссылки на оплату ---
PAYMENT_LINK = "https://yoomoney.ru/fundraise/1C59KCB3HTO.250815"
PAYMENT_MONTH_LINK = "https://yoomoney.ru/fundraise/1C5SH5U4OP8.250816"
KRUGOSVETKA_PAYMENT_LINK = "https://yoomoney.ru/fundraise/1CED7LONA1R.250829"
KRUGOSVETKA_SUPPORT_PAYMENT_LINK = "https://yoomoney.ru/fundraise/1CEIPLVDJ73.250829"
KRUGOSVETKA_PHONE_PAYMENT = "+79226080101 (OzonБанк, Антон Александрович К.)"
IREMEL_MAX_PARTICIPANTS = 27  # Максимум участников
IREMEL_PAYMENT_50 = "https://yoomoney.ru/fundraise/1DEVCCTJPC2.251017"  # Оплата 50%
IREMEL_PAYMENT_100 = "https://yoomoney.ru/fundraise/1DEVCQ391NA.251017"  # Оплата 100%
PAYMENT_LINK_UKTUS = "https://yoomoney.ru/fundraise/1DSL2EFR34L.251107"
PAYMENT_MONTH_LINK_UKTUS = "https://yoomoney.ru/fundraise/1DSL2QQ7II2.251107"

# --- Ссылки на внешние ресурсы ---
TRACK_LINK = "https://nakarte.me/#m=12/56.87619/60.56591&l=Co&nktl=ug9Q_i3vI6iatBi3XnjwDg"
KRUGOSVETKA_TABLE_LINK = "https://docs.google.com/spreadsheets/d/1zOGgv38Ydu08fgTFpzVm9SBc79yIBc0gA8zfFBVsrHI/edit?usp=sharing"

# --- Фотографии-обложки --- 
PHOTO_GRUPPENRUN_COVER = "AgACAgIAAxkBAAIQ_2jpIO_rb_rs-6CiiUkpnuTV9aCpAALi_TEbD7FIS5V_cYaS_xGZAQADAgADeQADNgQ"
PHOTO_KRUGOSVETKA_COVER = "AgACAgIAAxkBAAIQ_WjpHlMIm9MrHSlgQLybiWMiIunJAAJx-jEb9aowS5-pStcKQu5hAQADAgADeQADNgQ"
PHOTO_HOW_TO_GET_COVER = "AgACAgIAAxkBAAISKmjt7WAKncK8Q0HqzOyvcsgS26i2AAJ-9zEb4ntxS7dl2fhD89wTAQADAgADdwADNgQ"
PHOTO_IREMEL_COVER = "AgACAgIAAxkBAAISu2jyS9iVUNSGl_FzhsIb2uB94Od6AAKk_TEbQGWQS5RIr22cmB2bAQADAgADeQADNgQ"

# --- База данных ---
DB_FILE = "registrations_db.json"

# --- Текстовая информация ---
PHONE_PAYMENT_INFO = f"\n\nИли на номер телефона: `{KRUGOSVETKA_PHONE_PAYMENT}`"

# Меню завтраков - ПОЛНЫЕ названия с переносами строк
BREAKFAST_MENU = {
    "kasha_rice": {
        "name": "🍚 Каша, на основе жасминового риса,\nна кокосовом молоке, с вишневым вареньем",
        "price": 270
    },
    "kasha_hercules": {
        "name": "🥣 Каша геркулесовая, на коровьем молоке,\nс грушевым вареньем и сыром дор блю",
        "price": 280
    },
    "kasha_grechka": {
        "name": "🍵 Каша гречневая\nс яйцом пашот с соусом пармезан",
        "price": 240
    },
    "omlet_bacon": {
        "name": "🥓 Омлет с печеным\nперцем и беконом фри",
        "price": 350
    },
    "omlet_salmon": {
        "name": "🍳 Омлет с лососем\nи соусом пармезан",
        "price": 350
    },
    "oladki_kabachok": {
        "name": "🥞 Оладьи из кабачка,\nс лососем и соусом пармезан",
        "price": 380
    },
    "syrniki": {
        "name": "😋 Сырники\nс вишневым вареньем и сметаной",
        "price": 260
    }
}

# --- Этапы кругосветки ---
KRUGOSVETKA_STAGES = [
    ("1️⃣ Шарташ -> Сибирский тракт, 12.7 км", "stage_1"),
    ("2️⃣ Сибирский тракт -> Уктус, 10.2 км", "stage_2"),
    ("3️⃣ Уктус -> Амундсена, 7.3 км", "stage_3"),
    ("4️⃣ Амундсена -> Мега, 8.2 км", "stage_4"),
    ("5️⃣ Мега -> Палкинский Торфяник, 8.7 км", "stage_5"),
    ("6️⃣ Палкинский Торфяник -> 7 ключей, 13.3 км", "stage_6"),
    ("7️⃣ 7 ключей -> 40й км ЕКАД, 7.9 км", "stage_7"),
    ("8️⃣ 40й км ЕКАД -> Калиновка, 11.7 км", "stage_8"),
    ("9️⃣ Калиновка -> Шарташ, 8.6 км", "stage_9"),
    ("Весь круг 😎", "all_stages")
]

# --- Константы для расчета номера Группенрана ---
from datetime import date

FIRST_GRUPPENRUN_DATE = date(2019, 10, 27)  # Дата первой пробежки (для истории)
REFERENCE_GR_DATE = date(2025, 9, 28)       # Дата 277-го Группенрана
REFERENCE_GR_NUMBER = 277                    # Номер Группенрана на REFERENCE_GR_DATE

# --- Константы для Группенран Трейл (Уктус) ---
from datetime import date, timedelta

FIRST_UKTUS_DATE = date(2025, 11, 8)   # Дата первой тренировки Трейл
REFERENCE_UKTUS_DATE = date(2025, 11, 8)  # Дата 1-го Трейл
REFERENCE_UKTUS_NUMBER = 1              # Номер Трейл на REFERENCE_UKTUS_DATE

# --- Реквизиты для оплаты ---
PAYMENT_DETAILS = """
💳 Способы оплаты:

🔗 Через ЮMoney:
• Разовое (Шарташ): https://yoomoney.ru/fundraise/1C59KCB3HTO.250815
• Месячный (Шарташ): https://yoomoney.ru/fundraise/1C5SH5U4OP8.250816
• Разовое (Трейл): https://yoomoney.ru/fundraise/1DSL2EFR34L.251107
• Месячный (Трейл): https://yoomoney.ru/fundraise/1DSL2QQ7II2.251107

🏦 Прямой перевод:
• +7 (922) 608-01-01
• OzonБанк
• Антон Александрович К.

📝 После оплаты вернитесь в бот и нажмите кнопку "Я опалтил(-а)" для успешного завершения регистрации
"""



# Версия бота:
BOT_VERSION = "1.1.0"  # Увеличивай версию после каждого значимого обновления

