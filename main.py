"""
🎅 Тайный Санта Бот v666 🎅
Создан с любовью и 18 литрами энергетиков гением современности @Seb0g
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    FSInputFile,
    PhotoSize,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import Database
from config import Config

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("santa_bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
db = Database()


# ==================== FSM СОСТОЯНИЯ ====================

class GameStates(StatesGroup):
    """Состояния для FSM"""
    waiting_for_budget = State()
    waiting_for_wishlist = State()
    waiting_for_wishlist_photo = State()
    waiting_for_join_code = State()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def generate_join_code() -> str:
    """Генерирует уникальный код для присоединения"""
    import random
    import string
    # Генерируем код из 6 символов (буквы и цифры)
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(6))
    return code


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с кнопками"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Создать игру", callback_data="create_game"),
            InlineKeyboardButton(text="🔗 Присоединиться", callback_data="join_game"),
        ],
        [
            InlineKeyboardButton(text="📊 Мои игры", callback_data="my_games"),
            InlineKeyboardButton(text="📝 Правила", callback_data="show_rules"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot"),
        ],
    ])


def get_random_santa_message(username: str) -> str:
    """Возвращает рандомное мемное сообщение о жертве"""
    messages = [
        f"🎯 <b>Ты будешь дарить @{username}</b>\n\nНе облажайся, смертный! 🎁",
        f"🎯 <b>Твоя цель — @{username}</b>\n\nСделай так, чтобы он поверил в чудо… или в черную магию 🔮",
        f"🎯 <b>@{username} твой</b>\n\nБюджет не ограничен, но если подаришь носки — я найду тебя. 👀",
        f"🎯 <b>@{username} — твоя жертва</b>\n\nПодари что-то эпичное, а не очередной календарь на 2025! 📅",
        f"🎯 <b>@{username} ждёт подарка</b>\n\nНе разочаруй Санту, или я отправлю тебя в список непослушных! 😈",
    ]
    import random
    return random.choice(messages)


def get_roast_message(username: str) -> str:
    """Возвращает жесткий, но смешной роаст"""
    roasts = [
        f"🔥 <b>@{username}</b> — это тот, кто в детстве просил у Деда Мороза не игрушки, а чтобы родители не ругались. Теперь просит подарки у бота. Прогресс! 🎄",
        f"🔥 <b>@{username}</b> — единственный человек, который может опоздать на Новый год. Даже календарь его не ждёт! ⏰",
        f"🔥 <b>@{username}</b> — это тот, кто в прошлом году подарил себе носки. В этом году решил попробовать Тайного Санту. Надеюсь, не опять носки! 🧦",
        f"🔥 <b>@{username}</b> — легенда, которая может забыть про подарок даже с напоминанием бота. Респект за стабильность! 💪",
        f"🔥 <b>@{username}</b> — это тот, кто верит, что Новый год начнётся, когда он проснётся. Спойлер: уже начался! 🎉",
    ]
    import random
    return random.choice(roasts)


# ==================== КОМАНДЫ ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Проверяем, есть ли код в команде
    command_args = message.text.split() if message.text else []
    
    if len(command_args) > 1:
        # Присоединение по коду
        join_code = command_args[1].upper()
        await process_join_by_code(message, join_code)
        return
    
    # Обычное приветствие
    welcome_text = (
        "🎅 <b>Йо, смертный!</b> 🎅\n\n"
        "Я — <b>Тайный Санта Бот v666</b>, созданный богоподобным @Seb0g.\n\n"
        "Готовь подарки и жди магии! ✨\n\n"
        "Выбери действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    """Показывает правила игры"""
    rules_text = (
        "🎄 <b>ПРАВИЛА ТАЙНОГО САНТЫ 2025</b> 🎄\n\n"
        "1️⃣ <b>Создай игру</b> командой /newgame (только админы или в ЛС)\n\n"
        "2️⃣ <b>Вступи в игру</b> командой /join до дедлайна (7 дней)\n\n"
        "3️⃣ <b>Жди жеребьёвки</b> — создатель запускает /start_santa\n\n"
        "4️⃣ <b>Получи жертву</b> в ЛС командой /myvictim\n\n"
        "5️⃣ <b>Подари подарок</b> до Нового года (или после, но тогда Санта будет грустный 😢)\n\n"
        "6️⃣ <b>Не дари носки</b> — это клише, которое убивает магию! 🧦❌\n\n"
        "7️⃣ <b>Наслаждайся</b> процессом и не облажайся! 🎁✨\n\n"
        "<i>P.S. Если опоздал на регистрацию — извини, но Новый год только раз в году! 🎅</i>"
    )
    await message.answer(rules_text, parse_mode="HTML")


@dp.message(Command("about"))
async def cmd_about(message: Message):
    """Информация о боте"""
    about_text = (
        "🎅 <b>Тайный Санта Бот v666</b> 🎅\n\n"
        "Создан с любовью и 18 литрами энергетиков гением современности @Seb0g\n\n"
        "Версия: 666 (дьявольски стабильная)\n"
        "Технологии: aiogram 3.x, SQLite, Python 3.11+\n\n"
        "Если нашел баг — это фича. Если фича не работает — это баг.\n\n"
        "🎄 С наступающим, смертные! 🎄"
    )
    await message.answer(about_text, parse_mode="HTML")


@dp.callback_query(F.data == "create_game")
async def callback_create_game(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки создания игры"""
    user_id = callback.from_user.id
    chat_id = callback.from_user.id  # В ЛС chat_id = user_id
    
    # Генерируем уникальный код
    join_code = generate_join_code()
    # Проверяем уникальность (на случай коллизии)
    while await db.get_game_by_code(join_code):
        join_code = generate_join_code()
    
    # Создаём игру без бюджета (пока)
    deadline = datetime.now() + timedelta(days=7)
    game_id = await db.create_game(chat_id, user_id, deadline, None, join_code)
    
    if not game_id:
        await callback.answer("❌ Ошибка создания игры. Попробуй ещё раз.", show_alert=True)
        return
    
    # Сохраняем game_id в состояние
    await state.update_data(game_id=game_id, chat_id=chat_id, join_code=join_code)
    
    # Показываем кнопки для выбора бюджета
    budget_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 500₽", callback_data="budget_500"),
            InlineKeyboardButton(text="💰 1000₽", callback_data="budget_1000"),
        ],
        [
            InlineKeyboardButton(text="💰 1500₽", callback_data="budget_1500"),
            InlineKeyboardButton(text="💰 2000₽", callback_data="budget_2000"),
        ],
        [
            InlineKeyboardButton(text="💰 3000₽", callback_data="budget_3000"),
            InlineKeyboardButton(text="💰 5000₽", callback_data="budget_5000"),
        ],
        [
            InlineKeyboardButton(text="✏️ Свой бюджет", callback_data="budget_custom"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"),
        ],
    ])
    
    await callback.message.edit_text(
        "🎉 <b>Создание новой игры!</b> 🎉\n\n"
        "Выбери бюджет для подарков:\n\n"
        "💡 <i>Все участники будут знать бюджет и смогут указать свои желания</i>",
        reply_markup=budget_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.message(Command("newgame"))
async def cmd_newgame(message: Message, state: FSMContext):
    """Создать новую игру (команда)"""
    # Вызываем callback напрямую
    await callback_create_game(
        type('obj', (object,), {
            'message': message,
            'from_user': message.from_user,
            'answer': lambda x: None,
            'data': 'create_game'
        })(),
        state
    )
    
    # Показываем кнопки для выбора бюджета
    budget_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 500₽", callback_data="budget_500"),
            InlineKeyboardButton(text="💰 1000₽", callback_data="budget_1000"),
        ],
        [
            InlineKeyboardButton(text="💰 1500₽", callback_data="budget_1500"),
            InlineKeyboardButton(text="💰 2000₽", callback_data="budget_2000"),
        ],
        [
            InlineKeyboardButton(text="💰 3000₽", callback_data="budget_3000"),
            InlineKeyboardButton(text="💰 5000₽", callback_data="budget_5000"),
        ],
        [
            InlineKeyboardButton(text="✏️ Свой бюджет", callback_data="budget_custom"),
        ],
    ])
    
    # Пытаемся отправить фото если есть
    try:
        import os
        photo_path = "images/newgame.jpg"
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await message.answer_photo(
                photo,
                caption=(
                    "🎉 <b>Создание новой игры!</b> 🎉\n\n"
                    "Выбери бюджет для подарков:\n\n"
                    "💡 <i>Все участники будут знать бюджет и смогут указать свои желания</i>"
                ),
                reply_markup=budget_keyboard,
                parse_mode="HTML"
            )
        else:
            raise FileNotFoundError()
    except:
        # Если фото нет, отправляем просто текст
        await message.answer(
            "🎉 <b>Создание новой игры!</b> 🎉\n\n"
            "Выбери бюджет для подарков:\n\n"
            "💡 <i>Все участники будут знать бюджет и смогут указать свои желания</i>",
            reply_markup=budget_keyboard,
            parse_mode="HTML"
        )


