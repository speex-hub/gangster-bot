import sqlite3
import time

DB_NAME = "gangster_bot.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT UNIQUE,
            age INTEGER,
            balance INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            reg_type TEXT,
            reg_timestamp INTEGER,
            referrer_id INTEGER,
            channel_bonus_claimed INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim INTEGER DEFAULT 0,
            house_id INTEGER DEFAULT 0,
            business_id INTEGER DEFAULT 0,
            biz_raw_bought_time INTEGER DEFAULT 0,
            taxi_license INTEGER DEFAULT 0,
            car_id INTEGER DEFAULT 0,
            quests_completed INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            issued_time INTEGER,
            stage INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS police (
            user_id INTEGER PRIMARY KEY,
            rank INTEGER DEFAULT 1,
            reprimands INTEGER DEFAULT 0,
            solved_cases INTEGER DEFAULT 0,
            last_shift INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_nickname(nickname):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE LOWER(nickname) = LOWER(?)', (nickname,))
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
    now = int(time.time())
    start_balance = 100000 if reg_type == 'story' else 0

    cursor.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, nickname, age, balance, reg_type, reg_timestamp, referrer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, nickname, age, start_balance, reg_type, now, referrer_id))
    
    conn.commit()
    conn.close()

def update_nickname(user_id, new_nickname):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET nickname = ? WHERE user_id = ?', (new_nickname, user_id))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_reputation(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET reputation = reputation + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def transfer_money(sender_id, receiver_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, sender_id))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, receiver_id))
    conn.commit()
    conn.close()

def add_fine(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute('INSERT INTO fines (user_id, amount, issued_time, stage) VALUES (?, ?, ?, 1)', (user_id, amount, now))
    conn.commit()
    conn.close()

def get_active_fines(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT fine_id, amount, issued_time, stage FROM fines WHERE user_id = ?', (user_id,))
    fines = cursor.fetchall()
    conn.close()
    return fines

def process_fines_logic(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute('SELECT fine_id, amount, issued_time, stage FROM fines WHERE user_id = ?', (user_id,))
    fines = cursor.fetchall()

    for f in fines:
        fine_id, amount, issued_time, stage = f
        elapsed = now - issued_time
        
        if stage == 1 and elapsed > 172800:
            new_amount = int(amount * 1.5)
            cursor.execute('UPDATE fines SET amount = ?, stage = 2, issued_time = ? WHERE fine_id = ?', (new_amount, now, fine_id))
        elif stage == 2 and elapsed > 172800:
            cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
            cursor.execute('DELETE FROM fines WHERE fine_id = ?', (fine_id,))

    conn.commit()
    conn.close()

def pay_fine(fine_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT amount FROM fines WHERE fine_id = ? AND user_id = ?', (fine_id, user_id))
    fine = cursor.fetchone()
    
    if not fine:
        conn.close()
        return False, "Штраф не найден!"

    user = get_user(user_id)
    if user[3] < fine[0]:
        conn.close()
        return False, f"Недостаточно средств! Нужно: {fine[0]:,}₽"

    update_balance(user_id, -fine[0])
    cursor.execute('DELETE FROM fines WHERE fine_id = ?', (fine_id,))
    conn.commit()
    conn.close()
    return True, "Штраф успешно оплачен!"

def get_top_money():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nickname, balance FROM users ORDER BY balance DESC LIMIT 10')
    res = cursor.fetchall()
    conn.close()
    return res

def get_top_reputation():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nickname, reputation FROM users ORDER BY reputation DESC LIMIT 10')
    res = cursor.fetchall()
    conn.close()
    return res

def get_police_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, rank, reprimands, solved_cases, last_shift FROM police WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res