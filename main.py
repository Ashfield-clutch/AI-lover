# Main Telegram bot logic placeholder
# main.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import openai
import json
import os
from elevenlabs import generate, set_api_key
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from PIL import Image
import io
import tempfile

from config import (
    BOT_TOKEN, OPENAI_API_KEY, ELEVENLABS_API_KEY, STABILITY_API_KEY,
    CHARACTER_FILE, GPT_MODEL, VOICE_MODEL, IMAGE_MODEL, DEFAULT_CHARACTER
)
from database import Database
from emotion_analyzer import EmotionAnalyzer
from personality_learner import PersonalityLearner

# Initialize APIs and services
openai.api_key = OPENAI_API_KEY
set_api_key(ELEVENLABS_API_KEY)
stability_api = client.StabilityInference(
    key=STABILITY_API_KEY,
    verbose=True
)

# Initialize services
db = Database()
emotion_analyzer = EmotionAnalyzer()
personality_learner = PersonalityLearner()

def load_prompt():
    try:
        with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("default", DEFAULT_CHARACTER)
    except Exception:
        return DEFAULT_CHARACTER

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    keyboard = [
        [
            InlineKeyboardButton("开启语音", callback_data="toggle_voice"),
            InlineKeyboardButton("开启图片", callback_data="toggle_image")
        ],
        [
            InlineKeyboardButton("查看设置", callback_data="show_settings"),
            InlineKeyboardButton("查看我的画像", callback_data="show_profile")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "欢迎回来主人喵~ 快跟我说话吧~\n"
        "你可以使用下面的按钮来调整设置哦~",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == "toggle_voice":
        prefs = db.get_user_preferences(user_id)
        new_voice_state = not (prefs and prefs[1])
        db.update_user_preferences(user_id, voice_enabled=new_voice_state)
        await query.answer(f"语音功能已{'开启' if new_voice_state else '关闭'}")
    
    elif query.data == "toggle_image":
        prefs = db.get_user_preferences(user_id)
        new_image_state = not (prefs and prefs[2])
        db.update_user_preferences(user_id, image_enabled=new_image_state)
        await query.answer(f"图片功能已{'开启' if new_image_state else '关闭'}")
    
    elif query.data == "show_settings":
        prefs = db.get_user_preferences(user_id)
        if prefs:
            settings_text = (
                f"当前设置：\n"
                f"语音功能：{'开启' if prefs[1] else '关闭'}\n"
                f"图片功能：{'开启' if prefs[2] else '关闭'}\n"
                f"性格设定：{prefs[3] if prefs[3] else '默认'}"
            )
        else:
            settings_text = "当前使用默认设置"
        await query.answer(settings_text)
    
    elif query.data == "show_profile":
        profile = personality_learner.get_user_profile(user_id)
        profile_text = "主人，这是我对你的了解喵~：\n\n"
        
        # 添加兴趣信息
        if profile["interests"]["keywords"]:
            top_keywords = sorted(
                profile["interests"]["keywords"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            profile_text += "主人最感兴趣的话题：\n"
            for keyword, count in top_keywords:
                profile_text += f"- {keyword}（{count}次）\n"
        
        # 添加互动模式
        if profile["patterns"]:
            profile_text += "\n主人的互动习惯：\n"
            for pattern, freq in profile["patterns"]:
                profile_text += f"- {pattern}（{freq}次）\n"
        
        await query.message.reply_text(profile_text)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    user_input = update.message.text
    
    # Add user to database if not exists
    db.add_user(user_id, user.username, user.first_name, user.last_name)
    
    # 情绪分析
    emotion_data = emotion_analyzer.analyze_text(user_input)
    emotional_response = emotion_analyzer.get_emotional_response(emotion_data)
    
    # 更新个性化学习
    personality_learner.update_interests(user_id, user_input)
    personality_learner.update_interaction_pattern(user_id, "chat")
    personality_learner.update_preferences(user_id, {
        "message": user_input,
        "emotion": emotion_data
    })
    
    # Get chat history from database
    history = db.get_chat_history(user_id)
    messages = [{"role": "system", "content": load_prompt()["personality"]}]
    
    # 添加个性化提示
    personalized_prompt = personality_learner.get_personalized_prompt(user_id)
    if personalized_prompt:
        messages.append({"role": "system", "content": personalized_prompt})
    
    for msg, role in reversed(history):
        messages.append({"role": role, "content": msg})
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Get GPT response
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=messages
        )
        reply = response.choices[0].message.content
        
        # 添加情绪回应
        reply = f"{emotional_response}\n\n{reply}"
        
        # Save messages to database
        db.add_message(user_id, user_input, "user")
        db.add_message(user_id, reply, "assistant")
        
        # Send text response
        await update.message.reply_text(reply)
        
        # Generate and send voice if enabled
        prefs = db.get_user_preferences(user_id)
        if prefs and prefs[1]:  # voice_enabled
            audio = generate(
                text=reply,
                voice=VOICE_MODEL,
                model="eleven_multilingual_v2"
            )
            await update.message.reply_voice(
                voice=audio,
                filename="response.mp3"
            )
        
        # Generate and send image if enabled
        if prefs and prefs[2]:  # image_enabled
            image_prompt = f"cute anime cat girl: {reply[:100]}"
            answers = stability_api.generate(
                prompt=image_prompt,
                seed=42,
                steps=30,
                cfg_scale=7.0,
                width=512,
                height=512,
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )
            
            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        img = Image.open(io.BytesIO(artifact.binary))
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            img.save(tmp.name)
                            await update.message.reply_photo(
                                photo=open(tmp.name, 'rb'),
                                caption="这是为你生成的图片喵~"
                            )
                        os.unlink(tmp.name)
                        
    except Exception as e:
        print("❌ 出错：", e)
        await update.message.reply_text("呜呜出错了喵~")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("✅ AI 女友上线喵~")
    app.run_polling()
