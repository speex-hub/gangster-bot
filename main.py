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

from config import TOKEN, CHANNEL_USERNAME
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

class CasinoBetState(StatesGroup):
    waiting_box_bet = State()
    waiting_bj_bet = State()
    waiting_dice_bet = State()
    waiting_slots_bet = State()


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def fmt(amount: int) -> str:
    """Форматирование чисел с точками: 1000000 -> 1.000.000"""
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
        # Проверяем штрафы перед входом в меню
        db.process_fines_logic(message.from_user.id)
        user = db.get_user(message.from_user.id)
        text = get_dynamic_greeting(user[1], user[3])
        await message.answer(text, reply_markup=kb.get_main_menu_kb())
    else:
        # Рефералка
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != message.from_user.id:
                await state.update_data(referrer_id=ref_id)

        start_text = (
            "👋 Приветствуем тебя в «Бот Гангстер»!\n\n"
            "Здесь тебе предстоит пройти путь от обычного уличного бродяги до криминального босса Москвы: "
            "ты будешь устраиваться на работу (от грузчика до судьи), покупать дешёвую одежду и обходить авторитетов стороной на старте. "
            "Но уже с опытом и кучей пройденных миссий позади ты сможешь покупать дорогие тачки, вешать на них блатные номера "
            "и крутить своими миллионами (разумеется, с логотипом доллара на конце твоего счёта 🤫)\n\n"
            "Перед тем как начать, выбери, как ты хочешь зарегистрироваться:\n\n"
            "1. Пройти сюжетный пролог (~3 минуты): Погружение в историю + бонус 100.000₽ на старт от твоего наставника!\n"
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
        await call.message.edit_text("Загружаем сюжетный пролог...")
        await asyncio.sleep(5)
        
        prologue_1 = (
            "Окраина Москвы. Лето. 23:45. Моросит мелкий неприятный дождь. Ты стоишь под козырьком заброшенного магазина, "
            "поджав губы от холода. В кармане джинсов — дыра и ровно 12 рублей сдачи от сигарет.\n\n"
            "Из темноты переулка медленно выезжает чёрный Мерседес. Он сбавляет ход и останавливается прямо напротив тебя. "
            "Стекло пассажирской двери плавно опускается.\n\n"
            "Из салона на тебя смотрят тяжелые, уставшие глаза мужика лет 45. На щеке — шрам, на пальцах — перстни, а из динамиков тихо играет шансон.\n\n"
            "— Эй, пацан, — глухо произносит он, стряхивая пепел с сигареты. — Ты чего тут замерзаешь? На тусовщика не похож, на мента тем более. "
            "Как тебя величать-то?\n\n"
            "(Введи имя своего персонажа, от 2 до 25 букв):"
        )
        await call.message.answer(prologue_1)
    else:
        await call.message.answer("Введи имя своего персонажа (от 2 до 25 букв):")
        
    await state.set_state(RegState.waiting_for_name)


@dp.message(RegState.waiting_for_name)
async def process_reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    clean_name = "".join([c for c in name if c.isalpha()])
    
    # СТРОГАЯ ПРОВЕРКА: от 2 до 20 символов!
    if len(name) < 2 or len(name) > 20 or len(clean_name) == 0:
        await message.answer("Некорректное имя! Имя должно содержать буквы и быть длиной от 2 до 20 символов. Попробуй еще раз:")
        return

    if db.is_nickname_taken(name):
        await message.answer("Этот никнейм уже занят на улицах Москвы! Придумай другой никнейм:")
        return

    await state.update_data(nickname=name)
    data = await state.get_data()
    reg_type = data.get('reg_type')

    if reg_type == 'story':
        text = (
            f"— Меня зовут {name}, — ответил ты, чуть заикаясь от холода и поднимая воротник куртки.\n\n"
            "Мужик в машине едва заметно усмехнулся, оценивающе оглядывая тебя с ног до головы: твои поношенные кроссовки, мокрую толстовку и взъерошенные волосы.\n\n"
            f"— Ну, здорово, {name}. А я Виктор. Для своих — Седой. Вижу по глазам, что жизнь тебя не по головке гладила, а прямо сейчас тебе даже погреться негде.\n\n"
            "Седой щелчком выкинул бычок в лужу и кивнул на соседнее кожаное сиденье.\n\n"
            "— Запрыгивай. В машине тепло. Потолкуем. Только давай без глупостей — у меня на таких, как ты, чуйка. Сколько тебе лет-то вообще, «гангстер»?\n\n"
            "(Введи возраст своего персонажа. Ему должно быть от 18 до 35 лет!):"
        )
        await message.answer(text)
    else:
        await message.answer(f"Отлично, {name}! Теперь введи возраст своего персонажа (целое число от 18 до 35):")
        
    await state.set_state(RegState.waiting_for_age)


@dp.message(RegState.waiting_for_age)
async def process_reg_age(message: Message, state: FSMContext):
    age_str = message.text.strip()
    
    if not age_str.isdigit() or not (18 <= int(age_str) <= 35):
        await message.answer("Некорректный возраст! Введи только целое число от 18 до 35 лет:")
        return

    age = int(age_str)
    data = await state.get_data()
    nickname = data['nickname']
    reg_type = data['reg_type']
    referrer_id = data.get('referrer_id')

    # Регистрируем в БД
    db.register_user(message.from_user.id, nickname, age, reg_type, referrer_id)
    await state.clear()

    if reg_type == 'story':
        text = (
            f"— Мне {age}, — сказал ты, хлопая дверью тяжелого внедорожника. В салоне пахло дорогим парфюмом, хорошим табаком и коньяком.\n\n"
            f"— {age}... — Седой задумчиво протянул эту цифру, плавно трогаясь с места. — Самый сок, чтобы либо подняться на вершину этого города, либо сгнить в камере или под забором. Третьего в нашем городе не дано.\n\n"
            "Гелик плавно мчал по ночным улицам. За окном мелькали огни неоновых вывесок, дорогие автосалоны, элитные клубы... и темные подворотни, где кипела совсем другая жизнь.\n\n"
            f"— Знаешь, {nickname}, я ведь тоже начинал никем. Стоял вот так же в дождь, без гроша в кармане. А сейчас... этот город работает на меня. Но мне нужны верные люди. Наглые, голодные до денег, но с головой на плечах.\n\n"
            "Седой остановил машину у светофора, достал из бардачка пухлый кожаный конверт и бросил тебе на колени."
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
    user = db.get_user(call.from_user.id)
    
    text = (
        "Ты расстёгиваешь молнию конверта. Внутри — новенькие, хрустящие купюры и визитка с номером Виктора.\n\n"
        "— Тут 100.000₽, — спокойно говорит Седой. — Это тебе подъемные. На первое время: снимeшь хату, купишь нормальные шмотки, может, вложишься во что-то. Считай это авансом за твоё будущее.\n\n"
        "Светофор загорается зелёным, и Гелик с рёвом устремляется в центр города.\n\n"
        "— Завтра утром жду тебя в деле. Начнёшь с простого — надо прощупать почву. Работа грузчиком или таксистом для прикрытия отлично подойдет. А дальше... дальше покажешь, на что способен. Добро пожаловать в игру. Не подведи меня.\n\n"
        "Виктор высаживает тебя у проспекта. Рядом, пару панельных зданий, в которых точно можно найти и снять квартиру, а также кафе, где можно погреться и нормально покушать.\n\n"
        "Машина срывается с места и с визгом шин уезжает в ночную Москву.\n\n"
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
    pol = db.get_police_profile(call.from_user.id)
    
    ranks = [
        "Рядовой", "Мл. сержант", "Сержант", "Ст. сержант", "Старшина", "Прапорщик",
        "Ст. прапорщик", "Мл. лейтенант", "Лейтенант", "Ст. лейтенант", "Капитан", "Майор", "Подполковник", "Полковник"
    ]
    rank_str = ranks[pol[1] - 1] if pol else "Не состоит"

    text = (
        f"🏙 Профиль гангстера: {user[1]}\n"
        f"_________________________\n"
        f"👤 Возраст: {user[2]} лет\n"
        f"🏙 Город: Москва\n"
        f"💵 Баланс: {fmt(user[3])}₽\n"
        f"👑 Репутация: {fmt(user[4])} авторитета\n"
        f"🚔 Звание в МУР: {rank_str}\n"
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
    await call.message.edit_text("Введи новое имя своего персонажа (от 2 до 25 букв):")
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
        "📜 *Быстрые команды бота:*\n\n"
        "⚡️ `/profile` или `/p` — Открыть твой профиль\n"
        "💵 `/balance` или `/b` — Быстрый просмотр баланса\n"
        "🏆 `/top` — ТОП-10 богачей и авторитетов Москвы\n"
        "⚠️ `/fines` — Посмотреть твои неоплаченные штрафы\n"
        "🤝 `/ref` — Получить свою реферальную ссылку\n\n"
        "💸 *Перевод денег другим игрокам:*\n"
        "Команда: `/pay Никнейм Сумма`\n"
        "_(Пример: `/pay Серёга 50000`)_\n"
        "⚠️ *Комиссия уличных переводов составляет 5%*"
    )
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "sett_info")
async def show_info(call: CallbackQuery):
    text = (
        "ℹ️ О боте «Бот Гангстер»:\n\n"
        "Это криминальная текстовая RPG в сердце ночной Москвы. Пройди путь от замерзающего попрошайки "
        "до хозяина Нефтегазовой компании и дворца на Рублёвке.\n\n"
        "Работай на легальных и нелегальных работах, прокручивай схемы в МУРе, закупай сырьё для бизнесов, "
        "крути рулетку в казино и не попадайся УСБ!"
    )
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb())

@dp.callback_query(F.data == "sett_help")
async def show_help(call: CallbackQuery):
    text = (
        "🛠 Помощь и техподдержка:\n\n"
        "При возникновении вопросов, багов или нештатных ситуаций, пишите напрямую нашему администратору:\n"
        "👉 @ice_speex"
    )
    await call.message.edit_text(text, reply_markup=kb.get_settings_kb())


# ================= ЛЕГАЛЬНЫЕ И НЕЛЕГАЛЬНЫЕ РАБОТЫ =================

@dp.callback_query(F.data == "menu_jobs")
async def show_jobs_category(call: CallbackQuery):
    await call.message.edit_text("Выбери категорию занятости:", reply_markup=kb.get_jobs_category_kb())

@dp.callback_query(F.data == "jobs_legal")
async def show_legal_jobs(call: CallbackQuery):
    await call.message.edit_text("🟢 Легальные работы (Без риска и штрафов):", reply_markup=kb.get_legal_jobs_kb())

# --- Грузчик (5-7 сек) ---
@dp.callback_query(F.data == "work_loader")
async def do_loader(call: CallbackQuery):
    await call.message.edit_text("📦 Ты взял тяжёлую коробку и тащишь её на склад... (подожди 6 сек)")
    await asyncio.sleep(6)
    
    earn = random.randint(300, 800)
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    
    text = f"📦 Ты разгрузил фуру и получил {fmt(earn)}₽!\nТвой баланс: {fmt(user[3])}₽"
    await call.message.answer(text, reply_markup=kb.get_legal_jobs_kb())

# --- Курьер (7-10 сек) ---
@dp.callback_query(F.data == "work_courier")
async def do_courier(call: CallbackQuery):
    delay = random.randint(7, 10)
    await call.message.edit_text(f"🚴 Ты взял заказ и мчишь на электровелосипеде... (подожди {delay} сек)")
    await asyncio.sleep(delay)
    
    earn = int(delay * random.randint(150, 250))
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    
    text = f"🍕 Заказ доставлен! Клиент заплатил {fmt(earn)}₽.\nТвой баланс: {fmt(user[3])}₽"
    await call.message.answer(text, reply_markup=kb.get_legal_jobs_kb())

# --- Таксист ---
@dp.callback_query(F.data == "work_taxi")
async def do_taxi(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if not user[14]: # taxi_license
        if user[3] < 20000:
            await call.answer("❌ Нужно 20.000₽ для покупки лицензии таксиста!", show_alert=True)
            return
        db.update_balance(call.from_user.id, -20000)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET taxi_license = 1 WHERE user_id = ?', (call.from_user.id,))
        conn.commit()
        conn.close()
        await call.answer("🎉 Ты купил лицензию таксиста за 20.000₽!", show_alert=True)

    delay = random.randint(7, 12)
    await call.message.edit_text(f"🚖 Взял пассажира, везёшь в другой район... (подожди {delay} сек)")
    await asyncio.sleep(delay)
    
    earn = int(delay * random.randint(250, 400))
    db.update_balance(call.from_user.id, earn)
    user = db.get_user(call.from_user.id)
    
    text = f"🏁 Рейс выполнен! Пассажир расплатился: {fmt(earn)}₽.\nТвой баланс: {fmt(user[3])}₽"
    await call.message.answer(text, reply_markup=kb.get_legal_jobs_kb())


# ================= ШТРАФЫ =================

@dp.callback_query(F.data == "menu_fines")
async def show_fines(call: CallbackQuery):
    db.process_fines_logic(call.from_user.id)
    fines = db.get_active_fines(call.from_user.id)
    
    if not fines:
        await call.message.edit_text("✅ У тебя нет активных штрафов! Ты чист перед законами улиц.", reply_markup=kb.get_back_to_menu_kb())
        return

    text = "⚠️ Ваши неоплаченные штрафы:\n\n"
    now = int(time.time())
    
    inline_kb = []
    for f in fines:
        fine_id, amount, issued_time, stage = f
        left = 172800 - (now - issued_time)
        hrs = max(0, int(left // 3600))
        mins = max(0, int((left % 3600) // 60))
        
        st_text = "Обычный (48ч)" if stage == 1 else "ПЕНЯ +50% (Последний шанс 48ч)"
        text += f"🆔 #{fine_id} | Сумма: {fmt(amount)}₽ | Статус: {st_text} | Осталось: {hrs}ч {mins}мин\n"
        inline_kb.append([kb.InlineKeyboardButton(text=f"💳 Оплатить #{fine_id} ({fmt(amount)}₽)", callback_data=f"pay_fine_{fine_id}")])

    inline_kb.append([kb.InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")])
    await call.message.edit_text(text, reply_markup=kb.InlineKeyboardMarkup(inline_keyboard=inline_kb))

@dp.callback_query(F.data.startswith("pay_fine_"))
async def process_pay_fine(call: CallbackQuery):
    fine_id = int(call.data.split("_")[2])
    success, msg = db.pay_fine(fine_id, call.from_user.id)
    await call.answer(msg, show_alert=True)
    await show_fines(call)


# ================= ЕЖЕДНЕВНЫЙ БОНУС =================

@dp.callback_query(F.data == "menu_daily")
async def claim_daily(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    last_claim = user[10]
    streak = user[9]
    now = int(time.time())
    
    # 24 часа = 86400 сек
    if now - last_claim < 86400:
        left = 86400 - (now - last_claim)
        hrs = int(left // 3600)
        mins = int((left % 3600) // 60)
        await call.answer(f"⏳ Следующий бонус можно забрать через {hrs}ч {mins}мин!", show_alert=True)
        return

    if now - last_claim > 172800: # Пропустил больше 48 часов
        streak = 0

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


# ================= ТОП ИГРОКОВ =================

@dp.callback_query(F.data == "menu_top")
async def show_top(call: CallbackQuery):
    top_m = db.get_top_money()
    top_r = db.get_top_reputation()

    text = "🏆 ТОП-10 БОГАЧЕЙ МОСКВЫ:\n"
    for i, u in enumerate(top_m, 1):
        text += f"{i}. {u[0]} — {fmt(u[1])}₽\n"

    text += "\n👑 ТОП-10 АВТОРИТЕТОВУЛИЦ:\n"
    for i, u in enumerate(top_r, 1):
        text += f"{i}. {u[0]} — {fmt(u[1])} авторитета\n"

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
        "• Когда твой реферал заработает 1.000.000₽, ты получишь 3.000.000₽!\n"
        f"• Подпишись на наш канал @{CHANNEL_USERNAME} и забери 200.000₽!"
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
    if user[8]: # channel_bonus_claimed
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
        await call.answer("Ошибка проверки подписки. Убедитесь, что канал существует.", show_alert=True)

from config import ADMIN_ID

# --- СЕКРЕТНАЯ АДМИНКА ТОЛЬКО ДЛЯ ТЕБЯ ---
@dp.message(Command("adm_add_cash_99"))
async def admin_give_money(message: Message):
    # Проверка: если пишет НЕ админ — бот делает вид, что команды не существует
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Пиши: `/adm_add_cash_99 5000000` (сумма числом)")
        return
    
    amount = int(args[1])
    db.update_balance(message.from_user.id, amount)
    user = db.get_user(message.from_user.id)
    
    await message.answer(f"👑 *АДМИН-ПАНЕЛЬ*\nУспешно начислено: +{fmt(amount)}₽\nТвой баланс: {fmt(user[3])}₽")

# ================= БЫСТРЫЕ ТЕКСТОВЫЕ КОМАНДЫ =================

@dp.message(Command("profile", "p"))
async def cmd_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user: return
    pol = db.get_police_profile(message.from_user.id)
    ranks = ["Рядовой", "Мл. сержант", "Сержант", "Ст. сержант", "Старшина", "Прапорщик", "Ст. прапорщик", "Мл. лейтенант", "Лейтенант", "Ст. лейтенант", "Капитан", "Майор", "Подполковник", "Полковник"]
    rank_str = ranks[pol[1] - 1] if pol else "Не состоит"
    
    text = (
        f"🏙 Профиль гангстера: {user[1]}\n"
        f"_________________________\n"
        f"👤 Возраст: {user[2]} лет\n"
        f"🏙 Город: Москва\n"
        f"💵 Баланс: {fmt(user[3])}₽\n"
        f"👑 Репутация: {fmt(user[4])} авторитета\n"
        f"🚔 Звание в МУР: {rank_str}\n"
    )
    await message.answer(text, reply_markup=kb.get_back_to_menu_kb())

@dp.message(Command("balance", "b"))
async def cmd_balance(message: Message):
    user = db.get_user(message.from_user.id)
    if not user: return
    await message.answer(f"💵 Твой баланс: {fmt(user[3])}₽")

@dp.message(Command("top"))
async def cmd_top(message: Message):
    top_m = db.get_top_money()
    top_r = db.get_top_reputation()
    text = "🏆 ТОП-10 БОГАЧЕЙ МОСКВЫ:\n"
    for i, u in enumerate(top_m, 1): text += f"{i}. {u[0]} — {fmt(u[1])}₽\n"
    text += "\n👑 ТОП-10 АВТОРИТЕТОВ УЛИЦ:\n"
    for i, u in enumerate(top_r, 1): text += f"{i}. {u[0]} — {fmt(u[1])} авторитета\n"
    await message.answer(text, reply_markup=kb.get_back_to_menu_kb())

@dp.message(Command("fines"))
async def cmd_fines(message: Message):
    db.process_fines_logic(message.from_user.id)
    fines = db.get_active_fines(message.from_user.id)
    if not fines:
        await message.answer("✅ У тебя нет активных штрафов!")
        return
    text = "⚠️ Ваши неоплаченные штрафы:\n"
    for f in fines:
        text += f"🆔 #{f[0]} | Сумма: {fmt(f[1])}₽\n"
    await message.answer(text)

# --- ПЕРЕВОД ДЕНЕГ МЕЖДУ ИГРОКАМИ ---
@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    # Команда вида: /pay Никнейм 50000
    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        await message.answer("⚠️ Использование: `/pay Никнейм 50000`\n(Пример: `/pay Серёга 100000`)", parse_mode="Markdown")
        return

    target_nick = args[1]
    amount = int(args[2])
    sender = db.get_user(message.from_user.id)

    if amount <= 0:
        await message.answer("❌ Сумма перевода должна быть больше 0!")
        return

    if sender[3] < amount:
        await message.answer(f"❌ Недостаточно денег! Твой баланс: {fmt(sender[3])}₽")
        return

    receiver = db.get_user_by_nickname(target_nick)
    if not receiver:
        await message.answer(f"❌ Игрок с никнеймом «{target_nick}» не найден на улицах Москвы!")
        return

    if receiver[0] == message.from_user.id:
        await message.answer("❌ Нельзя переводить деньги самому себе!")
        return

    # Перевод с комиссией 5% (уличный налог)
    tax = int(amount * 0.05)
    final_amount = amount - tax

    db.transfer_money(message.from_user.id, receiver[0], amount)
    # Начисляем получателю сумму за вычетом комиссии
    db.update_balance(receiver[0], -tax)

    await message.answer(
        f"💸 Успешный перевод!\n\n"
        f"Вы перевели игроку {receiver[1]}: {fmt(amount)}₽\n"
        f"Уличная комиссия (5%): {fmt(tax)}₽\n"
        f"Ему дошло: {fmt(final_amount)}₽"
    )

# --- СЕКРЕТНАЯ АДМИНКА ТОЛЬКО ДЛЯ ТЕБЯ ---
@dp.message(Command("adm_add_cash_99"))
async def admin_give_money(message: Message):
    from config import ADMIN_ID
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Пиши: `/adm_add_cash_99 5000000`")
        return
    
    amount = int(args[1])
    db.update_balance(message.from_user.id, amount)
    user = db.get_user(message.from_user.id)
    await message.answer(f"👑 **АДМИН-ПАНЕЛЬ**\nНачислено: +{fmt(amount)}₽\nТвой баланс: {fmt(user[3])}₽", parse_mode="Markdown")

# ================= ЗАПУСК СЕРВЕРА =================

async def main():
    db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("==========================================")
    print("🔥 БОТ ГАНГСТЕР 2.0 УСПЕШНО ЗАПУЩЕН! 🔥")
    print("==========================================")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())