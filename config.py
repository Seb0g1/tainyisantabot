"""
Конфигурация бота
"""

from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Дедлайн регистрации по умолчанию (дни)
    DEFAULT_DEADLINE_DAYS: int = 7
    
    # Минимальное количество участников для жеребьёвки
    MIN_PARTICIPANTS: int = 3
    
    # Максимальное количество попыток создания derangement
    MAX_DERANGEMENT_ATTEMPTS: int = 100
    
    # Путь к базе данных
    DB_PATH: str = "santa_bot.db"
    
    # Путь к лог-файлу
    LOG_FILE: str = "santa_bot.log"


