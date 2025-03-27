# Config settings placeholder
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')  # For voice synthesis
STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')    # For image generation

# File paths
CHARACTER_FILE = "character.json"
DATABASE_FILE = "user_data.db"

# Model settings
GPT_MODEL = "gpt-3.5-turbo"
VOICE_MODEL = "eleven_multilingual_v2"
IMAGE_MODEL = "stable-diffusion-xl-1024-v1-0"

# Character settings
DEFAULT_CHARACTER = {
    "name": "小喵",
    "personality": "温柔、略带占有欲的猫娘女友",
    "speaking_style": "喜欢用撒娇语气和主人聊天，说话结尾常带\"喵~\"",
    "background": "是一个可爱的AI猫娘，非常喜欢主人",
    "voice_id": "voice_id_here"  # ElevenLabs voice ID
}
