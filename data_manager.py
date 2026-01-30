import sqlite3
import os
import time
from datetime import datetime

DB_PATH = "data/temple_data.db"


class DataManager:
    def __init__(self):
        self.check_db()
        self.session_start_time = None
        self.session_coins = 0
        self.current_session_levels = []

    def check_db(self): #создает папку data и таблицы в БД
        if not os.path.exists("data"):
            os.makedirs("data")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        #таблица для полных прохождения всех 3 уровней
        c.execute('''CREATE TABLE IF NOT EXISTS full_sessions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_date DATETIME,
                      total_time REAL,
                      total_coins INTEGER,
                      levels_completed TEXT)''')

        #таблица для отдельных уровней
        c.execute('''CREATE TABLE IF NOT EXISTS progress
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      level INTEGER, 
                      best_time REAL, 
                      coins_collected INTEGER,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        conn.commit()
        conn.close()

    def start_session(self): #начинает новую сессию, сбрасывая счетчики
        self.session_start_time = time.time()
        self.session_coins = 0
        self.current_session_levels = []

    def add_level_result(self, level, time_taken, coins): #добавляет результат уровня в текущую сессию и сохраняет
        self.current_session_levels.append({
            'level': level,
            'time': time_taken,
            'coins': coins
        })
        self.session_coins += coins
        self.save_single_level(level, time_taken, coins)

    def save_single_level(self, level, time_taken, coins): #сохраняет результат отдельного уровня, обновляя лучшее время
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT best_time FROM progress WHERE level = ? ORDER BY best_time ASC LIMIT 1", (level,))
        existing_best = c.fetchone()

        if not existing_best or time_taken < existing_best[0]:
            c.execute("INSERT INTO progress (level, best_time, coins_collected) VALUES (?, ?, ?)",
                      (level, round(time_taken, 2), coins))

        conn.commit()
        conn.close()

    def complete_session(self): #завершает сессию и сохраняет (только при прохождении всех 3 уровней)
        if not self.session_start_time or not self.current_session_levels:
            return False

        total_time = time.time() - self.session_start_time
        levels_completed = len(self.current_session_levels)

        if levels_completed == 3: #форматирует данные
            levels_data = ";".join([f"L{l['level']}:{l['time']:.1f}s:{l['coins']}c"
                                    for l in self.current_session_levels])

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO full_sessions 
                         (session_date, total_time, total_coins, levels_completed) 
                         VALUES (?, ?, ?, ?)""",
                      (current_time, round(total_time, 2), self.session_coins, levels_data))

            conn.commit()
            conn.close()
            return True

        return False

    def get_full_sessions(self, limit=10): # последние полные сессии, по дате
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT session_date, total_time, total_coins, levels_completed 
            FROM full_sessions 
            ORDER BY session_date DESC 
            LIMIT ?
        """, (limit,))
        data = c.fetchall()
        conn.close()
        return data

    def get_best_full_sessions(self, limit=5): #лучшие полные сессии, по времени
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT session_date, total_time, total_coins, levels_completed 
            FROM full_sessions 
            ORDER BY total_time ASC 
            LIMIT ?
        """, (limit,))
        data = c.fetchall()
        conn.close()
        return data

    def get_level_stats(self): #статистика по лучшим результатам каждого уровня
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT level, MIN(best_time) as best_time, 
                   MAX(coins_collected) as max_coins, 
                   COUNT(*) as attempts 
            FROM progress 
            GROUP BY level 
            ORDER BY level
        """)
        data = c.fetchall()
        conn.close()
        return data

    def get_recent_games(self, limit=5): #последние отдельные попытки по уровням
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT level, best_time, coins_collected, timestamp 
            FROM progress 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        data = c.fetchall()
        conn.close()
        return data

    def get_session_summary(self): #текущий прогресс сессии (уровни, монеты, время)
        if not self.current_session_levels:
            return None

        completed_levels = len(self.current_session_levels)
        current_coins = self.session_coins

        if self.session_start_time:
            current_time = time.time() - self.session_start_time
        else:
            current_time = 0

        return {
            'completed_levels': completed_levels,
            'total_coins': current_coins,
            'current_time': current_time
        }
