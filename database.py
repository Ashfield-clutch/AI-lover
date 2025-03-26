import sqlite3
import json
from datetime import datetime
from config import DATABASE_FILE

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create users table with indexes and constraints
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_interaction TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            settings TEXT DEFAULT '{}'
        )
        ''')

        # Create chat_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            role TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Create user_preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            voice_enabled BOOLEAN DEFAULT 1,
            image_enabled BOOLEAN DEFAULT 1,
            personality TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, created_at, last_interaction)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now(), datetime.now()))
        self.conn.commit()

    def add_message(self, user_id, message, role):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO chat_history (user_id, message, role, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (user_id, message, role, datetime.now()))
        self.conn.commit()

    def get_chat_history(self, user_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT message, role FROM chat_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

    def update_user_preferences(self, user_id, voice_enabled=None, image_enabled=None, personality=None):
        cursor = self.conn.cursor()
        updates = []
        values = []
        
        if voice_enabled is not None:
            updates.append("voice_enabled = ?")
            values.append(voice_enabled)
        if image_enabled is not None:
            updates.append("image_enabled = ?")
            values.append(image_enabled)
        if personality is not None:
            updates.append("personality = ?")
            values.append(personality)
            
        if updates:
            values.append(user_id)
            query = f'''
            INSERT INTO user_preferences (user_id, {", ".join(updates)})
            VALUES (?, {", ".join(["?" for _ in updates])})
            ON CONFLICT(user_id) DO UPDATE SET {", ".join(updates)}
            '''
            cursor.execute(query, values)
            self.conn.commit()

    def get_user_preferences(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()       
    