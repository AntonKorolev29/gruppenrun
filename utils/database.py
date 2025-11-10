import sqlite3
import json
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file: str = "bot_data.db"):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        """Создание таблиц БД при первом запуске"""
        with self.get_connection() as conn:
            # Таблица пользователей
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                username TEXT,
                bot_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Таблица регистраций Группенран (с location)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS gruppenrun_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                location TEXT DEFAULT 'shartas',
                type TEXT NOT NULL,
                valid_until DATE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)

            # Таблица регистраций Иремель
            conn.execute("""
            CREATE TABLE IF NOT EXISTS iremel_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                is_registered BOOLEAN DEFAULT 0,
                waiting_list BOOLEAN DEFAULT 0,
                payment_type TEXT,
                diet_restrictions TEXT,
                preferences TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)

            # Таблица регистраций Кругосветка
            conn.execute("""
            CREATE TABLE IF NOT EXISTS krugosvetka_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                stages_ids TEXT,
                pace TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)

            # Таблица заказов завтраков
            conn.execute("""
            CREATE TABLE IF NOT EXISTS breakfast_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                order_date DATE NOT NULL,
                items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, order_date)
            )
            """)

            # Таблица для отслеживания событий
            conn.execute("""
            CREATE TABLE IF NOT EXISTS event_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_name TEXT NOT NULL,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)

            # Индексы
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gruppenrun_user ON gruppenrun_registrations(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gruppenrun_location ON gruppenrun_registrations(location)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_iremel_user ON iremel_registrations(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_breakfast_date ON breakfast_orders(order_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON event_tracking(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON event_tracking(event_name)")

            logger.info("✅ База данных инициализирована")

    @contextmanager
    def get_connection(self):
        """Context manager для работы с БД"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка БД: {e}")
            raise
        finally:
            conn.close()

    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_user(self, user_id: str, name: str = None, phone: str = None,
                  username: str = None, bot_version: str = None):
        with self.get_connection() as conn:
            existing = self.get_user(user_id)
            if existing:
                updates = []
                params = []
                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                if phone is not None:
                    updates.append("phone = ?")
                    params.append(phone)
                if username is not None:
                    updates.append("username = ?")
                    params.append(username)
                if bot_version is not None:
                    updates.append("bot_version = ?")
                    params.append(bot_version)
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                conn.execute(query, params)
            else:
                conn.execute(
                    "INSERT INTO users (user_id, name, phone, username, bot_version) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, phone, username, bot_version)
                )
            logger.info(f"💾 Пользователь {user_id} сохранён")

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== ГРУППЕНРАН ====================
    def save_gruppenrun_registration(self, user_id: str, reg_type: str,
                                     valid_until: str = None, location: str = 'shartas'):
        """Сохранить регистрацию на Группенран"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO gruppenrun_registrations (user_id, location, type, valid_until) VALUES (?, ?, ?, ?)",
                (user_id, location, reg_type, valid_until)
            )

    def check_gruppenrun_registration(self, user_id: str, location: str = 'shartas') -> Dict[str, Any]:
        """Проверить регистрацию на Группенран"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM gruppenrun_registrations WHERE user_id = ? AND location = ? ORDER BY registered_at DESC LIMIT 1",
                (user_id, location)
            )
            row = cursor.fetchone()
            if not row:
                return {"is_active": False}
            reg = dict(row)
            if reg['type'] == 'monthly' and reg['valid_until']:
                valid_until = datetime.strptime(reg['valid_until'], '%Y-%m-%d').date()
                if valid_until < datetime.now().date():
                    return {"is_active": False}
            return {"is_active": True, "type": reg['type'], "valid_until": reg['valid_until']}

    # ==================== ИРЕМЕЛЬ ====================
    def save_iremel_registration(self, user_id: str, is_registered: bool = False,
                                 waiting_list: bool = False, payment_type: str = None,
                                 diet_restrictions: str = None, preferences: str = None):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM iremel_registrations WHERE user_id = ?", (user_id,))
            conn.execute(
                "INSERT INTO iremel_registrations (user_id, is_registered, waiting_list, payment_type, diet_restrictions, preferences) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, is_registered, waiting_list, payment_type, diet_restrictions, preferences)
            )
            logger.info(f"✅ Иремель: {user_id} зарегистрирован")

    def get_iremel_registration(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM iremel_registrations WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def count_iremel_registrations(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM iremel_registrations WHERE is_registered = 1")
            return cursor.fetchone()[0]

    # ==================== АНАЛИТИКА ====================
    def track_event(self, user_id: str, event_name: str, event_data: dict = None):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO event_tracking (user_id, event_name, event_data) VALUES (?, ?, ?)",
                (str(user_id), event_name, json.dumps(event_data) if event_data else None)
            )

# Глобальный экземпляр БД
db = Database()
