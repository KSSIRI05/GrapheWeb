import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "graphcrawler_db")

# GROQ (pas Grok)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 8000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

# Crawler
MAX_PAGES = 50
TIMEOUT = 10