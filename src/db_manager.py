import sqlite3
import datetime
import os

os.makedirs('data', exist_ok=True)
DB_PATH = 'data/bot_database.db'

def init_db() -> None:
    """Initializes the SQLite database and schemas."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mmr_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                r6_name TEXT NOT NULL,
                date TEXT NOT NULL,
                mmr INTEGER NOT NULL,
                rank TEXT NOT NULL
            )
        ''')
        print("Database Systems: ONLINE")

def log_mmr(r6_name: str, mmr: int, rank: str) -> None:
    """Upserts a daily MMR snapshot for a given player."""
    today = datetime.date.today().isoformat()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM mmr_history WHERE r6_name = ? AND date = ?', (r6_name, today))
        record = cursor.fetchone()
        
        if record:
            cursor.execute('''
                UPDATE mmr_history 
                SET mmr = ?, rank = ? 
                WHERE r6_name = ? AND date = ?
            ''', (mmr, rank, r6_name, today))
        else:
            cursor.execute('''
                INSERT INTO mmr_history (r6_name, date, mmr, rank) 
                VALUES (?, ?, ?, ?)
            ''', (r6_name, today, mmr, rank))