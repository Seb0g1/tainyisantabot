"""
База данных для Тайного Санты Бота
SQLite с async поддержкой через aiosqlite
"""

import aiosqlite
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "santa_bot.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def init(self):
        """Инициализация базы данных и создание таблиц"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        await self._create_tables()
        logger.info("✅ База данных инициализирована")
    
    async def _create_tables(self):
        """Создание таблиц"""
        # Таблица игр
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                budget INTEGER,
                join_code TEXT,
                started BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаём уникальный индекс для join_code (если его нет)
        try:
            await self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_games_join_code ON games(join_code)")
            await self.conn.commit()
        except Exception as e:
            logger.debug(f"Индекс join_code уже существует или ошибка: {e}")
        
        # Добавляем колонки если их нет (для миграции)
        # Проверяем существование колонок через PRAGMA table_info
        async with self.conn.execute("PRAGMA table_info(games)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        
        if "budget" not in columns:
            try:
                await self.conn.execute("ALTER TABLE games ADD COLUMN budget INTEGER")
                await self.conn.commit()
                logger.info("✅ Добавлена колонка budget")
            except Exception as e:
                logger.error(f"Ошибка добавления колонки budget: {e}")
        
        if "join_code" not in columns:
            try:
                await self.conn.execute("ALTER TABLE games ADD COLUMN join_code TEXT")
                await self.conn.commit()
                # Создаём уникальный индекс для join_code
                try:
                    await self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_games_join_code ON games(join_code)")
                    await self.conn.commit()
                except:
                    pass
                logger.info("✅ Добавлена колонка join_code")
            except Exception as e:
                logger.error(f"Ошибка добавления колонки join_code: {e}")
        
        # Таблица участников
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                victim_id INTEGER,
                wishlist TEXT,
                wishlist_photo TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                UNIQUE(game_id, user_id)
            )
        """)
        
        # Добавляем колонки wishlist если их нет (для миграции)
        try:
            await self.conn.execute("ALTER TABLE participants ADD COLUMN wishlist TEXT")
            await self.conn.execute("ALTER TABLE participants ADD COLUMN wishlist_photo TEXT")
            await self.conn.commit()
        except:
            pass  # Колонки уже существуют
        
        # Индексы для оптимизации
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_chat_id ON games(chat_id)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_participants_game_id ON participants(game_id)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_participants_user_id ON participants(user_id)
        """)
        
        await self.conn.commit()
    
    async def create_game(self, chat_id: int, creator_id: int, deadline: datetime, budget: Optional[int] = None, join_code: Optional[str] = None) -> Optional[int]:
        """Создать новую игру"""
        try:
            cursor = await self.conn.execute("""
                INSERT INTO games (chat_id, creator_id, deadline, budget, join_code, started)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (chat_id, creator_id, deadline.isoformat(), budget, join_code))
            
            await self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка создания игры: {e}")
            return None
    
    async def get_game_by_code(self, join_code: str) -> Optional[Dict]:
        """Получить игру по коду присоединения"""
        try:
            async with self.conn.execute("""
                SELECT * FROM games
                WHERE join_code = ? AND started = 0
                ORDER BY created_at DESC
                LIMIT 1
            """, (join_code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения игры по коду: {e}")
            return None
    
    async def set_budget(self, game_id: int, budget: int) -> bool:
        """Установить бюджет для игры"""
        try:
            await self.conn.execute("""
                UPDATE games SET budget = ? WHERE id = ?
            """, (budget, game_id))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка установки бюджета: {e}")
            return False
    
    async def set_wishlist(self, game_id: int, user_id: int, wishlist: str, photo_id: Optional[str] = None) -> bool:
        """Установить вишлист для участника"""
        try:
            await self.conn.execute("""
                UPDATE participants
                SET wishlist = ?, wishlist_photo = ?
                WHERE game_id = ? AND user_id = ?
            """, (wishlist, photo_id, game_id, user_id))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка установки вишлиста: {e}")
            return False
    
    async def has_wishlist(self, game_id: int, user_id: int) -> bool:
        """Проверить, есть ли вишлист у участника"""
        try:
            async with self.conn.execute("""
                SELECT wishlist FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, user_id)) as cursor:
                row = await cursor.fetchone()
                return row and row["wishlist"] is not None and row["wishlist"] != ""
        except Exception as e:
            logger.error(f"Ошибка проверки вишлиста: {e}")
            return False
    
    async def get_participants_without_wishlist(self, game_id: int) -> List[Dict]:
        """Получить участников без вишлиста"""
        try:
            async with self.conn.execute("""
                SELECT * FROM participants
                WHERE game_id = ? AND (wishlist IS NULL OR wishlist = '')
                ORDER BY joined_at
            """, (game_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения участников без вишлиста: {e}")
            return []
    
    async def get_active_game(self, chat_id: int) -> Optional[Dict]:
        """Получить активную (не запущенную) игру в чате"""
        try:
            async with self.conn.execute("""
                SELECT * FROM games
                WHERE chat_id = ? AND started = 0
                ORDER BY created_at DESC
                LIMIT 1
            """, (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения игры: {e}")
            return None
    
    async def get_game_by_id(self, game_id: int) -> Optional[Dict]:
        """Получить игру по ID"""
        try:
            async with self.conn.execute("""
                SELECT * FROM games
                WHERE id = ?
            """, (game_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения игры по ID: {e}")
            return None
    
    async def get_user_active_game(self, user_id: int) -> Optional[Dict]:
        """Получить активную игру, где участвует пользователь (включая запущенные)"""
        try:
            async with self.conn.execute("""
                SELECT g.* FROM games g
                INNER JOIN participants p ON g.id = p.game_id
                WHERE p.user_id = ?
                ORDER BY g.created_at DESC
                LIMIT 1
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения игры пользователя: {e}")
            return None
    
    async def get_user_created_games(self, creator_id: int) -> List[Dict]:
        """Получить все игры, созданные пользователем"""
        try:
            async with self.conn.execute("""
                SELECT * FROM games
                WHERE creator_id = ?
                ORDER BY created_at DESC
            """, (creator_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения игр создателя: {e}")
            return []
    
    async def get_user_participant_games(self, user_id: int) -> List[Dict]:
        """Получить все игры, где пользователь участвует"""
        try:
            async with self.conn.execute("""
                SELECT DISTINCT g.* FROM games g
                INNER JOIN participants p ON g.id = p.game_id
                WHERE p.user_id = ?
                ORDER BY g.created_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения игр участника: {e}")
            return []
    
    async def start_game(self, game_id: int) -> bool:
        """Запустить игру (пометить как started)"""
        try:
            await self.conn.execute("""
                UPDATE games SET started = 1 WHERE id = ?
            """, (game_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка запуска игры: {e}")
            return False
    
    async def delete_game(self, game_id: int) -> bool:
        """Удалить игру и всех участников"""
        try:
            # Сначала удаляем всех участников
            await self.conn.execute("""
                DELETE FROM participants WHERE game_id = ?
            """, (game_id,))
            # Затем удаляем игру
            await self.conn.execute("""
                DELETE FROM games WHERE id = ?
            """, (game_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления игры: {e}")
            return False
    
    async def add_participant(self, game_id: int, user_id: int, username: str) -> bool:
        """Добавить участника в игру"""
        try:
            await self.conn.execute("""
                INSERT OR IGNORE INTO participants (game_id, user_id, username)
                VALUES (?, ?, ?)
            """, (game_id, user_id, username))
            await self.conn.commit()
            
            # Проверяем, добавился ли
            async with self.conn.execute("""
                SELECT COUNT(*) as count FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, user_id)) as cursor:
                row = await cursor.fetchone()
                return row["count"] > 0
        except Exception as e:
            logger.error(f"Ошибка добавления участника: {e}")
            return False
    
    async def remove_participant(self, game_id: int, user_id: int) -> bool:
        """Удалить участника из игры"""
        try:
            cursor = await self.conn.execute("""
                DELETE FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, user_id))
            await self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка удаления участника: {e}")
            return False
    
    async def is_participant(self, game_id: int, user_id: int) -> bool:
        """Проверить, участвует ли пользователь в игре"""
        try:
            async with self.conn.execute("""
                SELECT COUNT(*) as count FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, user_id)) as cursor:
                row = await cursor.fetchone()
                return row["count"] > 0
        except Exception as e:
            logger.error(f"Ошибка проверки участника: {e}")
            return False
    
    async def get_participant_count(self, game_id: int) -> int:
        """Получить количество участников"""
        try:
            async with self.conn.execute("""
                SELECT COUNT(*) as count FROM participants
                WHERE game_id = ?
            """, (game_id,)) as cursor:
                row = await cursor.fetchone()
                return row["count"]
        except Exception as e:
            logger.error(f"Ошибка получения количества участников: {e}")
            return 0
    
    async def get_participants(self, game_id: int) -> List[Dict]:
        """Получить всех участников игры"""
        try:
            async with self.conn.execute("""
                SELECT * FROM participants
                WHERE game_id = ?
                ORDER BY joined_at
            """, (game_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения участников: {e}")
            return []
    
    async def set_victim(self, game_id: int, giver_id: int, victim_id: int) -> bool:
        """Установить жертву для дарителя"""
        try:
            await self.conn.execute("""
                UPDATE participants
                SET victim_id = ?
                WHERE game_id = ? AND user_id = ?
            """, (victim_id, game_id, giver_id))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка установки жертвы: {e}")
            return False
    
    async def get_victim(self, game_id: int, giver_id: int) -> Optional[Dict]:
        """Получить жертву для дарителя"""
        try:
            # Сначала получаем victim_id для дарителя
            async with self.conn.execute("""
                SELECT victim_id FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, giver_id)) as cursor:
                row = await cursor.fetchone()
                if not row or not row["victim_id"]:
                    return None
                
                victim_id = row["victim_id"]
            
            # Теперь получаем данные жертвы
            async with self.conn.execute("""
                SELECT * FROM participants
                WHERE game_id = ? AND user_id = ?
            """, (game_id, victim_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения жертвы: {e}")
            return None
    
    async def get_started_games(self) -> List[Dict]:
        """Получить все запущенные игры"""
        try:
            async with self.conn.execute("""
                SELECT * FROM games
                WHERE started = 1
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения запущенных игр: {e}")
            return []
    
    async def close(self):
        """Закрыть соединение с БД"""
        if self.conn:
            await self.conn.close()

