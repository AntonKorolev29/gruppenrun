from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """
    In-memory кэш для данных регистраций
    
    Решает проблему:
    - Каждый обработчик вызывает load_data() (чтение с диска)
    - При 100+ пользователей это замораживает бот
    
    Решение:
    - Кэшируем данные в памяти на 30-60 секунд
    - Автоматически инвалидируем после save_data()
    """
    
    def __init__(self, ttl_seconds: int = 60):
        """
        Args:
            ttl_seconds: Time To Live кэша в секундах (по умолчанию 60)
        """
        self._cache: Optional[Dict[str, Any]] = None
        self._last_update: Optional[datetime] = None
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hits = 0
        self.misses = 0
    
    def get_data(self, load_func) -> Dict[str, Any]:
        """
        Получить данные с кэшированием
        
        Args:
            load_func: Функция load_data() из helpers.py
        
        Returns:
            Кэшированные или свежие данные
        """
        now = datetime.now()
        
        # Если кэш устарел или пуст — загружаем свежие данные
        if self._cache is None or (now - self._last_update) > self.ttl:
            logger.debug("📥 Cache MISS — загружаю данные с диска")
            self._cache = load_func()
            self._last_update = now
            self.misses += 1
        else:
            # Используем кэшированные данные
            logger.debug("✅ Cache HIT — использую кэшированные данные")
            self.hits += 1
        
        return self._cache
    
    def invalidate(self):
        """Инвалидировать кэш (вызвать после save_data())"""
        self._cache = None
        self._last_update = None
        logger.debug("🔄 Cache invalidated")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.1f}%"
        }


# Глобальный экземпляр кэша
data_cache = DataCache(ttl_seconds=60)
