import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Bingo Backend")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
ROOM_CODE_LENGTH = int(os.getenv("ROOM_CODE_LENGTH", "6"))

# CORS origins: comma-separated list
ORIGINS = [o.strip() for o in os.getenv("ORIGINS", "*").split(",")]
