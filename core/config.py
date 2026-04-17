from dotenv import load_dotenv
from pathlib import Path
import os

# Explicitly load .env from project root — fixes Windows path issues
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
GROQ_MODEL = os.getenv("GROQ_MODEL")
DB_PATH = os.getenv("DB_PATH", "data/aira.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# ── ElevenLabs TTS ────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_EN = os.getenv("ELEVENLABS_VOICE_EN", "EXAVITQu4vr4xnSDxMaL")
ELEVENLABS_VOICE_UR = os.getenv("ELEVENLABS_VOICE_UR", "EXAVITQu4vr4xnSDxMaL")