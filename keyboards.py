from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. СТАРТ И РЕГИСТРАЦИЯ ---
def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="пройти сюжетный пролог", callback_data="reg_story")],
        [InlineKeyboardButton(text="быстрая регистрация", callback_data="reg_fast")]
    ])

def get_fast_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="начать сюжетный пролог", callback_data="reg_story")],
        [InlineKeyboardButton(text="уверен, быстрая регистрация", callback_data="reg_fast_start")]
    ])

def get_prologue_envelope_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="посмотреть, что в конверте", callback_data="prologue_open_envelope")]
    ])


# --- 2. ГЛАВНОЕ МЕНЮ ---
def get_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 профиль", callback_data="menu_profile"), InlineKeyboardButton(text="💼 работы", callback_data="menu_jobs")],
        [InlineKeyboardButton(text="🏢 бизнесы", callback_data="menu_business"), InlineKeyboardButton(text="🏠 недвижимость", callback_data="menu_houses")],
        [InlineKeyboardButton(text="🚗 автосалон", callback_data="menu_cars"), InlineKeyboardButton(text="🕵️‍♂️ квесты седого", callback_data="menu_quests")],
        [InlineKeyboardButton(text="👮‍♂️ МУР (Полиция)", callback_data="menu_police"), InlineKeyboardButton(text="🎰 казино", callback_data="menu_casino")],
        [InlineKeyboardButton(text="⚠️ штрафы", callback_data="menu_fines"), InlineKeyboardButton(text="🎁 бонус", callback_data="menu_daily")],
        [InlineKeyboardButton(text="🏆 топ игроков", callback_data="menu_top"), InlineKeyboardButton(text="🤝 рефералка", callback_data="menu_ref")],
        [InlineKeyboardButton(text="⚙️ настройки", callback_data="menu_settings")]
    ])

def get_back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])


# --- 3. НАСТРОЙКИ И ПРОФИЛЬ ---
def get_settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="мой персонаж", callback_data="sett_character")],
        [InlineKeyboardButton(text="команды", callback_data="sett_commands")],
        [InlineKeyboardButton(text="инфо о боте", callback_data="sett_info")],
        [InlineKeyboardButton(text="помощь", callback_data="sett_help")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_character_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ изменить имя", callback_data="change_name")],
        [InlineKeyboardButton(text="⬅️ в настройки", callback_data="menu_settings")]
    ])


# --- 4. РАБОТЫ ---
def get_jobs_category_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 легальные работы", callback_data="jobs_legal")],
        [InlineKeyboardButton(text="🔴 нелегальные работы", callback_data="jobs_illegal")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_legal_jobs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📦 грузчик", callback_data="info_job_loader")],
        [InlineKeyboardButton(text="🚴 курьер", callback_data="info_job_courier")],
        [InlineKeyboardButton(text="🚖 таксист", callback_data="info_job_taxi")],
        [InlineKeyboardButton(text="⬅️ к категориям работ", callback_data="menu_jobs")]
    ])

def get_illegal_jobs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤏 мелкий щипач (0 авторитета)", callback_data="info_job_pickpocket")],
        [InlineKeyboardButton(text="📦 наркокурьер (15 авторитета)", callback_data="info_job_dealer")],
        [InlineKeyboardButton(text="🔨 коллектор (50 авторитета)", callback_data="info_job_collector")],
        [InlineKeyboardButton(text="⬅️ к категориям работ", callback_data="menu_jobs")]
    ])


# --- 5. КАЗИНО ---
def get_casino_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥊 ставки на бокс", callback_data="cas_box")],
        [InlineKeyboardButton(text="🎲 кости (x5)", callback_data="cas_dice")],
        [InlineKeyboardButton(text="🎰 777 слоты", callback_data="cas_slots")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_box_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥊 фаворит (65% шанс | x1.5)", callback_data="box_fav")],
        [InlineKeyboardButton(text="🐴 тёмная лошадка (35% шанс | x2.5)", callback_data="box_underdog")],
        [InlineKeyboardButton(text="⬅️ в казино", callback_data="menu_casino")]
    ])


# --- 6. МУР И ПОЛИЦИЯ ---
def get_police_kb(in_police: bool):
    if not in_police:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👮‍♂️ Устроиться в МУР (100.000₽)", callback_data="pol_join")],
            [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕵️‍♂️ Пойти на смену (Взятки)", callback_data="pol_work")],
        [InlineKeyboardButton(text="⭐ Повысить звание", callback_data="pol_promote")],
        [InlineKeyboardButton(text="🚪 Уволиться из МУРа", callback_data="pol_leave")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_bribe_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Взять взятку (+Деньги | 20% шанс УСБ)", callback_data="bribe_take")],
        [InlineKeyboardButton(text="📜 Оформить протокол (+ЗП и Опыт | 0% риска)", callback_data="bribe_honest")]
    ])


# --- 7. КВЕСТЫ СЕДОГО ---
def get_quests_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Квест #1: Перехват грузовика (от 10 авт.)", callback_data="do_quest_1")],
        [InlineKeyboardButton(text="🎯 Квест #2: Угон спорткара депутата (от 30 авт.)", callback_data="do_quest_2")],
        [InlineKeyboardButton(text="🎯 Квест #3: Налёт на теневой банк (от 75 авт.)", callback_data="do_quest_3")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])