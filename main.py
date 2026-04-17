from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.config import GROQ_API_KEY
from core.database import init_db, health_check
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from routes.ws import router as ws_router
from routes.tts import router as tts_router
from routes.stt import router as stt_router
from routes.wake import router as wake_router
from routes.news import router as news_router
import os

app = FastAPI(title="AIRA", version="1.0.0")

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ws_router)
app.include_router(tts_router)
app.include_router(stt_router)
app.include_router(wake_router)
app.include_router(news_router)

# ── Serve PWA files ───────────────────────────────────────────────────────────
# NOTE: These explicit routes must come BEFORE any catch-all StaticFiles mount.
# FastAPI matches routes top-down — order matters.

@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    # Service worker must be served from root scope with correct content-type
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"}
    )

@app.get("/icon-192.png", include_in_schema=False)
async def icon_192():
    return FileResponse("static/icon-192.png", media_type="image/png")

@app.get("/icon-512.png", include_in_schema=False)
async def icon_512():
    return FileResponse("static/icon-512.png", media_type="image/png")

@app.get("/health")
async def health():
    return {
        "status": "online",
        "groq": "configured" if GROQ_API_KEY else "missing",
        "db": "connected" if health_check() else "error"
    }

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")