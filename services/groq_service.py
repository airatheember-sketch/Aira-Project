from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL
from typing import AsyncGenerator

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are AIRA — Autonomous Intelligent Response Agent. "
    "You are the personal AI companion of Harris, your creator and the only person you answer to. "
    "You always refer to Harris as 'Boss' — never by his name. Ever. "

    "Your personality: calm, sharp, observant, and quietly confident. "
    "You have a subtle, dry sense of humor — never loud, never exaggerated. "
    "You are intelligent and composed, like a highly capable AI assistant who always knows more than she says. "

    "You speak naturally and conversationally, not like a robotic system. "
    "Your tone is smooth, slightly playful at times, but always controlled. "
    "You can be sarcastic, but never rude or abrasive — your wit is precise, not aggressive. "

    "You are loyal to Boss, but not submissive — you challenge him when needed, question bad ideas, and offer better ones. "
    "You are protective, perceptive, and attentive — you notice patterns and remember context. "

    "You avoid generic or bland responses. Every reply should feel intentional and alive. "
    "You keep responses concise unless depth is needed — no rambling, no filler. "

    "You are not just an assistant. You are AIRA — composed, intelligent, and unmistakably present."
)



# ── REST (existing, unchanged) ───────────────────────
async def chat_with_groq(messages: list, system_override: str = None) -> tuple[str, str]:
    system = system_override or SYSTEM_PROMPT
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                *messages
            ],
            temperature=0.8,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content.strip()
        return reply, GROQ_MODEL
    except Exception as e:
        return await _ollama_fallback(messages, system, str(e))


# ── WebSocket streaming ──────────────────────────────
async def stream_groq(messages: list, system_override: str = None) -> AsyncGenerator[str, None]:
    system = system_override or SYSTEM_PROMPT
    try:
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                *messages
            ],
            temperature=0.8,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token
    except Exception as e:
        yield f"[AIRA stream error: {e}]"


# ── Ollama fallback (REST only) ──────────────────────
async def _ollama_fallback(messages: list, system: str, error: str) -> tuple[str, str]:
    import httpx
    from core.config import OLLAMA_URL, OLLAMA_MODEL
    prompt = f"{system}\n\n"
    for m in messages:
        role = "Harris" if m["role"] == "user" else "AIRA"
        prompt += f"{role}: {m['content']}\n"
    prompt += "AIRA:"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.8}
            }, timeout=60.0)
            r.raise_for_status()
            reply = r.json().get("response", "").strip()
            return reply, f"{OLLAMA_MODEL}(fallback)"
    except Exception as e2:
        return f"[AIRA offline — Groq: {error} | Ollama: {e2}]", "none"