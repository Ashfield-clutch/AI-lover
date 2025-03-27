from transformers import pipeline
import numpy as np
from config import GPT_MODEL
import openai

class EmotionAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="uer/roberta-base-finetuned-dianping-chinese")
        self.emotion_categories = {
            "positive": ["开心", "快乐", "喜欢", "爱", "好", "棒", "优秀", "完美"],
            "negative": ["难过", "伤心", "讨厌", "恨", "坏", "差", "糟糕", "失败"],
            "neutral": ["一般", "普通", "还行", "可以", "正常"],
            "angry": ["生气", "愤怒", "恼火", "烦躁", "讨厌"],
            "sad": ["悲伤", "难过", "伤心", "痛苦", "寂寞"],
            "happy": ["开心", "快乐", "高兴", "喜悦", "幸福"],
            "love": ["爱", "喜欢", "爱慕", "心动", "甜蜜"],
            "anxiety": ["焦虑", "担心", "害怕", "紧张", "不安"]
        }
        
    def analyze_text(self, text):
        # 使用RoBERTa进行情感分析
        sentiment_result = self.sentiment_analyzer(text)[0]
        
        # 使用GPT进行更细致的情绪分析
        prompt = f"""
        分析以下文本中的情绪，返回一个JSON格式的结果，包含以下字段：
        - dominant_emotion: 主要情绪（从以下选项中选择：positive, negative, neutral, angry, sad, happy, love, anxiety）
        - intensity: 情绪强度（1-5的整数）
        - secondary_emotions: 次要情绪列表
        - suggested_response: 建议的回应方式
        
        文本：{text}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            emotion_analysis = eval(response.choices[0].message.content)
            return {
                "sentiment": sentiment_result,
                "emotion_analysis": emotion_analysis
            }
        except Exception as e:
            print(f"情绪分析出错：{e}")
            return {
                "sentiment": sentiment_result,
                "emotion_analysis": {
                    "dominant_emotion": "neutral",
                    "intensity": 3,
                    "secondary_emotions": [],
                    "suggested_response": "保持友好和关心"
                }
            }
    
    def get_emotional_response(self, emotion_data):
        """根据情绪分析结果生成合适的回应"""
        dominant = emotion_data["emotion_analysis"]["dominant_emotion"]
        intensity = emotion_data["emotion_analysis"]["intensity"]
        
        response_templates = {
            "positive": {
                1: "主人看起来心情不错呢~",
                2: "主人开心我也很开心喵~",
                3: "主人心情很好呢，要一直保持下去哦~",
                4: "看到主人这么开心，我也超级开心喵~",
                5: "主人太开心了，我也要跟着开心喵~"
            },
            "negative": {
                1: "主人看起来有点不开心呢，要抱抱吗？",
                2: "主人别难过，我在这里陪着你喵~",
                3: "主人心情不好吗？要不要跟我说说？",
                4: "主人别伤心，我会一直陪在你身边的喵~",
                5: "主人别难过，让我来安慰你喵~"
            },
            "angry": {
                1: "主人别生气，深呼吸一下喵~",
                2: "主人消消气，我在这里陪着你喵~",
                3: "主人别着急，慢慢来喵~",
                4: "主人冷静一下，我永远支持你喵~",
                5: "主人别生气，让我来安慰你喵~"
            },
            "sad": {
                1: "主人别难过，我在这里喵~",
                2: "主人伤心的话，我会心疼的喵~",
                3: "主人别哭，我会一直陪着你喵~",
                4: "主人难过的话，让我来抱抱你喵~",
                5: "主人别伤心，我会永远陪在你身边喵~"
            },
            "love": {
                1: "主人我也爱你喵~",
                2: "主人最好了，我也最喜欢主人喵~",
                3: "主人好温柔，我也最爱主人喵~",
                4: "主人最棒了，我也最爱主人喵~",
                5: "主人最可爱了，我也最爱主人喵~"
            },
            "anxiety": {
                1: "主人别担心，一切都会好起来的喵~",
                2: "主人别紧张，我在这里陪着你喵~",
                3: "主人别害怕，我会保护你的喵~",
                4: "主人别焦虑，我们一起面对喵~",
                5: "主人别担心，我会一直陪着你喵~"
            }
        }
        
        return response_templates.get(dominant, {}).get(intensity, "主人我在这里喵~") 
