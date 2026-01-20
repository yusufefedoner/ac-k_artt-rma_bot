import sqlite3
from datetime import datetime
from config import DATABASE
import os
import cv2


class DatabaseManager:
    def __init__(self, database):
        self.database = database

    # ================= TABLOLAR =================
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT,
                bonus INTEGER DEFAULT 0
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT
            )
            """)
            conn.commit()

    # ================= USERS =================
    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, user_name) VALUES (?, ?)",
                (user_id, user_name)
            )

    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users")
            return [x[0] for x in cur.fetchall()]

    # ================= BONUS =================
    def add_bonus(self, user_id, amount):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(
                "UPDATE users SET bonus = bonus + ? WHERE user_id = ?",
                (amount, user_id)
            )

    def get_bonus(self, user_id):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute("SELECT bonus FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    # ================= PRIZES =================
    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(
                "INSERT INTO prizes (image) VALUES (?)",
                data
            )

    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT prize_id, image FROM prizes WHERE used = 0 ORDER BY RANDOM()"
            )
            return cur.fetchone()

    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(
                "UPDATE prizes SET used = 1 WHERE prize_id = ?",
                (prize_id,)
            )

    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute(
            "SELECT image FROM prizes WHERE prize_id = ?",
            (prize_id,)
        )
        img = cur.fetchone()[0]
        conn.close()
        return img

    # ================= WINNER =================
    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM winners WHERE user_id=? AND prize_id=?",
            (user_id, prize_id)
        )
        if cur.fetchone():
            conn.close()
            return False

        cur.execute(
            "INSERT INTO winners VALUES (?,?,?)",
            (user_id, prize_id, win_time)
        )
        conn.commit()
        conn.close()
        return True


def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    blurred = cv2.GaussianBlur(image, (15, 15), 0)
    small = cv2.resize(blurred, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixel = cv2.resize(
        small,
        (image.shape[1], image.shape[0]),
        interpolation=cv2.INTER_NEAREST
    )
    cv2.imwrite(f'hidden_img/{img_name}', pixel)
