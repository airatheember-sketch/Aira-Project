import httpx
from core.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_EN, ELEVENLABS_VOICE_UR

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
MODEL_ID = "eleven_multilingual_v2"  # supports English + Urdu natively

VOICE_MAP = {
    "en": ELEVENLABS_VOICE_EN,
    "ur": ELEVENLABS_VOICE_UR,
}


async def text_to_speech(text: str, lang: str = "en") -> bytes:
    """
    Convert text to speech via ElevenLabs API.
    Returns raw MP3 bytes.
    lang: 'en' → Alisha | 'ur' → Aisha
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in .env")

    voice_id = VOICE_MAP.get(lang, VOICE_MAP["en"])
    text = text.strip()[:2000]

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.4,           # lower = more expressive, fun
            "similarity_boost": 0.75,   # closeness to original voice
            "style": 0.35,              # energy and expressiveness
            "use_speaker_boost": True
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ELEVENLABS_API_URL}/{voice_id}",
            headers=headers,
            json=payload,
            timeout=30.0
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"ElevenLabs error {response.status_code}: {response.text}"
            )

        return response.content  # raw MP3 bytes