@dp.callback_query(F.data.startswith("budget_"))
async def process_budget(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора бюджета"""
    budget_str = callback.data.split("_")[1]
    data = await state.get_data()
    game_id = data.get("game_id")
    join_code = data.get("join_code")
    
    if not game_id:
        await callback.answer("❌ Ошибка. Начни заново.", show_alert=True)
        return
    
    if budget_str == "custom":
        await callback.message.edit_text(
            "✏️ <b>Введи свой бюджет</b> ✏️\n\n"
            "Напиши сумму в рублях (только число, например: 2500)",
            parse_mode="HTML"
        )
        await state.set_state(GameStates.waiting_for_budget)
        await callback.answer()
        return
    
    try:
        budget = int(budget_str)
        success = await db.set_budget(game_id, budget)
        
        if success:
            deadline = datetime.now() + timedelta(days=7)
            bot_username = (await bot.get_me()).username
            join_link = f"https://t.me/{bot_username}?start={join_code}"
            
            share_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Скопировать ссылку", callback_data=f"copy_link_{join_code}")],
                [InlineKeyboardButton(text="📋 Код: " + join_code, callback_data="show_code")],
                [
                    InlineKeyboardButton(text="📊 Статус игры", callback_data=f"game_status_{game_id}"),
                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
                ],
            ])
            
            await callback.message.edit_text(
                f"✅ <b>Игра создана!</b> ✅\n\n"
                f"💰 Бюджет: <b>{budget}₽</b>\n"
                f"📅 Дедлайн: <b>{deadline.strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"🔑 Код: <code>{join_code}</code>\n\n"
                f"🔗 <b>Ссылка для присоединения:</b>\n"
                f"<code>{join_link}</code>\n\n"
                f"📤 Отправь эту ссылку друзьям, чтобы они могли присоединиться!",
                reply_markup=share_keyboard,
                parse_mode="HTML"
            )
            await state.clear()
            await callback.answer("✅ Игра создана!")
        else:
            await callback.answer("❌ Ошибка установки бюджета.", show_alert=True)
    except ValueError:
        await callback.answer("❌ Неверный формат бюджета.", show_alert=True)


@dp.message(GameStates.waiting_for_budget)
async def process_custom_budget(message: Message, state: FSMContext):
    """Обработка кастомного бюджета"""
    try:
        budget = int(message.text.strip())
        if budget <= 0:
            await message.answer("❌ Бюджет должен быть больше нуля! Попробуй ещё раз.")
            return
        
        data = await state.get_data()
        game_id = data.get("game_id")
        join_code = data.get("join_code")
        
        if not game_id:
            await message.answer("❌ Ошибка. Начни заново с /newgame")
            await state.clear()
            return
        
        success = await db.set_budget(game_id, budget)
        
        if success:
            deadline = datetime.now() + timedelta(days=7)
            bot_username = (await bot.get_me()).username
            join_link = f"https://t.me/{bot_username}?start={join_code}"
            
            share_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Скопировать ссылку", callback_data=f"copy_link_{join_code}")],
                [InlineKeyboardButton(text="📋 Код: " + join_code, callback_data="show_code")],
                [
                    InlineKeyboardButton(text="📊 Статус игры", callback_data=f"game_status_{game_id}"),
                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
                ],
            ])
            
            await message.answer(
                f"✅ <b>Игра создана!</b> ✅\n\n"
                f"💰 Бюджет: <b>{budget}₽</b>\n"
                f"📅 Дедлайн: <b>{deadline.strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"🔑 Код: <code>{join_code}</code>\n\n"
                f"🔗 <b>Ссылка для присоединения:</b>\n"
                f"<code>{join_link}</code>\n\n"
                f"📤 Отправь эту ссылку друзьям, чтобы они могли присоединиться!",
                reply_markup=share_keyboard,
                parse_mode="HTML"
            )
            await state.clear()
        else:
            await message.answer("❌ Ошибка установки бюджета. Попробуй ещё раз.")
    except ValueError:
        await message.answer("❌ Введи только число! Например: 2500")


async def process_join_by_code(message: Message, join_code: str):
    """Обработка присоединения по коду"""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    # Получаем игру по коду
    game = await db.get_game_by_code(join_code.upper())
    if not game:
        await message.answer(
            "❌ <b>Игра не найдена!</b> ❌\n\n"
            "Проверь код и попробуй ещё раз.\n"
            "Или используй кнопку 'Присоединиться' для ввода кода.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Проверяем дедлайн
    deadline = datetime.fromisoformat(game["deadline"])
    if datetime.now() > deadline:
        await message.answer(
            "⏰ <b>Опоздал, лошара!</b> ⏰\n\n"
            "Новый год только раз в году! Дедлайн регистрации прошёл. 😢",
            parse_mode="HTML"
        )
        return
    
    # Проверяем, не участвует ли уже
    if await db.is_participant(game["id"], user_id):
        # Проверяем, заполнен ли вишлист
        if not await db.has_wishlist(game["id"], user_id):
            wishlist_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Заполнить вишлист", callback_data=f"wishlist_{game['id']}")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ])
            await message.answer(
                f"🎄 Ты уже в игре!\n\n"
                f"💰 Бюджет: <b>{game.get('budget', 'Не указан')}₽</b>\n\n"
                f"⚠️ <b>Не забудь заполнить вишлист!</b>\n"
                f"Укажи, что ты хочешь получить в подарок.",
                reply_markup=wishlist_keyboard,
                parse_mode="HTML"
            )
        else:
            game_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Статус игры", callback_data=f"game_status_{game['id']}")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ])
            await message.answer(
                "🎄 Ты уже в игре! Используй кнопки ниже для управления.",
                reply_markup=game_keyboard
            )
        return
    
    # Добавляем участника
    success = await db.add_participant(game["id"], user_id, username)
    if success:
        count = await db.get_participant_count(game["id"])
        budget = game.get("budget", "Не указан")
        budget_text = f"{budget}₽" if isinstance(budget, int) else budget
        
        wishlist_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заполнить вишлист", callback_data=f"wishlist_{game['id']}")],
            [
                InlineKeyboardButton(text="📊 Статус игры", callback_data=f"game_status_{game['id']}"),
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
            ],
        ])
        
        await message.answer(
            f"✅ <b>Ты в игре!</b> ✅\n\n"
            f"💰 Бюджет: <b>{budget_text}</b>\n"
            f"👥 Участников: <b>{count}</b>\n"
            f"📅 Дедлайн: <b>{deadline.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"📝 <b>Важно!</b> Заполни вишлист — укажи, что ты хочешь получить в подарок!",
            reply_markup=wishlist_keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка добавления. Попробуй ещё раз.")


@dp.callback_query(F.data == "join_game")
async def callback_join_game(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки присоединения"""
    await callback.message.edit_text(
        "🔗 <b>Присоединение к игре</b> 🔗\n\n"
        "Введи код игры (6 символов) или отправь ссылку:\n\n"
        "💡 <i>Код можно получить у создателя игры</i>",
        parse_mode="HTML"
    )
    await state.set_state(GameStates.waiting_for_join_code)
    await callback.answer()


@dp.message(Command("join"))
async def cmd_join(message: Message, state: FSMContext):
    """Вступить в игру (команда)"""
    # Если есть аргумент - код
    command_args = message.text.split() if message.text else []
    if len(command_args) > 1:
        join_code = command_args[1].upper()
        await process_join_by_code(message, join_code)
    else:
        # Просим ввести код
        await message.answer(
            "🔗 <b>Присоединение к игре</b> 🔗\n\n"
            "Введи код игры (6 символов) или отправь ссылку:\n\n"
            "💡 <i>Код можно получить у создателя игры</i>\n\n"
            "Или используй /start КОД для быстрого присоединения",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )


@dp.message(GameStates.waiting_for_join_code)
async def process_join_code_input(message: Message, state: FSMContext):
    """Обработка ввода кода присоединения"""
    text = message.text.strip()
    
    # Извлекаем код из ссылки или берём как есть
    if "t.me" in text or "telegram.me" in text:
        # Пытаемся извлечь код из ссылки
        parts = text.split("start=")
        if len(parts) > 1:
            join_code = parts[-1].split()[0].upper()
        else:
            await message.answer("❌ Неверный формат ссылки. Введи код напрямую.")
            return
    else:
        join_code = text.upper().strip()
    
    if len(join_code) != 6:
        await message.answer("❌ Код должен состоять из 6 символов! Попробуй ещё раз.")
        return
    
    await state.clear()
    await process_join_by_code(message, join_code)


@dp.callback_query(F.data.startswith("wishlist_"))
async def start_wishlist(callback: CallbackQuery, state: FSMContext):
    """Начать заполнение вишлиста"""
    game_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Проверяем, участвует ли пользователь
    if not await db.is_participant(game_id, user_id):
        await callback.answer("❌ Ты не участвуешь в этой игре!", show_alert=True)
        return
    
    await state.update_data(game_id=game_id, user_id=user_id)
    await state.set_state(GameStates.waiting_for_wishlist)
    
    await callback.message.edit_text(
        "📝 <b>Заполнение вишлиста</b> 📝\n\n"
        "Напиши, что ты хочешь получить в подарок!\n\n"
        "💡 <i>Можешь написать текст или отправить фото с описанием</i>\n\n"
        "Пример: \"Хочу наушники или книгу по Python\"",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.message(Command("wishlist"))
async def cmd_wishlist(message: Message, state: FSMContext):
    """Команда для заполнения вишлиста"""
    user_id = message.from_user.id
    
    # Получаем игру пользователя
    game = await db.get_user_active_game(user_id)
    if not game:
        await message.answer(
            "❌ Ты не участвуешь ни в одной игре!\n\n"
            "Вступи в игру командой /join в группе."
        )
        return
    
    if game["started"]:
        await message.answer("❌ Жеребьёвка уже запущена! Нельзя изменить вишлист.")
        return
    
    await state.update_data(game_id=game["id"], user_id=user_id)
    await state.set_state(GameStates.waiting_for_wishlist)
    
    await message.answer(
        "📝 <b>Заполнение вишлиста</b> 📝\n\n"
        "Напиши, что ты хочешь получить в подарок!\n\n"
        "💡 <i>Можешь написать текст или отправить фото с описанием</i>\n\n"
        "Пример: \"Хочу наушники или книгу по Python\"",
        parse_mode="HTML"
    )


@dp.message(GameStates.waiting_for_wishlist, F.photo)
async def process_wishlist_photo(message: Message, state: FSMContext):
    """Обработка вишлиста с фото"""
    data = await state.get_data()
    game_id = data.get("game_id")
    user_id = data.get("user_id")
    
    if not game_id or not user_id:
        await message.answer("❌ Ошибка. Начни заново с /wishlist")
        await state.clear()
        return
    
    # Получаем самое большое фото
    photo = message.photo[-1]
    photo_id = photo.file_id
    
    # Получаем подпись к фото или просим текст
    wishlist_text = message.caption or ""
    
    if not wishlist_text:
        await state.update_data(photo_id=photo_id)
        await state.set_state(GameStates.waiting_for_wishlist_photo)
        await message.answer(
            "📸 Фото получено! Теперь напиши описание того, что ты хочешь получить."
        )
        return
    
    # Сохраняем вишлист
    success = await db.set_wishlist(game_id, user_id, wishlist_text, photo_id)
    
    if success:
        await message.answer(
            "✅ <b>Вишлист сохранён!</b> ✅\n\n"
            "Теперь твой Санта будет знать, что тебе подарить! 🎁",
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Ошибка сохранения вишлиста. Попробуй ещё раз.")


@dp.message(GameStates.waiting_for_wishlist_photo)
async def process_wishlist_text_after_photo(message: Message, state: FSMContext):
    """Обработка текста вишлиста после фото"""
    data = await state.get_data()
    game_id = data.get("game_id")
    user_id = data.get("user_id")
    photo_id = data.get("photo_id")
    
    if not game_id or not user_id:
        await message.answer("❌ Ошибка. Начни заново с /wishlist")
        await state.clear()
        return
    
    wishlist_text = message.text or ""
    
    if not wishlist_text:
        await message.answer("❌ Напиши описание! Что ты хочешь получить?")
        return
    
    # Сохраняем вишлист
    success = await db.set_wishlist(game_id, user_id, wishlist_text, photo_id)
    
    if success:
        await message.answer(
            "✅ <b>Вишлист сохранён!</b> ✅\n\n"
            "Теперь твой Санта будет знать, что тебе подарить! 🎁",
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Ошибка сохранения вишлиста. Попробуй ещё раз.")


@dp.message(GameStates.waiting_for_wishlist, F.text)
async def process_wishlist_text(message: Message, state: FSMContext):
    """Обработка текстового вишлиста"""
    data = await state.get_data()
    game_id = data.get("game_id")
    user_id = data.get("user_id")
    
    if not game_id or not user_id:
        await message.answer("❌ Ошибка. Начни заново с /wishlist")
        await state.clear()
        return
    
    wishlist_text = message.text.strip()
    
    if len(wishlist_text) < 5:
        await message.answer("❌ Слишком короткое описание! Напиши подробнее, что ты хочешь.")
        return
    
    # Сохраняем вишлист
    success = await db.set_wishlist(game_id, user_id, wishlist_text, None)
    
    if success:
        await message.answer(
            "✅ <b>Вишлист сохранён!</b> ✅\n\n"
            "Теперь твой Санта будет знать, что тебе подарить! 🎁",
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Ошибка сохранения вишлиста. Попробуй ещё раз.")


@dp.message(Command("leave"))
async def cmd_leave(message: Message):
    """Выйти из игры"""
    user_id = message.from_user.id
    chat_id = user_id  # В ЛС chat_id = user_id
    
    game = await db.get_active_game(chat_id)
    if not game:
        await message.answer("❌ У тебя нет активной игры!")
        return
    
    # Проверяем, запущена ли уже жеребьёвка
    if game["started"]:
        await message.answer(
            "❌ Жеребьёвка уже запущена! Нельзя выйти из игры."
        )
        return
    
    success = await db.remove_participant(game["id"], user_id)
    if success:
        await message.answer("👋 Ты вышел из игры. Увидимся в следующем году!")
    else:
        await message.answer("❌ Ты не был в игре.")


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Показать статус игры"""
    user_id = message.from_user.id
    chat_id = user_id  # В ЛС chat_id = user_id
    
    game = await db.get_active_game(chat_id)
    if not game:
        await message.answer("❌ В этом чате нет активной игры!")
        return
    
    count = await db.get_participant_count(game["id"])
    deadline = datetime.fromisoformat(game["deadline"])
    time_left = deadline - datetime.now()
    
    if time_left.total_seconds() > 0:
        days = int(time_left.days)
        hours = int(time_left.seconds // 3600)
        time_text = f"{days} дн. {hours} ч."
    else:
        time_text = "Дедлайн прошёл"
    
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    # Проверяем вишлисты
    participants_without_wishlist = await db.get_participants_without_wishlist(game["id"])
    wishlist_status = f"✅ Все заполнили" if not participants_without_wishlist else f"⚠️ {len(participants_without_wishlist)} без вишлиста"
    
    status_text = (
        f"🎄 <b>СТАТУС ИГРЫ</b> 🎄\n\n"
        f"💰 Бюджет: <b>{budget_text}</b>\n"
        f"👥 Участников: <b>{count}</b>\n"
        f"📝 Вишлисты: <b>{wishlist_status}</b>\n"
        f"📅 До дедлайна: <b>{time_text}</b>\n"
        f"🎲 Жеребьёвка: {'✅ Запущена' if game['started'] else '⏳ Ожидает'}\n\n"
    )
    
    if not game["started"]:
        if count < 3:
            status_text += "⚠️ Нужно минимум 3 участника для жеребьёвки!"
        else:
            status_text += "✅ Можно запускать жеребьёвку командой /start_santa"
    
    await message.answer(status_text, parse_mode="HTML")


@dp.message(Command("start_santa"))
async def cmd_start_santa(message: Message):
    """Запустить жеребьёвку"""
    user_id = message.from_user.id
    chat_id = user_id  # В ЛС chat_id = user_id
    
    game = await db.get_active_game(chat_id)
    if not game:
        await message.answer("❌ В этом чате нет активной игры!")
        return
    
    # Проверяем, что это создатель игры
    if game["creator_id"] != user_id:
        await message.answer("❌ Только создатель игры может запустить жеребьёвку!")
        return
    
    # Проверяем, не запущена ли уже
    if game["started"]:
        await message.answer("✅ Жеребьёвка уже была запущена!")
        return
    
    # Проверяем количество участников
    count = await db.get_participant_count(game["id"])
    if count < 3:
        await message.answer(
            f"❌ Нужно минимум 3 участника! Сейчас: {count}\n\n"
            f"Подожди ещё немного или позови друзей!"
        )
        return
    
    # Получаем всех участников
    participants = await db.get_participants(game["id"])
    
    # Проверяем, все ли заполнили вишлисты
    participants_without_wishlist = await db.get_participants_without_wishlist(game["id"])
    if participants_without_wishlist:
        usernames = [p["username"] for p in participants_without_wishlist]
        await message.answer(
            f"⚠️ <b>Не все заполнили вишлисты!</b> ⚠️\n\n"
            f"Следующие участники ещё не указали свои желания:\n"
            f"{', '.join(['@' + u for u in usernames])}\n\n"
            f"Попроси их заполнить вишлист командой /wishlist",
            parse_mode="HTML"
        )
        return
    
    # Создаём derangement (перестановка без неподвижных точек)
    import random
    giver_ids = [p["user_id"] for p in participants]
    receiver_ids = giver_ids.copy()
    
    # Алгоритм Fisher-Yates для создания derangement
    max_attempts = 100
    derangement_ok = False
    for attempt in range(max_attempts):
        random.shuffle(receiver_ids)
        # Проверяем, что нет неподвижных точек
        if all(giver_ids[i] != receiver_ids[i] for i in range(len(giver_ids))):
            derangement_ok = True
            break
    
    if not derangement_ok:
        # Крайне редкий случай - если не получилось, пробуем ещё раз с другим подходом
        logger.warning("Не удалось создать derangement за 100 попыток, пробуем ещё раз...")
        for _ in range(1000):  # Даём ещё 1000 попыток
            random.shuffle(receiver_ids)
            if all(giver_ids[i] != receiver_ids[i] for i in range(len(giver_ids))):
                derangement_ok = True
                break
    
    if not derangement_ok:
        await message.answer(
            "❌ Ошибка жеребьёвки! Попробуй ещё раз.\n\n"
            "Если проблема повторяется — обратись к создателю бота."
        )
        return
    
    # Сохраняем пары
    for i, giver_id in enumerate(giver_ids):
        receiver_id = receiver_ids[i]
        await db.set_victim(game["id"], giver_id, receiver_id)
    
    # Запускаем игру только после успешной жеребьёвки
    success = await db.start_game(game["id"])
    if not success:
        await message.answer("❌ Ошибка запуска жеребьёвки. Попробуй ещё раз.")
        return
    
    # Отправляем сообщения всем участникам в ЛС
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    for i, giver in enumerate(participants):
        receiver = next(p for p in participants if p["user_id"] == receiver_ids[i])
        receiver_username = receiver["username"]
        receiver_wishlist = receiver.get("wishlist", "Не указан")
        receiver_photo = receiver.get("wishlist_photo")
        
        message_text = get_random_santa_message(receiver_username)
        message_text += f"\n\n🎁 <b>Твоя жертва:</b> @{receiver_username}\n"
        message_text += f"💰 <b>Бюджет:</b> {budget_text}\n\n"
        message_text += f"📝 <b>Что хочет получить:</b>\n{receiver_wishlist}"
        
        try:
            # Если есть фото, отправляем с фото
            if receiver_photo:
                await bot.send_photo(
                    giver["user_id"],
                    receiver_photo,
                    caption=message_text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    giver["user_id"],
                    message_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {giver['user_id']}: {e}")
            # Пытаемся отправить сообщение в группу, если не получилось в ЛС
            try:
                await message.answer(
                    f"⚠️ Не удалось отправить сообщение @{giver['username']} в ЛС.\n"
                    f"Попроси его написать боту /start в личных сообщениях!"
                )
            except:
                pass
    
    await message.answer(
        "🎉 <b>Жеребьёвка запущена!</b> 🎉\n\n"
        "Все участники получили свои жертвы в личные сообщения!\n\n"
        "Используй /myvictim в ЛС чтобы посмотреть, кому ты даришь! 🎁",
        parse_mode="HTML"
    )


@dp.message(Command("myvictim"))
async def cmd_myvictim(message: Message):
    """Показать жертву пользователя"""
    user_id = message.from_user.id
    
    # Получаем игру, где пользователь участвует
    game = await db.get_user_active_game(user_id)
    if not game:
        await message.answer(
            "❌ Ты не участвуешь ни в одной игре!\n\n"
            "Вступи в игру командой /join в группе."
        )
        return
    
    # Проверяем, запущена ли жеребьёвка
    if not game["started"]:
        await message.answer(
            "⏳ <b>Терпение, юный падаван</b> ⏳\n\n"
            "Саня ещё пьёт энергетики и крутит барабан судьбы. 🎅\n\n"
            "Жди запуска жеребьёвки!",
            parse_mode="HTML"
        )
        return
    
    # Получаем жертву
    victim = await db.get_victim(game["id"], user_id)
    if not victim:
        await message.answer("❌ Ошибка получения жертвы. Обратись к создателю игры.")
        return
    
    victim_username = victim["username"]
    victim_wishlist = victim.get("wishlist", "Не указан")
    victim_photo = victim.get("wishlist_photo")
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    message_text = (
        f"🎯 <b>ТВОЯ ЖЕРТВА</b> 🎯\n\n"
        f"🎁 <b>Имя:</b> @{victim_username}\n"
        f"💰 <b>Бюджет:</b> {budget_text}\n\n"
        f"📝 <b>Что хочет получить:</b>\n{victim_wishlist}\n\n"
        f"🔥 Не облажайся, смертный! Подари что-то эпичное! 🔥"
    )
    
    # Если есть фото, отправляем с фото
    try:
        if victim_photo:
            await message.answer_photo(
                victim_photo,
                caption=message_text,
                parse_mode="HTML"
            )
        else:
            await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        await message.answer(message_text, parse_mode="HTML")


@dp.message(Command("roast"))
async def cmd_roast(message: Message):
    """Роаст участника"""
    chat_id = message.chat.id
    
    # Проверяем, есть ли активная игра
    game = await db.get_active_game(chat_id)
    if not game:
        await message.answer("❌ В этом чате нет активной игры!")
        return
    
    # Парсим username из команды
    command_text = message.text or ""
    parts = command_text.split()
    
    if len(parts) < 2:
        await message.answer(
            "🔥 <b>Использование:</b> /roast @username\n\n"
            "Роастну указанного участника игры!",
            parse_mode="HTML"
        )
        return
    
    target_username = parts[1].replace("@", "")
    
    # Проверяем, участвует ли пользователь
    participants = await db.get_participants(game["id"])
    target_user = next((p for p in participants if p["username"] == target_username), None)
    
    if not target_user:
        await message.answer(
            f"❌ @{target_username} не участвует в игре!\n\n"
            f"Используй /status чтобы посмотреть участников."
        )
        return
    
    roast_text = get_roast_message(target_username)
    await message.answer(roast_text, parse_mode="HTML")


# ==================== ФОНОВЫЕ ЗАДАЧИ ====================

async def check_new_year_reminders():
    """Проверка и отправка напоминаний после Нового года"""
    while True:
        try:
            await asyncio.sleep(3600)  # Проверяем каждый час
            now = datetime.now()
            # Проверяем, прошёл ли Новый год (после 1 января)
            if now.month == 1 and now.day >= 1:
                logger.info("🎄 Проверка напоминаний о подарках...")
                started_games = await db.get_started_games()
                
                for game in started_games:
                    participants = await db.get_participants(game["id"])
                    reminder_text = (
                        "🎄 <b>Напоминание от Санты</b> 🎄\n\n"
                        "Ну что, подарил уже? Или опять носки? Я слежу за тобой 👀\n\n"
                        "Не забудь сделать подарок своему тайному другу! 🎁"
                    )
                    
                    for participant in participants:
                        try:
                            await bot.send_message(
                                participant["user_id"],
                                reminder_text,
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка отправки напоминания {participant['user_id']}: {e}")
                
                # Отправляем напоминания только один раз в день
                await asyncio.sleep(86400)
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(3600)


# ==================== ОБРАБОТЧИКИ CALLBACK КНОПОК ====================

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Главное меню"""
    welcome_text = (
        "🎅 <b>Главное меню</b> 🎅\n\n"
        "Выбери действие:"
    )
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "show_rules")
async def callback_show_rules(callback: CallbackQuery):
    """Показать правила"""
    rules_text = (
        "🎄 <b>ПРАВИЛА ТАЙНОГО САНТЫ 2025</b> 🎄\n\n"
        "1️⃣ <b>Создай игру</b> через кнопку 'Создать игру'\n\n"
        "2️⃣ <b>Присоединись к игре</b> по ссылке или коду\n\n"
        "3️⃣ <b>Заполни вишлист</b> — укажи, что хочешь получить\n\n"
        "4️⃣ <b>Жди жеребьёвки</b> — создатель запускает игру\n\n"
        "5️⃣ <b>Получи жертву</b> в ЛС с её вишлистом\n\n"
        "6️⃣ <b>Подари подарок</b> до Нового года! 🎁\n\n"
        "7️⃣ <b>Не дари носки</b> — это клише! 🧦❌"
    )
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        rules_text,
        reply_markup=back_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "about_bot")
async def callback_about_bot(callback: CallbackQuery):
    """О боте"""
    about_text = (
        "🎅 <b>Тайный Санта Бот v666</b> 🎅\n\n"
        "Создан с любовью и 18 литрами энергетиков гением современности @Seb0g\n\n"
        "Версия: 666 (дьявольски стабильная)\n"
        "Технологии: aiogram 3.x, SQLite, Python 3.11+\n\n"
        "Если нашел баг — это фича. Если фича не работает — это баг.\n\n"
        "🎄 С наступающим, смертные! 🎄"
    )
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        about_text,
        reply_markup=back_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "my_games")
async def callback_my_games(callback: CallbackQuery):
    """Мои игры"""
    user_id = callback.from_user.id
    
    # Получаем все игры пользователя (созданные и где участвует)
    created_games = await db.get_user_created_games(user_id)
    participant_games = await db.get_user_participant_games(user_id)
    
    # Объединяем и убираем дубликаты
    all_games = {}
    for game in created_games + participant_games:
        all_games[game["id"]] = game
    
    if not all_games:
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Создать игру", callback_data="create_game")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            "📊 <b>Мои игры</b> 📊\n\n"
            "У тебя нет игр.\n\n"
            "Создай новую игру или присоединись к существующей!",
            reply_markup=back_keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Сортируем по дате создания
    games_list = sorted(all_games.values(), key=lambda x: x["created_at"], reverse=True)
    
    # Формируем список игр с кнопками
    games_text = "📊 <b>МОИ ИГРЫ</b> 📊\n\n"
    keyboard_buttons = []
    
    for i, game in enumerate(games_list[:10]):  # Показываем максимум 10 игр
        budget = game.get("budget", "Не указан")
        budget_text = f"{budget}₽" if isinstance(budget, int) else budget
        status_emoji = "✅" if game["started"] else "⏳"
        is_creator = game["creator_id"] == user_id
        
        games_text += f"{status_emoji} <b>Игра #{game['id']}</b>\n"
        games_text += f"💰 {budget_text} | "
        if is_creator:
            games_text += "👑 Создатель\n"
        else:
            games_text += "👤 Участник\n"
        games_text += f"🔑 Код: <code>{game.get('join_code', 'N/A')}</code>\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Игра #{game['id']} ({budget_text})",
                callback_data=f"game_status_{game['id']}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🎮 Создать новую игру", callback_data="create_game")])
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    
    games_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        games_text,
        reply_markup=games_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("game_status_"))
