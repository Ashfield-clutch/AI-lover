import json
from datetime import datetime
from config import DATABASE_FILE
import sqlite3
import numpy as np

class PersonalityLearner:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 创建用户兴趣表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interests (
            user_id INTEGER PRIMARY KEY,
            interests TEXT,
            last_updated TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # 创建用户互动模式表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS interaction_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pattern_type TEXT,
            frequency INTEGER,
            last_occurrence TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # 创建用户偏好表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences_learned (
            user_id INTEGER PRIMARY KEY,
            preferred_topics TEXT,
            preferred_style TEXT,
            preferred_time TEXT,
            last_updated TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def update_interests(self, user_id, message):
        """更新用户兴趣"""
        cursor = self.conn.cursor()
        
        # 获取现有兴趣
        cursor.execute('SELECT interests FROM user_interests WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            interests = json.loads(result[0])
        else:
            interests = {
                "topics": {},
                "keywords": {},
                "emotions": {}
            }
        
        # 分析消息中的关键词和主题
        keywords = self._extract_keywords(message)
        for keyword in keywords:
            interests["keywords"][keyword] = interests["keywords"].get(keyword, 0) + 1
        
        # 更新数据库
        cursor.execute('''
        INSERT OR REPLACE INTO user_interests (user_id, interests, last_updated)
        VALUES (?, ?, ?)
        ''', (user_id, json.dumps(interests), datetime.now()))
        self.conn.commit()
    
    def update_interaction_pattern(self, user_id, pattern_type):
        """更新用户互动模式"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        INSERT INTO interaction_patterns (user_id, pattern_type, frequency, last_occurrence)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id, pattern_type) DO UPDATE SET
        frequency = frequency + 1,
        last_occurrence = ?
        ''', (user_id, pattern_type, datetime.now(), datetime.now()))
        self.conn.commit()
    
    def get_user_profile(self, user_id):
        """获取用户画像"""
        cursor = self.conn.cursor()
        
        # 获取兴趣
        cursor.execute('SELECT interests FROM user_interests WHERE user_id = ?', (user_id,))
        interests_result = cursor.fetchone()
        interests = json.loads(interests_result[0]) if interests_result else {"topics": {}, "keywords": {}, "emotions": {}}
        
        # 获取互动模式
        cursor.execute('''
        SELECT pattern_type, frequency 
        FROM interaction_patterns 
        WHERE user_id = ? 
        ORDER BY frequency DESC 
        LIMIT 5
        ''', (user_id,))
        patterns = cursor.fetchall()
        
        # 获取偏好
        cursor.execute('SELECT * FROM user_preferences_learned WHERE user_id = ?', (user_id,))
        preferences = cursor.fetchone()
        
        return {
            "interests": interests,
            "patterns": patterns,
            "preferences": preferences
        }
    
    def _extract_keywords(self, text):
        """提取文本中的关键词"""
        # 这里可以使用更复杂的NLP方法
        # 现在简单实现，按空格分割
        return text.split()
    
    def update_preferences(self, user_id, interaction_data):
        """更新用户偏好"""
        cursor = self.conn.cursor()
        
        # 获取现有偏好
        cursor.execute('SELECT * FROM user_preferences_learned WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            preferences = {
                "preferred_topics": json.loads(result[1]),
                "preferred_style": json.loads(result[2]),
                "preferred_time": json.loads(result[3])
            }
        else:
            preferences = {
                "preferred_topics": {},
                "preferred_style": {},
                "preferred_time": {}
            }
        
        # 更新偏好
        current_hour = datetime.now().hour
        time_period = self._get_time_period(current_hour)
        
        preferences["preferred_time"][time_period] = preferences["preferred_time"].get(time_period, 0) + 1
        
        # 更新数据库
        cursor.execute('''
        INSERT OR REPLACE INTO user_preferences_learned 
        (user_id, preferred_topics, preferred_style, preferred_time, last_updated)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            json.dumps(preferences["preferred_topics"]),
            json.dumps(preferences["preferred_style"]),
            json.dumps(preferences["preferred_time"]),
            datetime.now()
        ))
        self.conn.commit()
    
    def _get_time_period(self, hour):
        """获取时间段"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def get_personalized_prompt(self, user_id):
        """获取个性化提示"""
        profile = self.get_user_profile(user_id)
        
        # 构建个性化提示
        prompt_parts = []
        
        # 添加兴趣相关提示
        if profile["interests"]["keywords"]:
            top_keywords = sorted(
                profile["interests"]["keywords"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            prompt_parts.append(f"主人对{', '.join(k[0] for k in top_keywords)}很感兴趣呢~")
        
        # 添加时间相关提示
        current_hour = datetime.now().hour
        time_period = self._get_time_period(current_hour)
        if profile["preferences"] and time_period in profile["preferences"][2]:
            prompt_parts.append(f"现在是{time_period}，主人通常这个时候都会来找我聊天呢~")
        
        return " ".join(prompt_parts) 