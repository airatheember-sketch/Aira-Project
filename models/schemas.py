from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ── Auth ────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ── Chat ────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    model_used: str

# ── Memory ──────────────────────────────────────────
class MemoryStatus(BaseModel):
    tier1_messages: int
    tier2_summaries: int
    tier3_vector: str