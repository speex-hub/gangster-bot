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
        [InlineKeyboardButton(text="🎰 казино", callback_data="menu_casino"), InlineKeyboardButton(text="⚠️ штрафы", callback_data="menu_fines")],
        [InlineKeyboardButton(text="🎁 ежедневный бонус", callback_data="menu_daily"), InlineKeyboardButton(text="🏆 топ игроков", callback_data="menu_top")],
        [InlineKeyboardButton(text="🤝 рефералка", callback_data="menu_ref"), InlineKeyboardButton(text="⚙️ настройки", callback_data="menu_settings")]
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
        [InlineKeyboardButton(text="🏢 мой бизнес", callback_data="menu_business")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_legal_jobs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 грузчик", callback_data="work_loader")],
        [InlineKeyboardButton(text="🚴 курьер", callback_data="work_courier")],
        [InlineKeyboardButton(text="🚖 таксист", callback_data="work_taxi")],
        [InlineKeyboardButton(text="⬅️ к категориям работ", callback_data="menu_jobs")]
    ])

def get_illegal_jobs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤏 мелкий щипач", callback_data="work_pickpocket")],
        [InlineKeyboardButton(text="📦 наркокурьер", callback_data="work_dealer")],
        [InlineKeyboardButton(text="🔨 коллектор", callback_data="work_collector")],
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


# --- 6. БИЗНЕСЫ И НЕДВИЖИМОСТЬ ---
def get_business_catalog_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏪 ларек с шаурмой (100.000₽)", callback_data="buy_biz_1")],
        [InlineKeyboardButton(text="🍔 точка фаст-фуда (500.000₽)", callback_data="buy_biz_2")],
        [InlineKeyboardButton(text="🧼 автомойка (3.500.000₽)", callback_data="buy_biz_3")],
        [InlineKeyboardButton(text="🥊 бойцовский клуб (10.000.000₽)", callback_data="buy_biz_4")],
        [InlineKeyboardButton(text="🍽 ресторан (30.000.000₽)", callback_data="buy_biz_5")],
        [InlineKeyboardButton(text="🎰 теневое казино (80.000.000₽)", callback_data="buy_biz_6")],
        [InlineKeyboardButton(text="🏦 коммерческий банк (250.000.000₽)", callback_data="buy_biz_7")],
        [InlineKeyboardButton(text="✈️ авиакомпания (750.000.000₽)", callback_data="buy_biz_8")],
        [InlineKeyboardButton(text="🛢 нефтегазовая компания (2.500.000.000₽)", callback_data="buy_biz_9")],
        [InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])

def get_house_catalog_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏚 комната на окраине (2.500.000₽)", callback_data="buy_house_1")],
        [InlineKeyboardButton(text="🏠 однушка на окраине (9.000.000₽)", callback_data="buy_house_2")],
        [InlineKeyboardButton(text="🏙 двушка в 6км от центра (22.000.000₽)", callback_data="buy_house_3")],
        [InlineKeyboardButton(text="🏡 1-эт. дом в частном секторе (35.000.000₽)", callback_data="buy_house_4")],
        [InlineKeyboardButton(text="🏢 трёшка в 3км от центра (65.000.000₽)", callback_data="buy_house_5")],
        [InlineKeyboardButton(text="🏰 2-эт. дом в частном секторе (80.000.000₽)", callback_data="buy_house_6")],
        [InlineKeyboardButton(text="🏊‍♂️ 3-эт. дом с бассейном (250.000.000₽)", callback_data="buy_house_7")],
        [InlineKeyboardButton(text="🏙 5-комн. квартира в moscow city (550.000.000₽)", callback_data="buy_house_8")],
        [InlineKeyboardButton(text="👑 дворец на рублёвке (1.500.000.000₽)", callback_data="buy_house_9")],
        [InlineKeyboardButton(text="🏝 резиденция на частном острове (5.000.000.000₽)", callback_data="buy_house_10")],
[InlineKeyboardButton(text="⬅️ в главное меню", callback_data="to_main_menu")]
    ])