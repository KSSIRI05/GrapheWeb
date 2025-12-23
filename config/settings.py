import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "web_crawler_db")

# Claude
# Gemini (au lieu de Claude)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4000))
MODEL = "claude-sonnet-4-20250514"

# Crawler
MAX_PAGES = 50
TIMEOUT = 10