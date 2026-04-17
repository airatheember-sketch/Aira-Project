from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Literal
from core.auth import get_current_user
from services.tts_service import text_to_speech

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    lang: Literal["en", "ur"] = "en"


@router.post("/speak")
async def speak(
    payload: TTSRequest,
    current_user: dict = Depends(get_current_user)
):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if len(payload.text) > 2000:
        raise HTTPException(status_code=400, detail="Text too long (max 2000 chars)")
    try:
        audio_bytes = await text_to_speech(payload.text, payload.lang)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=aira.mp3"}
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))