import asyncio
import random
import logging
import time
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import TOKEN, CHANNEL_USERNAME, ADMIN_ID
import database as db
import keyboards as kb

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- FSM Состояния ---
class RegState(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()

class ChangeNameState(StatesGroup):
    waiting_for_new_name = State()

class CasinoState(StatesGroup):
    waiting_box_bet = State()
    waiting_dice_bet = State()
    waiting_slots_bet = State()


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def fmt(amount: int) -> str:
    return f"{amount:,}".replace(",", ".")

def get_msk_time():
    tz = pytz.timezone('Europe/Moscow')
    return datetime.now(tz)

def get_dynamic_greeting(nickname: str, balance: int) -> str:
    hour = get_msk_time().hour
    b_str = fmt(balance)
    
    if 0 <= hour < 6:
        phrases = [
            f"Салют, {nickname}! Почему ещё не спишь? Ты щас в столице — Москве! На твоём балике: {b_str}₽",
            f"Ночь на дворе, {nickname}... А ты всё суетишь. На данный момент ты в Москве. У тебя на балансе: {b_str}₽",
            f"Йо, {nickname}! Тёмное время для тёмных дел. Ты в Москве! На твоём счету: {b_str}₽"
        ]
    elif 6 <= hour < 12:
        phrases = [
            f"Утро доброе, {nickname}! Чего не спится? Ты щас в Москве. На твоём счету: {b_str}₽",
            f"Сап, {nickname}! Город только просыпается, а ты уже на ногах. Ты в столице — Москве! На твоём балике: {b_str}₽",
            f"Приветствую, {nickname}! Встречаешь рассвет над Москвой? На данный момент на твоём балансе: {b_str}₽"
        ]
    elif 12 <= hour < 18:
        phrases = [
            f"Здорово, {nickname}! Как суета? На данный момент ты в Москве. У тебя на балансе: {b_str}₽",
            f"Добрый день, {nickname}! Москва кипит, бабки крутятся. Ты в столице! На твоём счету: {b_str}₽",
            f"Хай, {nickname}! Готов к новым делам? Ты сейчас в Москве. У тя щас: {b_str}₽"
        ]
    else:
        phrases = [
            f"Добрый вечер, {nickname}! Город погружается во тьму. Ты в Москве. На твоём балике: {b_str}₽",
            f"Салют, {nickname}! Вечерняя Москва красива, но опасна. На данный момент ты в Москве. У тебя на балансе: {b_str}₽",
            f"Привет, {nickname}! Время подводить итоги дня. Ты в столице — Москве! На твоём счету: {b_str}₽"
        ]
    return random.choice(phrases)


# ================= СТАРТ И РЕГИСТРАЦИЯ =================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user(message.from_user.id)
    
    if user:
        db.process_fines_logic(message.from_user.id)
        user = db.get_user(message.from_user.id)
        text = get_dynamic_greeting(user[1], user[3])
        await message.answer(text, reply_markup=kb.get_main_menu_kb())
    else:
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != message.from_user.id:
                await state.update_data(referrer_id=ref_id)

        start_text = (
            "👋 Приветствуем тебя в «Бот Гангстер»!\n\n"
            "Здесь тебе предстоит пройти путь от обычного уличного бродяги до криминального босса Москвы: "
            "ты будешь устраиваться на работу, покупать бизнесы и обходить авторитетов стороной на старте.\n\n"
            "Перед тем как начать, выбери, как ты хочешь зарегистрироваться:\n\n"
            "1. Пройти сюжетный пролог (~3 минуты): Погружение в историю + бонус 100.000₽ от наставника!\n"
            "2. Быстрая регистрация: Просто укажи информацию и сразу переходи к игре (без бонуса)."
        )
        await message.answer(start_text, reply_markup=kb.get_start_kb())


@dp.callback_query(F.data == "reg_fast")
async def reg_fast_confirm(call: CallbackQuery):
    text = (
        "⚠️ Ты уверен, что хочешь выбрать быструю регистрацию?\n\n"
        "Потратив всего 3 минуты на сюжетный пролог, ты получишь 100.000₽ стартового капитала от наставника! "
        "При быстрой регистрации твоя игра начнется с 0₽ в кармане."
    )
    await call.message.edit_text(text, reply_markup=kb.get_fast_confirm_kb())


@dp.callback_query(F.data.in_(["reg_story", "reg_fast_start"]))
async def start_reg_process(call: CallbackQuery, state: FSMContext):
    reg_type = 'story' if call.data == "reg_story" else 'fast'
    await state.update_data(reg_type=reg_type)
    
    if reg_type == 'story':
        await call.message.edit_text("загружаем сюжетный пролог...")
        await asyncio.sleep(5)
        
        prologue_1 = (
            "Окраина Москвы. Лето. 23:45. Моросит мелкий неприятный дождь. Ты стоишь под козырьком заброшенного магазина, "
            "поджав губы от холода. В кармане джинсов — дыра и ровно 12 рублей сдачи от сигарет.\n\n"
            "Из темноты переулка медленно выезжает чёрный Мерседес. Стекло пассажирской двери плавно опускается.\n\n"
            "— Эй, пацан, — глухо произносит Седой. — Ты чего тут замерзаешь? Как тебя величать-то?\n\n"
            "(Введи имя своего персонажа, от 2 до 20 букв):"
        )
        await call.message.answer(prologue_1)
    else:
        await call.message.answer("Введи имя своего персонажа (от 2 до 20 букв):")
        
    await state.set_state(RegState.waiting_for_name)


@dp.message(RegState.waiting_for_name)
async def process_reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    clean_name = "".join([c for c in name if c.isalpha()])
    
    if len(name) < 2 or len(name) > 20 or len(clean_name) == 0:
        await message.answer("Некорректное имя! Только буквы от 2 до 20 символов. Попробуй еще раз:")
        return

    if db.is_nickname_taken(name):
        await message.answer("Этот никнейм уже занят на улицах Москвы! Придумай другой:")
        return

    await state.update_data(nickname=name)
    data = await state.get_data()
    reg_type = data.get('reg_type')

    if reg_type == 'story':
        text = (
            f"— Меня зовут {name}, — ответил ты.\n\n"
            f"— Ну, здорово, {name}. А я Виктор. Для своих — Седой. Сколько тебе лет-то вообще?\n\n"
            "(Введи возраст персонажа от 18 до 35 лет):"
        )
        await message.answer(text)
    else:
        await message.answer(f"Отлично, {name}! Теперь введи возраст персонажа (число от 18 до 35):")
        
    await state.set_state(RegState.waiting_for_age)


@dp.message(RegState.waiting_for_age)
async def process_reg_age(message: Message, state: FSMContext):
    age_str = message.text.strip()
    
    if not age_str.isdigit() or not (18 <= int(age_str) <= 35):
        await message.answer("Некорректный возраст! Введи число от 18 до 35 лет:")
        return

    age = int(age_str)
    data = await state.get_data()
    nickname = data['nickname']
    reg_type = data['reg_type']
    referrer_id = data.get('referrer_id')

    db.register_user(message.from_user.id, nickname, age, reg_type, referrer_id)
    await state.clear()

    if reg_type == 'story':
        text = (
            f"— Мне {age}, — сказал ты.\n\n"
            "Седой достал из бардачка пухлый кожаный конверт и бросил тебе на колени."
        )
        await message.answer(text, reply_markup=kb.get_prologue_envelope_kb())
    else:
        await message.answer("Регистрация завершена! Поздравляю! 🥳")
        await message.answer("Загружаем меню...")
        await asyncio.sleep(5)
        
        user = db.get_user(message.from_user.id)
        greet = get_dynamic_greeting(user[1], user[3])
        await message.answer(greet, reply_markup=kb.get_main_menu_kb())


@dp.callback_query(F.data == "prologue_open_envelope")
async def process_envelope(call: CallbackQuery):
    text = (
        "Ты расстёгиваешь конверт. Внутри — 100.000₽ и визитка Седого.\n\n"
        "— Тут 100.000₽, — говорит Седой. — Это тебе подъемные. Добро пожаловать в игру!\n\n"
        "###\nПролог пройден, вам начислено 100.000₽."
    )
    await call.message.edit_text(text)
    await call.message.answer("Загружаем меню...")
    await asyncio.sleep(5)
    
    user = db.get_user(call.from_user.id)
    greet = get_dynamic_greeting(user[1], user[3])
    await call.message.answer(greet, reply_markup=kb.get_main_menu_kb())


# ================= ГЛАВНОЕ МЕНЮ И НАВИГАЦИЯ =================

@dp.callback_query(F.data == "to_main_menu")
async def back_to_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    db.process_fines_logic(call.from_user.id)
    user = db.get_user(call.from_user.id)
    greet = get_dynamic_greeting(user[1], user[3])
    await call.message.edit_text(greet, reply_markup=kb.get_main_menu_kb())

@dp.callback_query(F.data == "menu_profile")
async def show_profile(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    
    text = (
        f"🏙 Профиль гангстера: {user[1]}\n"
        f"_________________________\n"
        f"👤 Возраст: {user[2]} лет\n"
        f"🏙 Город: Москва\n"
        f"💵 Баланс: {fmt(user[3])}₽\n"
        f"👑 Репутация: {fmt(user[4])} авторитета\n"
    )
    await call.message.edit_text(text, reply_markup=kb.get_back_to_menu_kb())


# ================= НАСТРОЙКИ =================

@dp.callback_query(F.data == "menu_settings")
async def show_settings(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    await call.message.edit_text(f"{user[1]}, ты попал в настройки.", reply_markup=kb.get_settings_kb())

@dp.callback_query(F.data == "sett_character")
async def show_character(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    text = (
        f"👤 Характеристики персонажа:\n\n"
        f"Имя: {user[1]}\n"
        f"Возраст: {user[2]} лет (изменить нельзя)\n"
        f"Пол: Мужской (изменить нельзя — криминальные улицы Москвы ошибок не прощают)"
    )
    await call.message.edit_text(text, reply_markup=kb.get_character_kb())

@dp.callback_query(F.data == "change_name")
async def start_change_name(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введи новое имя своего персонажа (от 2 до 20 букв):")
    await state.set_state(ChangeNameState.waiting_for_new_name)

@dp.message(ChangeNameState.waiting_for_new_name)
async def process_new_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 20 or not name.isalpha():
        await message.answer("Некорректное имя! Только буквы от 2 до 20 символов:")
        return
    if db.is_nickname_taken(name):
        await message.answer("Этот никнейм уже занят! Придумай другой:")
        return

    db.update_nickname(message.from_user.id, name)
    await state.clear()
    await message.answer(f"Имя успешно изменено на {name}!", reply_markup=kb.get_settings_kb())

@dp.callback_query(F.data == "sett_commands")
async def show_commands(call: CallbackQuery):
    text = (
        "📜 **Быстрые команды бота:**\n\n"
        "⚡️ `/profile` или `/p` — Твой профиль\n"
        "💵 `/balance` или `/b` — Быстрый баланс\n"
        "🏆 `/top` — ТОП-10 богачей и авторитетов\n"
        "⚠️ `/fines` — Неоплаченные штрафы\n"
        "🤝 `/ref` — Реферальная ссылка\n\n"
        "💸 **Перевод денег:** `/pay Никнейм Сумма`"
    )
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "sett_info")
async def show_info(call: CallbackQuery):
    text = "ℹ️ О боте «Бот Гангстер»:\n\nКриминальная текстовая RPG в сердце ночной Москвы. Пройди путь от бродяги до миллиардера!"
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb())

@dp.callback_query(F.data == "sett_help")
async def show_help(call: CallbackQuery):
    text = "🛠 Помощь и техподдержка:\n\nПо всем вопросам пишите админу: @ice_speex"
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb())


# ================= РАБОТЫ (ЛЕГАЛ И НЕЛЕГАЛ) =================

@dp.callback_query(F.data == "menu_jobs")
async def show_jobs_category(call: CallbackQuery):
    await call.message.edit_text("Выбери категорию занятости:", reply_markup=kb.get_jobs_category_kb())

@dp.callback_query(F.data == "jobs_legal")
async def show_legal_jobs(call: CallbackQuery):
    await call.message.edit_text("🟢 Легальные работы", reply_markup=kb.get_legal_jobs_kb())

@dp.callback_query(F.data == "jobs_illegal")
async def show_illegal_jobs(call: CallbackQuery):
    await call.message.edit_text("🔴 Нелегальные работы", reply_markup=kb.get_illegal_jobs_kb())

# --- Легальные ---
@dp.callback_query(F.data == "work_loader")
async def do_loader(call: CallbackQuery):
    await call.message.edit_text("📦 Ты взял коробку и тащишь её на склад...")
    await asyncio.sleep(6)
    earn = random.randint(300, 800)
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    await call.message.answer(f"📦 Разгрузил фуру и получил {fmt(earn)}₽!\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_legal_jobs_kb())

@dp.callback_query(F.data == "work_courier")
async def do_courier(call: CallbackQuery):
    delay = random.randint(7, 10)
    await call.message.edit_text(f"🚴 Мчишь на велосипеде с заказом...")
    await asyncio.sleep(delay)
    earn = int(delay * random.randint(150, 250))
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    await call.message.answer(f"🍕 Заказ доставлен! Заработок: {fmt(earn)}₽.\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_legal_jobs_kb())

@dp.callback_query(F.data == "work_taxi")
async def do_taxi(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if not user[14]:
        if user[3] < 20000:
            await call.answer("❌ Нужно 20.000₽ для покупки лицензии таксиста!", show_alert=True)
            return
        db.update_balance(call.from_user.id, -20000)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET taxi_license = 1 WHERE user_id = ?', (call.from_user.id,))
        conn.commit()
        conn.close()
        await call.answer("🎉 Лицензия таксиста куплена за 20.000₽!", show_alert=True)

    delay = random.randint(7, 12)
    await call.message.edit_text(f"🚖 Везёшь пассажира...")
    await asyncio.sleep(delay)
    earn = int(delay * random.randint(250, 400))
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    await call.message.answer(f"🏁 Пассажир расплатился: {fmt(earn)}₽.\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_legal_jobs_kb())

# --- Нелегальные ---
@dp.callback_query(F.data == "work_pickpocket")
async def do_pickpocket(call: CallbackQuery):
    await call.message.edit_text("🤏 Трёшься в метро, высматриваешь кошельки...")
    await asyncio.sleep(5)
    
    if random.randint(1, 100) <= 15: # 15% риск
        fine = 5000
        db.add_fine(call.from_user.id, fine)
        await call.message.answer(f"🚨 Тебя за руку схватил ППС! Выписан штраф {fmt(fine)}₽! Оплати его в меню штрафов.", reply_markup=kb.get_illegal_jobs_kb())
    else:
        earn = random.randint(800, 3500)
        db.update_balance(call.from_user.id, earn)
        db.update_reputation(call.from_user.id, 2)
        user = db.get_user(call.from_user.id)
        await call.message.answer(f"💰 Вытащил бумажник! Улов: {fmt(earn)}₽ (+2 авторитета).\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_illegal_jobs_kb())

@dp.callback_query(F.data == "work_dealer")
async def do_dealer(call: CallbackQuery):
    await call.message.edit_text("📦 Прячешь «магнит» в тихом районе...")
    await asyncio.sleep(10)
    
    if random.randint(1, 100) <= 25: # 25% риск
        fine = 15000
        db.add_fine(call.from_user.id, fine)
        await call.message.answer(f"🚨 Накрыл ОМОН! Удалось убежать, но завели дело. Штраф: {fmt(fine)}₽!", reply_markup=kb.get_illegal_jobs_kb())
    else:
        earn = random.randint(6000, 14000)
        db.update_balance(call.from_user.id, earn)
        db.update_reputation(call.from_user.id, 5)
        user = db.get_user(call.from_user.id)
        await call.message.answer(f"📦 Закладка сделана! Куратор перевёл: {fmt(earn)}₽ (+5 авторитета).\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_illegal_jobs_kb())

@dp.callback_query(F.data == "work_collector")
async def do_collector(call: CallbackQuery):
    await call.message.edit_text("🔨 Выбиваешь долги у просрочившего должника...")
    await asyncio.sleep(12)
    
    if random.randint(1, 100) <= 20: # 20% риск
        fine = 30000
        db.add_fine(call.from_user.id, fine)
        await call.message.answer(f"🚨 Должник вызвал Ментов! Штраф за хулиганство: {fmt(30000)}₽!", reply_markup=kb.get_illegal_jobs_kb())
    else:
        earn = random.randint(18000, 40000)
        db.update_balance(call.from_user.id, earn)
        db.update_reputation(call.from_user.id, 15)
        user = db.get_user(call.from_user.id)
        await call.message.answer(f"🔨 Долг выбит! Твой процент: {fmt(earn)}₽ (+15 авторитета).\nБаланс: {fmt(user[3])}₽", reply_markup=kb.get_illegal_jobs_kb())


# ================= БИЗНЕСЫ =================

BIZ_DATA = {
    1: {"name": "🏪 Ларек с шаурмой", "price": 100000, "raw_price": 20000, "income": 70000},
    2: {"name": "🍔 Точка фаст-фуда", "price": 500000, "raw_price": 80000, "income": 300000},
    3: {"name": "🧼 Автомойка", "price": 3500000, "raw_price": 500000, "income": 2000000},
    4: {"name": "🥊 Подпольный клуб", "price": 10000000, "raw_price": 1500000, "income": 6500000},
    5: {"name": "🍽 Ресторан", "price": 30000000, "raw_price": 4000000, "income": 18000000},
    6: {"name": "🎰 Теневое казино", "price": 80000000, "raw_price": 10000000, "income": 50000000},
    7: {"name": "🏦 Коммерческий банк", "price": 250000000, "raw_price": 30000000, "income": 160000000},
    8: {"name": "✈️ Авиакомпания", "price": 750000000, "raw_price": 100000000, "income": 500000000},
    9: {"name": "🛢 Нефтегазовая компания", "price": 2500000000, "raw_price": 350000000, "income": 1700000000}
}

@dp.callback_query(F.data == "menu_business")
async def show_business(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    biz_id = user[12]
    
    if not biz_id:
        await call.message.edit_text("🏢 У тебя пока нет бизнеса. Выбери бизнес из каталога для покупки:", reply_markup=kb.get_business_catalog_kb())
        return

    biz = BIZ_DATA[biz_id]
    bought_time = user[13]
    now = int(time.time())
    
    # Сырье перерабатывается 48 часов (172800 сек)
    if bought_time == 0:
        status_text = "⚠️ Закупка сырья НЕ произведена!"
        btn_text = f"📦 Закупить сырье ({fmt(biz['raw_price'])}₽)"
        cb_data = "biz_buy_raw"
    elif now - bought_time < 172800:
        left = 172800 - (now - bought_time)
        hrs = int(left // 3600)
        mins = int((left % 3600) // 60)
        status_text = f"⚙️ Сырье перерабатывается. Прибыль будет через: {hrs}ч {mins}мин"
        btn_text = "⏳ Ждем переработку..."
        cb_data = "biz_wait"
    else:
        status_text = "✅ Прибыль готова к снятию!"
        btn_text = f"💰 Снять прибыль ({fmt(biz['income'])}₽)"
        cb_data = "biz_collect"

    text = (
        f"🏢 Твой бизнес: {biz['name']}\n"
        f"_________________________\n"
        f"💵 Чистая прибыль за цикл: {fmt(biz['income'])}₽\n"
        f"📦 Стоимость сырья на 48ч: {fmt(biz['raw_price'])}₽\n\n"
        f"Статус: {status_text}"
    )
    
    kb_biz = kb.InlineKeyboardMarkup(inline_keyboard=[
        [kb.InlineKeyboardButton(text=btn_text, callback_data=cb_data)],
        [kb.InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb_biz)

@dp.callback_query(F.data.startswith("buy_biz_"))
async def process_buy_biz(call: CallbackQuery):
    b_id = int(call.data.split("_")[2])
    biz = BIZ_DATA[b_id]
    user = db.get_user(call.from_user.id)

    if user[12]:
        await call.answer("❌ У тебя уже есть один бизнес! Нельзя владеть несколькими ИП.", show_alert=True)
        return

    if user[3] < biz["price"]:
        await call.answer(f"❌ Недостаточно денег! Нужно: {fmt(biz['price'])}₽", show_alert=True)
        return

    db.update_balance(call.from_user.id, -biz["price"])
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET business_id = ? WHERE user_id = ?', (b_id, call.from_user.id))
    conn.commit()
    conn.close()

    await call.answer(f"🎉 Поздравляем с покупкой бизнeса «{biz['name']}»!", show_alert=True)
    await show_business(call)

@dp.callback_query(F.data == "biz_buy_raw")
async def biz_buy_raw(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    biz = BIZ_DATA[user[12]]

    if user[3] < biz["raw_price"]:
        await call.answer(f"❌ Недостаточно денег на закупку сырья! Нужно: {fmt(biz['raw_price'])}₽", show_alert=True)
        return

    db.update_balance(call.from_user.id, -biz["raw_price"])
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET biz_raw_bought_time = ? WHERE user_id = ?', (int(time.time()), call.from_user.id))
    conn.commit()
    conn.close()

    await call.answer("📦 Сырье закуплено! Зайди через 48 часов за прибылью.", show_alert=True)
    await show_business(call)

@dp.callback_query(F.data == "biz_collect")
async def biz_collect(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    biz = BIZ_DATA[user[12]]

    db.update_balance(call.from_user.id, biz["income"])
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET biz_raw_bought_time = 0 WHERE user_id = ?', (call.from_user.id,))
    conn.commit()
    conn.close()

    await call.answer(f"💰 Вы успешно сняли {fmt(biz['income'])}₽ прибыли!", show_alert=True)
    await show_business(call)


# ================= НЕДВИЖИМОСТЬ =================

HOUSE_DATA = {
    1: {"name": "🏚 Комната на окраине", "price": 2500000},
    2: {"name": "🏠 Однушка на окраине", "price": 9000000},
    3: {"name": "🏙 Двушка в 6км от центра", "price": 22000000},
    4: {"name": "🏡 1-эт. дом в частном секторе", "price": 35000000},
    5: {"name": "🏢 Трёшка в 3км от центра", "price": 65000000},
    6: {"name": "🏰 2-эт. дом в частном секторе", "price": 80000000},
    7: {"name": "🏊‍♂️ 3-эт. дом с бассейном", "price": 250000000},
    8: {"name": "🏙 5-комн. квартира в Moscow City", "price": 550000000},
    9: {"name": "👑 Дворец на Рублёвке", "price": 1500000000},
    10: {"name": "🏝 Резиденция на частном острове", "price": 5000000000}
}

@dp.callback_query(F.data == "menu_houses")
async def show_houses(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    house_id = user[11]

    if house_id:
        h = HOUSE_DATA[house_id]
        text = f"🏠 Твоя текущая недвижимость:\n\nОбъект: {h['name']}\nСтоимость: {fmt(h['price'])}₽"
        await call.message.edit_text(text, reply_markup=kb.get_back_to_menu_kb())
    else:
        await call.message.edit_text("🏠 Каталог недвижимости Москвы:", reply_markup=kb.get_house_catalog_kb())

@dp.callback_query(F.data.startswith("buy_house_"))
async def process_buy_house(call: CallbackQuery):
    h_id = int(call.data.split("_")[2])
    house = HOUSE_DATA[h_id]
    user = db.get_user(call.from_user.id)

    if user[3] < house["price"]:
        await call.answer(f"❌ Недостаточно денег! Нужно: {fmt(house['price'])}₽", show_alert=True)
        return

    db.update_balance(call.from_user.id, -house["price"])
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET house_id = ? WHERE user_id = ?', (h_id, call.from_user.id))
    conn.commit()
    conn.close()

    await call.answer(f"🎉 Поздравляем с покупкой элитного жилья: {house['name']}!", show_alert=True)
    await show_houses(call)


#================= КАЗИНО =================

@dp.callback_query(F.data == "menu_casino")
async def show_casino(call: CallbackQuery):
    await call.message.edit_text("🎰 Подпольное казино Москвы. Сделай свою ставку:", reply_markup=kb.get_casino_kb())

# --- Слоты ---
@dp.callback_query(F.data == "cas_slots")
async def slots_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🎰 Введи сумму ставки на слоты (число):")
    await state.set_state(CasinoState.waiting_slots_bet)

@dp.message(CasinoState.waiting_slots_bet)
async def process_slots_bet(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("⚠️ Введи корректную сумму числом!")
        return
    bet = int(message.text)
    user = db.get_user(message.from_user.id)
    
    if user[3] < bet:
        await message.answer(f"❌ Недостаточно денег! Твой баланс: {fmt(user[3])}₽")
        return

    db.update_balance(message.from_user.id, -bet)
    msg = await message.answer_dice(emoji="🎰")
    val = msg.dice.value
    await state.clear()
    await asyncio.sleep(2.5)

    if val == 64: # 777
        win = bet * 5
        db.update_balance(message.from_user.id, win)
        await message.answer(f"🎉 ДЖЕКПОТ! 777! Вы выиграли {fmt(win)}₽!")
    elif val in [1, 22, 43]: # Три одинаковых
        win = bet * 2
        db.update_balance(message.from_user.id, win)
        await message.answer(f"🎰 Три в ряд! Вы выиграли {fmt(win)}₽!")
    else:
        await message.answer("❌ Не повезло! Ставка сгорела.")

# --- Кости ---
@dp.callback_query(F.data == "cas_dice")
async def dice_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🎲 Введи сумму ставки на кости (Шанс 16% | Выигрыш x5):")
    await state.set_state(CasinoState.waiting_dice_bet)

@dp.message(CasinoState.waiting_dice_bet)
async def process_dice_bet(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("⚠️ Введи корректную сумму числом!")
        return
    bet = int(message.text)
    user = db.get_user(message.from_user.id)
    
    if user[3] < bet:
        await message.answer(f"❌ Недостаточно денег! Твой баланс: {fmt(user[3])}₽")
        return

    db.update_balance(message.from_user.id, -bet)
    msg = await message.answer_dice(emoji="🎲")
    val = msg.dice.value
    await state.clear()
    await asyncio.sleep(2.5)

    if val == 6: # Выпала шестерка (16% шанс)
        win = bet * 5
        db.update_balance(message.from_user.id, win)
        await message.answer(f"🎲 ВЫПАЛА 6! Победа! Вы выиграли {fmt(win)}₽!")
    else:
        await message.answer(f"🎲 Выпало {val}. Вы проиграли {fmt(bet)}₽!")

# --- Бокс ---
@dp.callback_query(F.data == "cas_box")
async def box_start(call: CallbackQuery):
    await call.message.edit_text("🥊 Выбери бойца:", reply_markup=kb.get_box_choice_kb())

@dp.callback_query(F.data.in_(["box_fav", "box_underdog"]))
async def box_bet_choice(call: CallbackQuery, state: FSMContext):
    choice = "fav" if call.data == "box_fav" else "underdog"
    await state.update_data(box_choice=choice)
    await call.message.edit_text("🥊 Введи сумму ставки на бой (число):")
    await state.set_state(CasinoState.waiting_box_bet)

@dp.message(CasinoState.waiting_box_bet)
async def process_box_bet(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("⚠️ Введи сумму числом!")
        return
    bet = int(message.text)
    data = await state.get_data()
    choice = data['box_choice']
    user = db.get_user(message.from_user.id)

    if user[3] < bet:
        await message.answer(f"❌ Недостаточно денег! Баланс: {fmt(user[3])}₽")
        return

    db.update_balance(message.from_user.id, -bet)
    await message.answer("🥊 Бой начался! Идёт 3-й раунд...")
    await asyncio.sleep(4)
    await state.clear()

    rnd = random.randint(1, 100)
    if choice == "fav":
        if rnd <= 65: # 65% шанс
            win = int(bet * 1.5)
            db.update_balance(message.from_user.id, win)
            await message.answer(f"🎉 Проверенный боец победил нокаутом! Вы выиграли {fmt(win)}₽!")
        else:
            await message.answer("❌ Фаворит неожиданно упал в нокаут! Ставка сгорела.")
    else:
        if rnd <= 35: # 35% шанс
            win = int(bet * 2.5)
            db.update_balance(message.from_user.id, win)
            await message.answer(f"🎉 ТЁМНАЯ ЛОШАДКА ВЫРВАЛА ПОБЕДУ! Вы выиграли {fmt(win)}₽!")
        else:
            await message.answer("❌ Тёмная лошадка проиграла бой. Ставка сгорела.")


# ================= ШТРАФЫ =================

# ================= ШТРАФЫ =================

@dp.callback_query(F.data == "menu_fines")
async def show_fines(call: CallbackQuery):
    db.process_fines_logic(call.from_user.id)
    fines = db.get_active_fines(call.from_user.id)
    
    if not fines:
        await call.message.edit_text(
            "✅ У тебя нет активных штрафов! Ты чист перед законами улиц.", 
            reply_markup=kb.get_back_to_menu_kb()
        )
        return

    text = "⚠️ Ваши неоплаченные штрафы:\n\n"
    now = int(time.time())
    inline_kb = []
    
    for f in fines:
        fine_id, amount, issued_time, stage = f
        left = 172800 - (now - issued_time)
        hrs = max(0, int(left // 3600))
        mins = max(0, int((left % 3600) // 60))
        
        st_text = "Обычный (48ч)" if stage == 1 else "ПЕНЯ +50% (48ч)"
        text += f"🆔 #{fine_id} | Сумма: {fmt(amount)}₽ | Статус: {st_text} | Осталось: {hrs}ч {mins}мин\n"
        inline_kb.append([kb.InlineKeyboardButton(text=f"💳 Оплатить #{fine_id} ({fmt(amount)}₽)", callback_data=f"pay_fine_{fine_id}")])

    inline_kb.append([kb.InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")])
    await call.message.edit_text(text, reply_markup=kb.InlineKeyboardMarkup(inline_keyboard=inline_kb))

@dp.callback_query(F.data == "to_main_menu")
async def back_to_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    db.process_fines_logic(call.from_user.id)
    user = db.get_user(call.from_user.id)
    greet = get_dynamic_greeting(user[1], user[3])
    try:
        await call.message.edit_text(greet, reply_markup=kb.get_main_menu_kb())
    except Exception:
        await call.message.answer(greet, reply_markup=kb.get_main_menu_kb())

# ================= ЕЖЕДНЕВНЫЙ БОНУС И ТОП =================

@dp.callback_query(F.data == "menu_daily")
async def claim_daily(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    last_claim = user[10]
    streak = user[9]
    now = int(time.time())
    
    if now - last_claim < 86400:
        left = 86400 - (now - last_claim)
        hrs = int(left // 3600)
        mins = int((left % 3600) // 60)
        await call.answer(f"⏳ Следующий бонус можно забрать через {hrs}ч {mins}мин!", show_alert=True)
        return

    if now - last_claim > 172800: streak = 0
    streak = (streak % 7) + 1
    reward = streak * 2000
    
    db.update_balance(call.from_user.id, reward)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET daily_streak = ?, last_daily_claim = ? WHERE user_id = ?', (streak, now, call.from_user.id))
    conn.commit()
    conn.close()

    await call.answer(f"🎁 День {streak}/7! Вы получили {fmt(reward)}₽!", show_alert=True)
    await back_to_main_menu(call, None)

@dp.callback_query(F.data == "menu_top")
async def show_top(call: CallbackQuery):
    top_m = db.get_top_money()
    top_r = db.get_top_reputation()

    text = "🏆 ТОП-10 БОГАЧЕЙ МОСКВЫ:\n"
    for i, u in enumerate(top_m, 1): text += f"{i}. {u[0]} — {fmt(u[1])}₽\n"
    text += "\n👑 ТОП-10 АВТОРИТЕТОВ УЛИЦ:\n"
    for i, u in enumerate(top_r, 1): text += f"{i}. {u[0]} — {fmt(u[1])} авторитета\n"

    await call.message.edit_text(text, reply_markup=kb.get_back_to_menu_kb())


# ================= РЕФЕРАЛКА И КАНАЛ =================

@dp.callback_query(F.data == "menu_ref")
async def show_ref(call: CallbackQuery):
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    
    text = (
        "🤝 Реферальная система:\n\n"
        f"Твоя ссылка: `{link}`\n\n"
        "🎁 Бонусы:\n"
        "• За подписку на канал: 200.000₽\n"
        "• Когда твой реферал заработает 1.000.000₽, ты получишь 3.000.000₽!"
    )
    
    kb_ref = kb.InlineKeyboardMarkup(inline_keyboard=[
        [kb.InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [kb.InlineKeyboardButton(text="🎁 Проверить подписку (+200.000₽)", callback_data="check_channel_sub")],
        [kb.InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb_ref, parse_mode="Markdown")

@dp.callback_query(F.data == "check_channel_sub")
async def check_sub(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if user[8]:
        await call.answer("❌ Ты уже забирал бонус за подписку!", show_alert=True)
        return

    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=call.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            db.update_balance(call.from_user.id, 200000)
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET channel_bonus_claimed = 1 WHERE user_id = ?', (call.from_user.id,))
            conn.commit()
            conn.close()
            await call.answer("🎉 Подписка подтверждена! Вам начислено 200.000₽!", show_alert=True)
        else:
            await call.answer("❌ Ты ещё не подписался на канал!", show_alert=True)
    except Exception:
        await call.answer("Ошибка проверки подписки.", show_alert=True)


# ================= БЫСТРЫЕ ТЕКСТОВЫЕ КОМАНДЫ =================

@dp.message(Command("profile", "p"))
async def cmd_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user: return
    text = f"🏙 Профиль: {user[1]}\n💵 Баланс: {fmt(user[3])}₽\n👑 Репутация: {fmt(user[4])} авторитета"
    await message.answer(text, reply_markup=kb.get_back_to_menu_kb())

@dp.message(Command("balance", "b"))
async def cmd_balance(message: Message):
    user = db.get_user(message.from_user.id)
    if not user: return
    await message.answer(f"💵 Баланс: {fmt(user[3])}₽")

@dp.message(Command("fines"))
async def cmd_fines(message: Message):
    fines = db.get_active_fines(message.from_user.id)
    if not fines:
        await message.answer("✅ У вас нет неоплаченных штрафов!")
        return
    text = "⚠️ Ваши неоплаченные штрафы:\n"
    for f in fines: text += f"🆔 #{f[0]} | Сумма: {fmt(f[1])}₽\n"
    await message.answer(text)

@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        await message.answer("⚠️ Использование: `/pay Никнейм 50000`", parse_mode="Markdown")
        return

    target_nick, amount, sender = args[1], int(args[2]), db.get_user(message.from_user.id)
    if amount <= 0 or sender[3] < amount:
        await message.answer("❌ Недостаточно денег на балансе!")
        return

    receiver = db.get_user_by_nickname(target_nick)
    if not receiver or receiver[0] == message.from_user.id:
        await message.answer("❌ Некорректный получатель!")
        return

    tax = int(amount * 0.05)
    db.transfer_money(message.from_user.id, receiver[0], amount)
    db.update_balance(receiver[0], -tax)
    await message.answer(f"💸 Перевод {fmt(amount)}₽ игроку {receiver[1]} выполнен! (Комиссия 5%: {fmt(tax)}₽)")

@dp.message(Command("adm_add_cash_99"))
async def admin_give_money(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit(): return
    amount = int(args[1])
    db.update_balance(message.from_user.id, amount)
    user = db.get_user(message.from_user.id)
    await message.answer(f"👑 **АДМИН-ПАНЕЛЬ**: Начислено +{fmt(amount)}₽!\nБаланс: {fmt(user[3])}₽", parse_mode="Markdown")

# ================= МУР И ПРОДАЖНЫЙ КОП =================

POLICE_RANKS = [
    "Рядовой", "Мл. сержант", "Сержант", "Ст. сержант", "Старшина", "Прапорщик",
    "Ст. прапорщик", "Мл. лейтенант", "Лейтенант", "Ст. лейтенант", "Капитан", "Майор", "Подполковник", "Полковник"
]

@dp.callback_query(F.data == "menu_police")
async def show_police(call: CallbackQuery):
    pol = db.get_police_profile(call.from_user.id)
    
    if not pol:
        text = (
            "👮‍♂️ **Московский Уголовный Розыск (МУР)**\n\n"
            "Хочешь крышевать улицы, брать взятки с задерживаемых и крутить схемы? "
            "Вступи в МУР! Покупка формы и корочки стоит **100.000₽**."
        )
        await call.message.edit_text(text, reply_markup=kb.get_police_kb(False), parse_mode="Markdown")
    else:
        rank_name = POLICE_RANKS[pol[1] - 1]
        salary = pol[1] * 15000
        text = (
            f"👮‍♂️ **Твоё досье в МУР:**\n\n"
            f"⭐ Звание: **{rank_name}** ({pol[1]}/14)\n"
            f"💵 Официальный оклад: **{fmt(salary)}₽**\n"
            f"⚠️ Выговоры от УСБ: **{pol[2]}/3** (при 3/3 — увольнение)\n"
            f"📈 Раскрыто дел: **{pol[3]}**\n"
            f"⏳ Последняя смена: {datetime.fromtimestamp(pol[4]).strftime('%H:%M') if pol[4] else 'Не был'}"
        )
        await call.message.edit_text(text, reply_markup=kb.get_police_kb(True), parse_mode="Markdown")

@dp.callback_query(F.data == "pol_join")
async def pol_join(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if user[3] < 100000:
        await call.answer("❌ Нужно 100.000₽ для взноса в отдел!", show_alert=True)
        return
    
    db.update_balance(call.from_user.id, -100000)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO police (user_id, rank, reprimands, solved_cases) VALUES (?, 1, 0, 0)', (call.from_user.id,))
    conn.commit()
    conn.close()

    await call.answer("🎉 Поздравляем! Ты принят в МУР в звании Рядовой!", show_alert=True)
    await show_police(call)

@dp.callback_query(F.data == "pol_work")
async def pol_work(call: CallbackQuery):
    pol = db.get_police_profile(call.from_user.id)
    now = int(time.time())
    
    # Кулдаун 10 минут
    if now - pol[4] < 600:
        left = 600 - (now - pol[4])
        await call.answer(f"⏳ Следующий патруль через {int(left//60)} мин {int(left%60)} сек!", show_alert=True)
        return

    await call.message.edit_text("🚔 Ты выехал на патрулирование Петровки... Задержан мажор на Гелике без номеров!")
    await asyncio.sleep(4)
    
    bribe_sum = pol[1] * random.randint(25000, 60000)
    text = (
        f"🚘 **Задержан нарушитель!**\n\n"
        f"Мажор дрожащими руками суёт тебе конверт, в котором **{fmt(bribe_sum)}₽**!\n\n"
        f"Что делаем?"
    )
    
    # Сохраняем кулдаун
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE police SET last_shift = ? WHERE user_id = ?', (now, call.from_user.id))
    conn.commit()
    conn.close()

    await call.message.edit_text(text, reply_markup=kb.get_bribe_choice_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "bribe_take")
async def bribe_take(call: CallbackQuery):
    pol = db.get_police_profile(call.from_user.id)
    bribe_sum = pol[1] * random.randint(25000, 60000)

    # 20% Шанс проверки УСБ
    if random.randint(1, 100) <= 20:
        reps = pol[2] + 1
        if reps >= 3:
            # Увольнение
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM police WHERE user_id = ?', (call.from_user.id,))
            conn.commit()
            conn.close()
            await call.message.edit_text("🚨 **ОПЕРАЦИЯ УСБ!** Вас приняли с поличным при взятии взятки!\nВы ПОЗОРНО УВОЛЕНЫ ИЗ МУРа!", reply_markup=kb.get_back_to_menu_kb())
        else:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE police SET reprimands = ? WHERE user_id = ?', (reps, call.from_user.id))
            conn.commit()
            conn.close()
            fine = 50000
            db.add_fine(call.from_user.id, fine)
            await call.message.edit_text(f"🚨 **УСБ НАКРЫЛО СХЕМУ!**\nВам выписан выговор ({reps}/3) и штраф {fmt(fine)}₽!", reply_markup=kb.get_back_to_menu_kb())
    else:
        db.update_balance(call.from_user.id, bribe_sum)
        await call.message.edit_text(f"🤫 **Взятка успешно взята!**\nВы положили в карман **+{fmt(bribe_sum)}₽**! УСБ ничего не заметило.", reply_markup=kb.get_back_to_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "bribe_honest")
async def bribe_honest(call: CallbackQuery):
    pol = db.get_police_profile(call.from_user.id)
    salary = pol[1] * 15000
    
    db.update_balance(call.from_user.id, salary)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE police SET solved_cases = solved_cases + 1 WHERE user_id = ?', (call.from_user.id,))
    conn.commit()
    conn.close()

    await call.message.edit_text(f"📜 Протокол оформлен! Вы получили оклад: **+{fmt(salary)}₽** и +1 раскрытое дело!", reply_markup=kb.get_back_to_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "pol_promote")
async def pol_promote(call: CallbackQuery):
    pol = db.get_police_profile(call.from_user.id)
    if pol[1] >= 14:
        await call.answer("👑 Ты уже Полковник МУРа! Выше только Звезды!", show_alert=True)
        return

    req_cases = pol[1] * 3
    if pol[3] < req_cases:
        await call.answer(f"❌ Нужно раскрыть {req_cases} дел для повышения! (У тебя: {pol[3]})", show_alert=True)
        return

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE police SET rank = rank + 1 WHERE user_id = ?', (call.from_user.id,))
    conn.commit()
    conn.close()

    new_rank = POLICE_RANKS[pol[1]]
    await call.answer(f"🎉 ПОЗДРАВЛЯЕМ! Новое звание: {new_rank}!", show_alert=True)
    await show_police(call)

@dp.callback_query(F.data == "pol_leave")
async def pol_leave(call: CallbackQuery):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM police WHERE user_id = ?', (call.from_user.id,))
    conn.commit()
    conn.close()
    await call.answer("🚪 Вы уволились из МУРа по собственному желанию.", show_alert=True)
    await back_to_main_menu(call, None)

# ================= ЗАПУСК СЕРВЕРА =================

from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    print("==========================================")
    print("🔥 БОТ ГАНГСТЕР 2.0 УСПЕШНО ЗАПУЩЕН! 🔥")
    print("==========================================")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())