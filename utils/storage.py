import json
import os
from typing import Optional, Dict, Any
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType


class JSONStorage(BaseStorage):
    """Простое файловое хранилище для FSM состояний"""
    
    def __init__(self, file_path: str = "fsm_storage.json"):
        self.file_path = file_path
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки FSM storage: {e}")
                self._data = {}
        else:
            print("ℹ️ Файл FSM storage не найден, создаём новый")
    
    def _save(self):
        """Сохранение данных в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения FSM storage: {e}")
    
    def _make_key(self, key: StorageKey) -> str:
        """Создание уникального ключа пользователя"""
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"
    
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """Установка состояния пользователя"""
        storage_key = self._make_key(key)
        if storage_key not in self._data:
            self._data[storage_key] = {}
        
        # ИСПРАВЛЕНИЕ: сохраняем строковое представление состояния
        if state is None:
            self._data[storage_key]['state'] = None
        else:
            # Преобразуем State в строку (формат: "ModuleName:StateName")
            self._data[storage_key]['state'] = state.state if hasattr(state, 'state') else str(state)
        
        self._save()
    
    async def get_state(self, key: StorageKey) -> Optional[str]:
        """Получение состояния пользователя"""
        storage_key = self._make_key(key)
        return self._data.get(storage_key, {}).get('state')
    
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Сохранение данных пользователя"""
        storage_key = self._make_key(key)
        if storage_key not in self._data:
            self._data[storage_key] = {}
        self._data[storage_key]['data'] = data
        self._save()
    
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """Получение данных пользователя"""
        storage_key = self._make_key(key)
        return self._data.get(storage_key, {}).get('data', {})
    
    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Обновление данных пользователя"""
        storage_key = self._make_key(key)
        if storage_key not in self._data:
            self._data[storage_key] = {}
        if 'data' not in self._data[storage_key]:
            self._data[storage_key]['data'] = {}
        self._data[storage_key]['data'].update(data)
        self._save()
    
    async def close(self) -> None:
        """Закрытие хранилища и сохранение данных"""
        self._save()
        print("✅ FSM storage сохранён и закрыт")
