# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "1685470205"))
DEFAULT_CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "15"))
MONGO_URI: str = os.getenv("MONGO_URI", "")
