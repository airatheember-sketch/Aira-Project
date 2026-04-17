from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from core.auth import get_current_user
from services.stt_service import transcribe_audio

router = APIRouter(prefix="/stt", tags=["stt"])


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    lang: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe uploaded audio file using Whisper.
    
    - audio: audio file (webm, wav, mp3, mp4)
    - lang: optional language hint ('en' or 'ur'). If omitted, Whisper auto-detects.
    
    Returns: { text, language, confidence }
    """
    # Validate file type
    allowed_types = {
        "audio/webm", "audio/wav", "audio/mpeg",
        "audio/mp4", "audio/ogg", "video/webm"  # browser MediaRecorder sends video/webm
    }
    if audio.content_type and audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {audio.content_type}"
        )

    # Enforce size limit — 10MB max
    audio_bytes = await audio.read()
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio file too small or empty")

    try:
        result = await transcribe_audio(audio_bytes, lang=lang)

        if not result["text"]:
            raise HTTPException(status_code=422, detail="No speech detected in audio")

        return result

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")