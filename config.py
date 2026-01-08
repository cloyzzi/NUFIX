import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    WALLET_TON = os.getenv("WALLET_TON")
    TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_numbers.db")
    
    # TON Center API
    TONCENTER_API_URL = "https://toncenter.com/api/v2/"
    
    # Pizza design emojis
    EMOJIS = {
        "pizza": "🍕",
        "money": "💰",
        "phone": "📱",
        "admin": "👑",
        "buy": "🛒",
        "balance": "💳",
        "check": "✅",
        "cross": "❌",
        "clock": "⏰",
        "lock": "🔒",
        "unlock": "🔓",
        "ton": "💎"
    }