import sqlite3
import time
from datetime import datetime, timedelta

DB_NAME = "gangster_bot.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Создание всех таблиц системы"""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT UNIQUE,
            age INTEGER,
            balance INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            registration_type TEXT,
            referrer_id INTEGER DEFAULT NULL,
            ref_reward_claimed INTEGER DEFAULT 0,
            channel_bonus_claimed INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim INTEGER DEFAULT 0,
            house_id INTEGER DEFAULT 0,
            business_id INTEGER DEFAULT 0,
            biz_raw_bought_time INTEGER DEFAULT 0,
            taxi_license INTEGER DEFAULT 0
        )
    ''')

    # Таблица системы полиции (МУР)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS police (
            user_id INTEGER PRIMARY KEY,
            rank_id INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            last_shift INTEGER DEFAULT 0
        )
    ''')

    # Таблица штрафов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            issued_time INTEGER,
            stage INTEGER DEFAULT 1,
            is_paid INTEGER DEFAULT 0
        )
    ''')

    # Таблица рефералов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referral_id INTEGER PRIMARY KEY,
            earned_million INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


# ================= РАБОТА С ПОЛЬЗОВАТЕЛЯМИ =================

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def is_nickname_taken(nickname):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE LOWER(nickname) = LOWER(?)', (nickname,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def register_user(user_id, nickname, age, reg_type, referrer_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Стартовый баланс: если сюжет - 100.000, если быстрая - 0
    start_bal = 100000 if reg_type == 'story' else 0
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, nickname, age, balance, registration_type, referrer_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, nickname, age, start_bal, reg_type, referrer_id))
    
    # Создаем запись в полиции
    cursor.execute('INSERT OR IGNORE INTO police (user_id) VALUES (?)', (user_id,))
    
    if referrer_id:
        cursor.execute('INSERT OR IGNORE INTO referrals (referrer_id, referral_id) VALUES (?, ?)', (referrer_id, user_id))

    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def set_balance(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_reputation(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET reputation = reputation + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_nickname(user_id, new_nickname):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET nickname = ? WHERE user_id = ?', (new_nickname, user_id))
    conn.commit()
    conn.close()


# ================= СИСТЕМА ШТРАФОВ (48 ЧАСОВ) =================

def add_fine(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute('INSERT INTO fines (user_id, amount, issued_time) VALUES (?, ?, ?)', (user_id, amount, now))
    conn.commit()
    conn.close()

def get_active_fines(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, amount, issued_time, stage FROM fines WHERE user_id = ? AND is_paid = 0', (user_id,))
    fines = cursor.fetchall()
    conn.close()
    return fines

def pay_fine(fine_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT amount FROM fines WHERE id = ? AND user_id = ? AND is_paid = 0', (fine_id, user_id))
    fine = cursor.fetchone()
    
    if not fine:
        conn.close()
        return False, "Штраф не найден."

    amount = fine[0]
    user = get_user(user_id)
    
    if user[3] < amount:
        conn.close()
        return False, "Недостаточно денег для оплаты штрафа!"

    # Списываем бабки и закрываем штраф
    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    cursor.execute('UPDATE fines SET is_paid = 1 WHERE id = ?', (fine_id,))
    conn.commit()
    conn.close()
    return True, f"Штраф на сумму {amount:,}₽ успешно оплачен!".replace(",", ".")

def process_fines_logic(user_id):
    """Проверка и обновление статуса штрафов (просрочка 48ч)"""
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())
    
    cursor.execute('SELECT id, amount, issued_time, stage FROM fines WHERE user_id = ? AND is_paid = 0', (user_id,))
    fines = cursor.fetchall()
    
    for fine in fines:
        fine_id, amount, issued_time, stage = fine
        elapsed = now - issued_time
        
        # 48 часов = 172800 секунд
        if stage == 1 and elapsed >= 172800:
            # Увеличиваем штраф на 50% и переводим на этап 2
            new_amount = int(amount * 1.5)
            cursor.execute('UPDATE fines SET amount = ?, stage = 2, issued_time = ? WHERE id = ?', (new_amount, now, fine_id))
            
        elif stage == 2 and elapsed >= 172800:
            # Не оплатил за вторые 48 часов -> Обнуление баланса
            cursor.execute('UPDATE users SET balance = 0 WHERE user_id = ?', (user_id,))
            cursor.execute('UPDATE fines SET is_paid = 1 WHERE id = ?', (fine_id,))
            
    conn.commit()
    conn.close()


# ================= МУР / ПОЛИЦИЯ =================

def get_police_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM police WHERE user_id = ?', (user_id,))
    prof = cursor.fetchone()
    conn.close()
    return prof

def update_police_stats(user_id, xp_change, warnings_change=0):
    conn = get_connection()
    cursor = conn.cursor()
    
    prof = get_police_profile(user_id)
    new_xp = max(0, prof[2] + xp_change)
    new_warns = max(0, prof[3] + warnings_change)
    
    # Логика 3 выговоров
    rank_id = prof[1]
    if new_warns >= 3:
        rank_id = max(1, rank_id - 1) # Понижение звания
        new_warns = 0 # Сброс выговоров
        
    cursor.execute('UPDATE police SET xp = ?, warnings = ?, rank_id = ? WHERE user_id = ?', (new_xp, new_warns, rank_id, user_id))
    conn.commit()
    conn.close()


# ================= ТОПЫ И СТАТИСТИКА =================

def get_top_money():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nickname, balance FROM users ORDER BY balance DESC LIMIT 10')
    top = cursor.fetchall()
    conn.close()
    return top

def get_top_reputation():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nickname, reputation FROM users ORDER BY reputation DESC LIMIT 10')
    top = cursor.fetchall()
    conn.close()
    return top

def get_user_by_nickname(nickname):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE LOWER(nickname) = LOWER(?)', (nickname,))
    user = cursor.fetchone()
    conn.close()
    return user

def transfer_money(sender_id, receiver_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, sender_id))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, receiver_id))
    conn.commit()
    conn.close()