async def callback_game_status(callback: CallbackQuery):
    """Статус игры"""
    game_id = int(callback.data.split("_")[2])
    await show_game_status(callback, game_id)
    await callback.answer()


async def show_game_status(callback: CallbackQuery, game_id: int):
    """Показать статус игры"""
    # Получаем игру по ID
    game = await db.get_game_by_id(game_id)
    if not game:
        await callback.message.edit_text(
            "❌ Игра не найдена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
            ])
        )
        return
    
    count = await db.get_participant_count(game_id)
    deadline = datetime.fromisoformat(game["deadline"])
    time_left = deadline - datetime.now()
    
    if time_left.total_seconds() > 0:
        days = int(time_left.days)
        hours = int(time_left.seconds // 3600)
        time_text = f"{days} дн. {hours} ч."
    else:
        time_text = "Дедлайн прошёл"
    
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    # Проверяем вишлисты
    participants_without_wishlist = await db.get_participants_without_wishlist(game_id)
    wishlist_status = f"✅ Все заполнили" if not participants_without_wishlist else f"⚠️ {len(participants_without_wishlist)} без вишлиста"
    
    is_creator = game["creator_id"] == callback.from_user.id
    is_participant = await db.is_participant(game_id, callback.from_user.id)
    
    status_text = (
        f"📊 <b>СТАТУС ИГРЫ</b> 📊\n\n"
        f"💰 Бюджет: <b>{budget_text}</b>\n"
        f"👥 Участников: <b>{count}</b>\n"
        f"📝 Вишлисты: <b>{wishlist_status}</b>\n"
        f"📅 До дедлайна: <b>{time_text}</b>\n"
        f"🎲 Жеребьёвка: {'✅ Запущена' if game['started'] else '⏳ Ожидает'}\n"
        f"🔑 Код: <code>{game.get('join_code', 'N/A')}</code>\n\n"
    )
    
    keyboard_buttons = []
    
    if is_creator and not game["started"]:
        # Кнопка запуска жеребьёвки - всегда показываем для создателя
        keyboard_buttons.append([InlineKeyboardButton(text="🎲 Запустить жеребьёвку", callback_data=f"start_santa_{game_id}")])
        
        # Предупреждения, если условия не выполнены
        if count < 3:
            status_text += "⚠️ Нужно минимум 3 участника для запуска!\n"
        if participants_without_wishlist:
            status_text += "⚠️ Не все заполнили вишлисты!\n"
        
        # Кнопка удаления игры (только для создателя и только до запуска)
        keyboard_buttons.append([InlineKeyboardButton(text="🗑️ Удалить игру", callback_data=f"delete_game_{game_id}")])
    
    if is_participant and not game["started"]:
        if not await db.has_wishlist(game_id, callback.from_user.id):
            keyboard_buttons.append([InlineKeyboardButton(text="📝 Заполнить вишлист", callback_data=f"wishlist_{game_id}")])
        # Участник может выйти из игры
        keyboard_buttons.append([InlineKeyboardButton(text="👋 Выйти из игры", callback_data=f"leave_game_{game_id}")])
    
    if game["started"] and is_participant:
        keyboard_buttons.append([InlineKeyboardButton(text="🎯 Моя жертва", callback_data=f"my_victim_{game_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    
    status_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        status_text,
        reply_markup=status_keyboard,
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("copy_link_"))
async def callback_copy_link(callback: CallbackQuery):
    """Копирование ссылки"""
    join_code = callback.data.split("_")[2]
    bot_username = (await bot.get_me()).username
    join_link = f"https://t.me/{bot_username}?start={join_code}"
    
    await callback.answer(f"🔗 Ссылка: {join_link}", show_alert=True)


@dp.callback_query(F.data == "show_code")
async def callback_show_code(callback: CallbackQuery):
    """Показать код"""
    # Код уже показан в сообщении, просто подтверждаем
    await callback.answer("✅ Код скопирован в сообщении выше!")


@dp.callback_query(F.data.startswith("start_santa_"))
async def callback_start_santa(callback: CallbackQuery):
    """Запуск жеребьёвки через кнопку"""
    game_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    game = await db.get_active_game(user_id)
    if not game or game["id"] != game_id:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if game["creator_id"] != user_id:
        await callback.answer("❌ Только создатель может запустить жеребьёвку!", show_alert=True)
        return
    
    # Используем логику из cmd_start_santa, но адаптируем для callback
    if game["started"]:
        await callback.answer("✅ Жеребьёвка уже была запущена!", show_alert=True)
        return
    
    count = await db.get_participant_count(game_id)
    if count < 3:
        await callback.answer(f"❌ Нужно минимум 3 участника! Сейчас: {count}", show_alert=True)
        return
    
    participants = await db.get_participants(game_id)
    participants_without_wishlist = await db.get_participants_without_wishlist(game_id)
    if participants_without_wishlist:
        usernames = [p["username"] for p in participants_without_wishlist]
        await callback.answer(
            f"⚠️ Не все заполнили вишлисты: {', '.join(['@' + u for u in usernames])}",
            show_alert=True
        )
        return
    
    # Запускаем жеребьёвку (код из cmd_start_santa)
    import random
    giver_ids = [p["user_id"] for p in participants]
    receiver_ids = giver_ids.copy()
    
    max_attempts = 100
    derangement_ok = False
    for attempt in range(max_attempts):
        random.shuffle(receiver_ids)
        if all(giver_ids[i] != receiver_ids[i] for i in range(len(giver_ids))):
            derangement_ok = True
            break
    
    if not derangement_ok:
        for _ in range(1000):
            random.shuffle(receiver_ids)
            if all(giver_ids[i] != receiver_ids[i] for i in range(len(giver_ids))):
                derangement_ok = True
                break
    
    if not derangement_ok:
        await callback.answer("❌ Ошибка жеребьёвки! Попробуй ещё раз.", show_alert=True)
        return
    
    for i, giver_id in enumerate(giver_ids):
        receiver_id = receiver_ids[i]
        await db.set_victim(game_id, giver_id, receiver_id)
    
    success = await db.start_game(game_id)
    if not success:
        await callback.answer("❌ Ошибка запуска жеребьёвки!", show_alert=True)
        return
    
    # Отправляем сообщения участникам
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    for i, giver in enumerate(participants):
        receiver = next(p for p in participants if p["user_id"] == receiver_ids[i])
        receiver_username = receiver["username"]
        receiver_wishlist = receiver.get("wishlist", "Не указан")
        receiver_photo = receiver.get("wishlist_photo")
        
        message_text = get_random_santa_message(receiver_username)
        message_text += f"\n\n🎁 <b>Твоя жертва:</b> @{receiver_username}\n"
        message_text += f"💰 <b>Бюджет:</b> {budget_text}\n\n"
        message_text += f"📝 <b>Что хочет получить:</b>\n{receiver_wishlist}"
        
        try:
            if receiver_photo:
                await bot.send_photo(giver["user_id"], receiver_photo, caption=message_text, parse_mode="HTML")
            else:
                await bot.send_message(giver["user_id"], message_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {giver['user_id']}: {e}")
    
    await callback.message.edit_text(
        "🎉 <b>Жеребьёвка запущена!</b> 🎉\n\n"
        "Все участники получили свои жертвы в личные сообщения!\n\n"
        "Используй кнопку 'Моя жертва' чтобы посмотреть, кому ты даришь! 🎁",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Моя жертва", callback_data=f"my_victim_{game_id}")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ]),
        parse_mode="HTML"
    )
    await callback.answer("✅ Жеребьёвка запущена!")


@dp.callback_query(F.data.startswith("delete_game_"))
async def callback_delete_game(callback: CallbackQuery):
    """Удаление игры с подтверждением"""
    game_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    game = await db.get_active_game(user_id)
    if not game or game["id"] != game_id:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if game["creator_id"] != user_id:
        await callback.answer("❌ Только создатель может удалить игру!", show_alert=True)
        return
    
    if game["started"]:
        await callback.answer("❌ Нельзя удалить запущенную игру!", show_alert=True)
        return
    
    # Показываем подтверждение
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{game_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"game_status_{game_id}"),
        ],
    ])
    
    count = await db.get_participant_count(game_id)
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b> ⚠️\n\n"
        f"Ты уверен, что хочешь удалить игру?\n\n"
        f"📊 Участников: <b>{count}</b>\n"
        f"💰 Бюджет: <b>{game.get('budget', 'Не указан')}₽</b>\n\n"
        f"<b>Это действие нельзя отменить!</b>\n"
        f"Все участники будут удалены из игры.",
        reply_markup=confirm_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_delete_"))
async def callback_confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления игры"""
    game_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    game = await db.get_active_game(user_id)
    if not game or game["id"] != game_id:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if game["creator_id"] != user_id:
        await callback.answer("❌ Только создатель может удалить игру!", show_alert=True)
        return
    
    if game["started"]:
        await callback.answer("❌ Нельзя удалить запущенную игру!", show_alert=True)
        return
    
    # Получаем участников для уведомления
    participants = await db.get_participants(game_id)
    
    # Удаляем игру
    success = await db.delete_game(game_id)
    
    if success:
        # Уведомляем участников
        for participant in participants:
            if participant["user_id"] != user_id:  # Создателя не уведомляем
                try:
                    await bot.send_message(
                        participant["user_id"],
                        "❌ <b>Игра была удалена</b> ❌\n\n"
                        "Создатель игры удалил её. Если хочешь создать новую игру, используй /start",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления участника {participant['user_id']}: {e}")
        
        # Показываем успешное удаление
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Создать новую игру", callback_data="create_game")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        
        await callback.message.edit_text(
            "✅ <b>Игра удалена!</b> ✅\n\n"
            "Все участники были уведомлены об удалении игры.\n\n"
            "Можешь создать новую игру!",
            reply_markup=back_keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Игра удалена!")
    else:
        await callback.answer("❌ Ошибка удаления игры!", show_alert=True)


@dp.callback_query(F.data.startswith("leave_game_"))
async def callback_leave_game(callback: CallbackQuery):
    """Выход из игры через кнопку"""
    game_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    game = await db.get_active_game(user_id)
    if not game or game["id"] != game_id:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if game["started"]:
        await callback.answer("❌ Нельзя выйти из запущенной игры!", show_alert=True)
        return
    
    if not await db.is_participant(game_id, user_id):
        await callback.answer("❌ Ты не участвуешь в этой игре!", show_alert=True)
        return
    
    # Удаляем участника
    success = await db.remove_participant(game_id, user_id)
    
    if success:
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            "👋 <b>Ты вышел из игры</b> 👋\n\n"
            "Увидимся в следующей игре!",
            reply_markup=back_keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Ты вышел из игры!")
    else:
        await callback.answer("❌ Ошибка выхода из игры!", show_alert=True)


@dp.callback_query(F.data.startswith("my_victim_"))
async def callback_my_victim(callback: CallbackQuery):
    """Показать жертву через кнопку"""
    game_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    game = await db.get_user_active_game(user_id)
    if not game or game["id"] != game_id:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return
    
    if not game["started"]:
        await callback.answer("⏳ Жеребьёвка ещё не запущена!", show_alert=True)
        return
    
    # Получаем жертву
    victim = await db.get_victim(game_id, user_id)
    if not victim:
        await callback.answer("❌ Ошибка получения жертвы!", show_alert=True)
        return
    
    victim_username = victim["username"]
    victim_wishlist = victim.get("wishlist", "Не указан")
    victim_photo = victim.get("wishlist_photo")
    budget = game.get("budget", "Не указан")
    budget_text = f"{budget}₽" if isinstance(budget, int) else budget
    
    message_text = (
        f"🎯 <b>ТВОЯ ЖЕРТВА</b> 🎯\n\n"
        f"🎁 <b>Имя:</b> @{victim_username}\n"
        f"💰 <b>Бюджет:</b> {budget_text}\n\n"
        f"📝 <b>Что хочет получить:</b>\n{victim_wishlist}\n\n"
        f"🔥 Не облажайся, смертный! Подари что-то эпичное! 🔥"
    )
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
    ])
    
    try:
        if victim_photo:
            await callback.message.delete()
            await callback.message.answer_photo(
                victim_photo,
                caption=message_text,
                reply_markup=back_keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                message_text,
                reply_markup=back_keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        await callback.message.edit_text(
            message_text,
            reply_markup=back_keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция запуска бота"""
    logger.info("🎅 Запуск Тайного Санты Бота v666...")
    
    # Инициализация БД
    await db.init()
    
    # Проверка токена
    if not os.getenv("BOT_TOKEN"):
        logger.error("❌ BOT_TOKEN не найден в .env файле!")
        return
    
    # Запускаем фоновую задачу для напоминаний
    asyncio.create_task(check_new_year_reminders())
    
    # Запуск бота
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

