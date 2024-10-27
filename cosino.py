import random
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = '8168488635:AAF7a_uf9BxpxxSmowZgjgcnVqiVeJEQBcg'

ADMIN_IDS = [1499120550] #админ айди

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_balance = {}
user_registration_date = {}
active_games = {}
user_bets = {}
game_history = {} 

START_BALANCE = 300

class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_number = State()
    waiting_for_range = State()
    waiting_for_choice = State()

class ReferralStates(StatesGroup):
    waiting_for_referral_id = State()


def create_database():
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        referral_used INTEGER DEFAULT 0,  -- 0 - не использован, 1 - использован
        referrals_count INTEGER DEFAULT 0, -- количество рефералов
        registration_date TEXT
    )
    ''')

    conn.commit()
    conn.close()

def increment_referral_count(referral_user_id: int):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE users 
    SET referrals_count = referrals_count + 1 
    WHERE user_id = ?
    ''', (referral_user_id,))

    conn.commit()
    conn.close()


def update_balance_in_db(user_id: int, balance: int):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO users (user_id, balance) VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET balance=excluded.balance
    ''', (user_id, balance))

    conn.commit()
    conn.close()

def load_users_from_db():
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, balance, registration_date FROM users')
    rows = cursor.fetchall()

    for user_id, balance, registration_date in rows:
        user_balance[user_id] = balance
        user_registration_date[user_id] = registration_date
        game_history[user_id] = [] 

    conn.close()


async def add_daily_coins():
    for user_id in user_balance.keys():
        user_balance[user_id] += 300 
        print(f"Добавлено 300 монет пользователю {user_id}. Новый баланс: {user_balance[user_id]}.")


scheduler = AsyncIOScheduler()
scheduler.add_job(add_daily_coins, 'interval', days=1)  
scheduler.start()

def home_selection_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль"),KeyboardButton(text="Играть")],
            [KeyboardButton(text="Баланс"),KeyboardButton(text="Реферальная система")],
            [KeyboardButton(text="История последних игр"),KeyboardButton(text="Наши проекты")],
        ],
        resize_keyboard=True
    )
    return keyboard


def game_selection_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Кубик"),KeyboardButton(text="🎯 Дартс")],
            [KeyboardButton(text="🏀 Баскетбол"),KeyboardButton(text="⚽ Футбол")],
            [KeyboardButton(text="🎳 Боулинг"),KeyboardButton(text="🎰 Слоты")],
            [KeyboardButton(text="Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard

def betting_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="10 монет"), KeyboardButton(text="50 монет"), KeyboardButton(text="100 монет")],
            [KeyboardButton(text="200 монет"), KeyboardButton(text="500 монет"), KeyboardButton(text="1000 монет")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def cube_betting_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ставка на число (6x)"), KeyboardButton(text="Ставка на промежутки (3x)")],
            [KeyboardButton(text="Ставка больше/меньше 3"), KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def cube_rate_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1-2"), KeyboardButton(text="3-4")],
            [KeyboardButton(text="5-6"), KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def cube_half_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Больше"), KeyboardButton(text="Меньше")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(CommandStart())
async def start_game(message: Message):
    user_id = message.from_user.id
    referral_user_id = None  

    if user_id not in user_balance:
        user_balance[user_id] = START_BALANCE
        user_registration_date[user_id] = message.date.strftime('%Y-%m-%d')
        if referral_user_id:
            increment_referral_count(referral_user_id)

        update_balance_in_db(user_id, START_BALANCE)

    await message.answer(f"Добро пожаловать! Ваш баланс: {user_balance[user_id]} монет.")

@dp.message(Command(commands=['referrals']))
async def show_referrals(message: Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()

    cursor.execute('SELECT referrals_count FROM users WHERE user_id = ?', (user_id,))
    referrals_count = cursor.fetchone()[0]

    await message.answer(f"У вас {referrals_count} рефералов.")
    conn.close()


@dp.message(Command('player_count'))
async def player_count_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        count = len(user_balance)  
        await message.answer(f"Количество игроков: {count}")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('top_players'))
async def top_players_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        sorted_players = sorted(user_balance.items(), key=lambda x: x[1], reverse=True)[:10]
        top_players_message = "Топ 10 игроков по балансу:\n"
        for user_id, balance in sorted_players:
            top_players_message += f"ID: {user_id}, Баланс: {balance} монет\n"
        await message.answer(top_players_message)
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('set_balance'))
async def set_balance_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split()
            user_id = int(args[1])
            new_balance = int(args[2])

            if user_id in user_balance:
                user_balance[user_id] = new_balance
                update_balance_in_db(user_id, new_balance) 
                await message.answer(f"Баланс игрока {user_id} обновлён на {new_balance} монет.")
                await notify_user_balance_change(user_id, new_balance)
            else:
                await message.answer(f"Игрок с ID {user_id} не найден.")
        except (IndexError, ValueError):
            await message.answer("Неверный формат команды. Используйте: /set_balance user_id new_balance")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('set_balance_all'))
async def set_balance_handler(message: Message):
    for user_id in user_balance.keys():
        if user_balance[user_id] < 10:
            user_balance[user_id] += 100
            update_balance_in_db(user_id, user_balance[user_id])
            await message.answer(f"Добавлено 100 монет пользователю {user_id}. Новый баланс: {user_balance[user_id]}.")
    

@dp.message(Command('admin_send_mes'))
async def admin_send_message_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer("Пожалуйста, укажите сообщение для отправки.")
                return
            
            message_to_send = args[1]  

            conn = sqlite3.connect('casino.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            conn.close()
 
            for user in users:
                user_id = user[0]
                try:
                    await bot.send_message(user_id, message_to_send)
                except Exception as e:
                    print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

            await message.answer("Сообщение успешно отправлено всем пользователям.")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('admin_add'))
async def admin_add_handler(message:  Message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer("Пожалуйста, укажите ID администратора для добавления.")
                return
            
            admin_id_to_add = int(args[1]) 
            
            if admin_id_to_add not in ADMIN_IDS:
                ADMIN_IDS.append(admin_id_to_add)
                await message.answer("Администратор успешно добавлен.")
            else:
                await message.answer("Этот пользователь уже является администратором.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID администратора.")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('admin_show'))
async def admin_show_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        try:
            admin_list = "\n".join(str(i) for i in ADMIN_IDS)
            await message.answer(f"Список администраторов:\n{admin_list}")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('admin_del'))
async def admin_del_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer("Пожалуйста, укажите ID администратора для удаления.")
                return
            
            admin_id_to_remove = int(args[1])  
            
            if admin_id_to_remove in ADMIN_IDS:
                ADMIN_IDS.remove(admin_id_to_remove)
                await message.answer("Администратор успешно удалён.")
            else:
                await message.answer("Этот пользователь не является администратором.")
        except ValueError:
            await message.answer("Пожалуйста, введите корректный ID администратора.")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

async def send_message_to_all_users(message_text: str):
    """Отправляет сообщение всем зарегистрированным пользователям."""
    for user_id in user_balance.keys():
        try:
            await bot.send_message(user_id, message_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def notify_user_balance_change(user_id: int, new_balance: int):
    """Уведомляет пользователя об изменении его баланса."""
    if user_id in user_balance:
        await bot.send_message(user_id, f"Ваш баланс был изменён администратором. Новый баланс: {new_balance} монет.")

@dp.message(F.text == "История последних игр")
async def game_history_handler(message: Message):
    user_id = message.from_user.id
    history = game_history.get(user_id, [])
    
    if not history:
        await message.answer("У вас пока нет истории игр.")
        return

    history_message = "История последних игр:\n"
    for idx, (game, balance) in enumerate(reversed(history[-5:]), start=1): 
        history_message += f"{idx}. Игра: {game}, Баланс: {balance} монет\n"

    await message.answer(history_message)

@dp.message(F.text == "Профиль")
async def profile_handler(message: Message):
    user_id = message.from_user.id
    registration_date = user_registration_date.get(user_id, "Неизвестно")
    balance = user_balance.get(user_id, START_BALANCE)
    await message.answer(f"Ваш профиль: {user_id}\nДата регистрации: {registration_date}\nБаланс: {balance} монет.")

@dp.message(F.text == "Баланс")
async def check_balance(message: Message):
    user_id = message.from_user.id
    balance = user_balance.get(user_id, START_BALANCE)
    await message.answer(f"Ваш баланс: {balance} монет.")

@dp.message(F.text == "Реферальная система")
async def referral_system_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    conn = sqlite3.connect('casino.db')  
    cursor = conn.cursor()

    cursor.execute("SELECT referral_used FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if user_data is None:
        await message.answer("Ваш аккаунт не найден.")
        conn.close()
        return

    referral_used = user_data[0]

    if referral_used == 1:
        await message.answer(f"Ваш реферальный код: `{user_id}`. Вы уже использовали реферальный код.")
    else:
        await message.answer(f"Ваш реферальный код: `{user_id}`.\n\nВведите ID пользователя, чтобы использовать реферальный код:", parse_mode='Markdown')
        await state.set_state(ReferralStates.waiting_for_referral_id) 

    conn.close()

@dp.message(ReferralStates.waiting_for_referral_id)
async def process_referral_id(message: Message, state: FSMContext):
    user_id = message.from_user.id
    referral_id = message.text.strip()

    if not referral_id.isdigit():
        await message.answer("Пожалуйста, введите корректный ID пользователя.")
        return

    referral_id = int(referral_id)

    conn = sqlite3.connect('casino.db')  
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (referral_id,))
        referral_user = cursor.fetchone()

        if referral_user is None:
            await message.answer("Пользователь с таким ID не найден.")
            return
        cursor.execute("SELECT balance, referral_used FROM users WHERE user_id = ?", (user_id,))
        current_user = cursor.fetchone()

        if current_user is None:
            await message.answer("Ваш аккаунт не найден.")
            return

        if current_user[1] == 1:
            await message.answer("Вы уже использовали реферальный код.")
            return

        current_user_balance = current_user[0] + 200
        referral_user_balance = referral_user[0] + 300

        update_balance_in_db(user_id, current_user_balance)
        update_balance_in_db(referral_id, referral_user_balance)

        user_balance[user_id] += 200
        user_balance[referral_id] += 300

        increment_referral_count(referral_id)

        cursor.execute("SELECT referrals_count FROM users WHERE user_id = ?", (referral_id,))
        updated_referral_count = cursor.fetchone()[0]


        cursor.execute("UPDATE users SET referral_used = 1 WHERE user_id = ?", (user_id,))

        conn.commit()

        await message.answer(f"Вы успешно использовали реферальный код!\n"
                             f"Вам начислено 200 монет (Ваш новый баланс: {current_user_balance} монет).\n")


    except sqlite3.Error as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        await state.clear()  
        conn.close()


@dp.message(F.text == "Наши проекты")
async def projects_handler(message: Message):
    await message.answer("Телеграм канал с проектами: @danila_gonyshev")

@dp.message(F.text == "Играть")
async def game_selection_handler(message: Message):
    await message.answer("Выберите игру:", reply_markup=game_selection_keyboard())


@dp.message(Command('balance'))
async def check_balance(message: Message):
    user_id = message.from_user.id
    balance = user_balance.get(user_id, START_BALANCE)
    await message.answer(f"Ваш баланс: {balance} монет.")

def update_game_history(user_id, game_name, balance):
    if user_id not in game_history:
        game_history[user_id] = []
    game_history[user_id].append((game_name, balance))

    if len(game_history[user_id]) > 5:
        game_history[user_id].pop(0)


@dp.message(F.text == "🎲 Кубик")
async def cube_game_selection_handler(message: Message):
    user_id = message.from_user.id
    active_games[user_id] = "cube"
    await message.answer("Вы выбрали игру: Кубик.\n"
                         "Выберите тип ставки:", reply_markup=cube_betting_keyboard())

@dp.message(F.text.in_(["Ставка на число (6x)", "Ставка на промежутки (3x)", "Ставка больше/меньше 3"]))
async def cube_bet_type_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bet_type = message.text
    user_bets[user_id] = bet_type  
    await message.answer(f"Вы выбрали: {bet_type}.\nПожалуйста, выберите свою ставку:", reply_markup=betting_keyboard())
    await state.set_state(GameStates.waiting_for_bet)

@dp.message(F.text.in_(["10 монет", "50 монет", "100 монет","200 монет", "500 монет", "1000 монет"]))
async def bet_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bet = int(message.text.split(" ")[0])

    if user_id not in user_balance:
        user_balance[user_id] = START_BALANCE

    if user_balance[user_id] < bet:
        await message.answer(f"Недостаточно средств! Ваш баланс: {user_balance[user_id]} монет.")
        return

    game = active_games.get(user_id)

    await state.update_data(bet=bet)

    if game == "cube":
        await process_cube_bet(message, bet, state)
    elif game in ["Дартс", "Баскетбол", "Футбол", "Боулинг"]:
        await process_other_games(message, bet, game)
    elif game == "Слоты":
        await process_slots_game(message, bet)  
    else:
        await message.answer("Произошла ошибка. Попробуйте выбрать игру заново.")


@dp.message(F.text == "Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    """Обработчик для отмены текущего состояния."""
    user_id = message.from_user.id
    active_games.pop(user_id, None)
    user_bets.pop(user_id, None)
    await state.clear() 
    await message.answer("Игра отменена. Возвращаемся к выбору игры.", reply_markup=game_selection_keyboard())

@dp.message(F.text == "Главное меню")
async def home_handler(message: Message, state: FSMContext):
    """Обработчик для отмены текущего состояния."""
    user_id = message.from_user.id
    active_games.pop(user_id, None)
    user_bets.pop(user_id, None)
    await state.clear()  
    await message.answer("Главное меню.", reply_markup=home_selection_keyboard())


async def process_cube_bet(message: Message, bet: int, state: FSMContext):
    user_id = message.from_user.id
    bet_type = user_bets[user_id]

    if bet_type == "Ставка на число (6x)":
        await message.answer("Введите число от 1 до 6, на которое хотите поставить:",reply_markup=back_keyboard())
        await state.set_state(GameStates.waiting_for_number)
    elif bet_type == "Ставка на промежутки (3x)":
        await message.answer("Введите промежуток (1-2, 3-4 или 5-6):", reply_markup=cube_rate_keyboard())
        await state.set_state(GameStates.waiting_for_range)
    elif bet_type == "Ставка больше/меньше 3":
        await message.answer("Хотите поставить на больше или меньше 3? (введите 'больше' или 'меньше'):", reply_markup=cube_half_keyboard())
        await state.set_state(GameStates.waiting_for_choice)

@dp.message(GameStates.waiting_for_number)
async def number_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        user_bet_number = int(message.text)
        if user_bet_number < 1 or user_bet_number > 6:
            await message.answer("Введите число от 1 до 6.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число от 1 до 6.")
        return
    
    data = await state.get_data()
    bet = data.get("bet")

    user_balance[user_id] -= bet

    emoji = '🎲'
    data = await bot.send_dice(message.chat.id, emoji=emoji)
    result = data.dice.value

    if result == user_bet_number:
        user_balance[user_id] += bet * 6
        await message.answer(f"Вы выиграли {bet * 6} монет! Ваш новый баланс: {user_balance[user_id]} монет.", reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (число)", user_balance[user_id])
        update_balance_in_db(user_id, user_balance[user_id])  
    else:
        await message.answer(f"Вы проиграли {bet} монет. Ваш новый баланс: {user_balance[user_id]} монет.",reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (число)", user_balance[user_id])
        update_balance_in_db(user_id, user_balance[user_id])   
    await state.clear()


@dp.message(GameStates.waiting_for_range)
async def range_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_bet_range = message.text

    if user_bet_range not in ["1-2", "3-4", "5-6"]:
        await message.answer("Пожалуйста, выберите один из доступных диапазонов: 1-2, 3-4 или 5-6.")
        return

    data = await state.get_data()
    bet = data.get("bet")

    user_balance[user_id] -= bet

    emoji = '🎲'
    data = await bot.send_dice(message.chat.id, emoji=emoji)
    result = data.dice.value

    if (user_bet_range == "1-2" and result in [1, 2]) or \
       (user_bet_range == "3-4" and result in [3, 4]) or \
       (user_bet_range == "5-6" and result in [5, 6]):
        user_balance[user_id] += bet * 3
        await message.answer(f"Вы выиграли {bet * 3} монет! Ваш новый баланс: {user_balance[user_id]} монет.", reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (промежуток)", user_balance[user_id]) 
        update_balance_in_db(user_id, user_balance[user_id])
    else:
        await message.answer(f"Вы проиграли {bet} монет. Ваш новый баланс: {user_balance[user_id]} монет.", reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (промежуток)", user_balance[user_id])
        update_balance_in_db(user_id, user_balance[user_id])  
    await state.clear()  


@dp.message(GameStates.waiting_for_choice)
async def choice_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_choice = message.text.lower()
    data = await state.get_data()
    bet = data.get("bet")

    user_balance[user_id] -= bet

    emoji = '🎲'
    data = await bot.send_dice(message.chat.id, emoji=emoji)
    result = data.dice.value

    if (user_choice == "больше" and result > 3) or (user_choice == "меньше" and result < 3):
        user_balance[user_id] += bet * 2
        await message.answer(f"Вы выиграли {bet * 2} монет! Ваш новый баланс: {user_balance[user_id]} монет.",reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (больше/меньше)", user_balance[user_id])
        update_balance_in_db(user_id, user_balance[user_id]) 
    else:
        await message.answer(f"Вы проиграли {bet} монет. Ваш новый баланс: {user_balance[user_id]} монет.", reply_markup=cube_betting_keyboard())
        update_game_history(user_id, "Кубик (больше/меньше)", user_balance[user_id]) 
        update_balance_in_db(user_id, user_balance[user_id]) 
    await state.clear()


@dp.message(F.text.in_(["🎯 Дартс", "🏀 Баскетбол", "⚽ Футбол", "🎳 Боулинг", "🎰 Слоты"]))
async def other_games_handler(message: Message):
    user_id = message.from_user.id

    game = None
    if "Дартс" in message.text:
        game = "Дартс"
    elif "Баскетбол" in message.text:
        game = "Баскетбол"
    elif "Футбол" in message.text:
        game = "Футбол"
    elif "Боулинг" in message.text:
        game = "Боулинг"
    elif "Слоты" in message.text:
        game = "Слоты"

    if game:
        active_games[user_id] = game  
        await message.answer(f"Вы выбрали игру: {game.capitalize()}. Пожалуйста, выберите свою ставку.", reply_markup=betting_keyboard())

async def process_other_games(message: Message, bet: int, game: str):
    user_id = message.from_user.id

    emoji = None
    multiplier = 0 

    user_balance[user_id] -= bet

    if game == "Дартс":
        emoji = '🎯'
    elif game == "Баскетбол":
        emoji = '🏀'
    elif game == "Футбол":
        emoji = '⚽'
    elif game == "Боулинг":
        emoji = '🎳'

    if emoji:
        data = await bot.send_dice(message.chat.id, emoji=emoji)
        result = data.dice.value

        if emoji == '🎯':  # Дартс
            if result == 6:
                multiplier = 2  # Буллсай - множитель 2
            elif result > 3:
                multiplier = 1  # Хороший бросок - множитель 1
            else:
                multiplier = 0  # Промах - проигрыш

        elif emoji == '🏀':  # Баскетбол
            if result in [4, 5]:
                multiplier = 2  # Забитый мяч - множитель 2
            elif result in [1, 2, 3]:
                multiplier = 0  # Промах - проигрыш

        elif emoji == '⚽':  # Футбол
            if result in [4, 5]:
                multiplier = 2  # Гол - множитель 2
            elif result in [1, 2, 3]:
                multiplier = 0  # Промах - проигрыш

        elif emoji == '🎳':  # Боулинг
            if result == 6:
                multiplier = 2  # Все кегли сбиты - множитель 2
            elif result in [4, 5]:
                multiplier = 1  # Хороший бросок - множитель 1
            elif result == 1:
                multiplier = 0  # Промах - проигрыш


        if multiplier > 0:
            user_balance[user_id] += bet * multiplier
            await message.answer(f"Вы выиграли {bet * multiplier} монет! Ваш новый баланс: {user_balance[user_id]} монет.")
            update_game_history(user_id, game.capitalize(), user_balance[user_id]) 
            update_balance_in_db(user_id, user_balance[user_id])  
        else:
            await message.answer(f"Вы проиграли {bet} монет. Ваш новый баланс: {user_balance[user_id]} монет.")
            update_game_history(user_id, game.capitalize(), user_balance[user_id]) 
            update_balance_in_db(user_id, user_balance[user_id])

@dp.message(F.text == "🎰 Слоты")
async def slots_game_handler(message: Message):
    user_id = message.from_user.id
    active_games[user_id] = "slots"  
    await message.answer("Вы выбрали игру: Слоты. Пожалуйста, выберите свою ставку.", reply_markup=betting_keyboard())


def get_combo_text(dice_value: int):
    values = ["BAR", "виноград", "лимон", "семь"]

    dice_value -= 1
    result = []
    for _ in range(3):
        result.append(values[dice_value % 4])
        dice_value //= 4
    return result

async def process_slots_game(message: Message, bet: int):
    user_id = message.from_user.id

    user_balance[user_id] -= bet

    emoji = '🎰'
    data = await bot.send_dice(message.chat.id, emoji=emoji)
    result = data.dice.value
    combo = get_combo_text(result)

    await message.answer(f"Вам выпало: {' | '.join(combo)}")

    # Логика расчета выигрыша в зависимости от выпавшей комбинации
    if combo.count("семь") == 3:
        multiplier = 10  # Три "семь" — редкий крупный выигрыш
    elif combo.count("BAR") == 3:
        multiplier = 8  # Три "BAR" — тоже крупный, но реже
    elif combo.count("виноград") == 3:
        multiplier = 5  # Три "виноград" — средний выигрыш
    elif combo.count("лимон") == 3:
        multiplier = 2  # Три "лимон" — небольшой выигрыш
    elif combo.count("семь") == 2:
        multiplier = 2  # Две "семь" — маленький выигрыш
    elif combo.count("семь") == 1:
        multiplier = 1  # Одна "семь" — минимальный выигрыш
    else:
        multiplier = 0  # Любая другая комбинация — проигрыш

    if multiplier > 0:
        user_balance[user_id] += bet * multiplier
        await message.answer(f"Вы выиграли {bet * multiplier} монет! Ваш новый баланс: {user_balance[user_id]} монет.")
        update_game_history(user_id, "Слоты", user_balance[user_id]) 
        update_balance_in_db(user_id, user_balance[user_id])  
    else:
        await message.answer(f"Вы проиграли {bet} монет. Ваш новый баланс: {user_balance[user_id]} монет.")
        update_game_history(user_id, "Слоты", user_balance[user_id]) 
        update_balance_in_db(user_id, user_balance[user_id])  

async def main():
    create_database() 
    load_users_from_db()  
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
