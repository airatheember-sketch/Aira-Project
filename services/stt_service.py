import os
import tempfile
import whisper

# Load model once at startup — 'base' is fast and supports 99 languages including Urdu
# Upgrade to 'small' or 'medium' on VPS for better accuracy
_model = None


def get_model():
    global _model
    if _model is None:
        print("[STT] Loading Whisper base model...")
        _model = whisper.load_model("base")
        print("[STT] Whisper model loaded.")
    return _model


async def transcribe_audio(audio_bytes: bytes, lang: str = None) -> dict:
    """
    Transcribe audio bytes using Whisper.
    
    Args:
        audio_bytes: Raw audio bytes (webm, mp4, wav, mp3 — all supported)
        lang: Optional language hint e.g. 'en', 'ur'. 
              If None, Whisper auto-detects the language.
    
    Returns:
        {
            "text": "transcribed text",
            "language": "detected or provided language",
            "confidence": 0.0 - 1.0
        }
    """
    model = get_model()

    # Write to a temp file — Whisper requires a file path not raw bytes
    suffix = ".webm"  # browser MediaRecorder default
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        options = {
            "task": "transcribe",
            "fp16": False,  # fp16 off — safer for CPU-only machines
        }

        # If language is provided, pass it — improves accuracy significantly
        # Whisper uses ISO 639-1 codes: 'en', 'ur', etc.
        if lang and lang in _supported_languages():
            options["language"] = lang

        result = model.transcribe(tmp_path, **options)

        return {
            "text": result["text"].strip(),
            "language": result.get("language", lang or "unknown"),
            "confidence": _avg_confidence(result)
        }

    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _avg_confidence(result: dict) -> float:
    """Extract average confidence from Whisper segments."""
    segments = result.get("segments", [])
    if not segments:
        return 0.0
    scores = [abs(s.get("avg_logprob", 0)) for s in segments]
    # Convert log probability to approximate confidence (0-1)
    avg_logprob = sum(scores) / len(scores)
    confidence = max(0.0, min(1.0, 1.0 - avg_logprob))
    return round(confidence, 2)


def _supported_languages() -> set:
    """Languages we explicitly support for the lang hint."""
    return {"en", "ur", "hi", "ar"}