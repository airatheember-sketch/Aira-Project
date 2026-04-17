from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.auth import decode_token
from services.wake_service import process_audio_chunk, reset_wake_model

router = APIRouter(tags=["wake"])


@router.websocket("/ws/wake")
async def wake_word_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for wake word detection.
    
    Flow:
      1. Browser connects with JWT token
      2. Browser streams raw PCM audio chunks (16kHz, 16-bit, mono)
      3. Server runs openWakeWord on each chunk
      4. On detection → sends {"event": "wake_detected"} to client
      5. Client stops streaming, starts recording command
    
    Browser sends: raw PCM bytes
    Server sends:  JSON messages
      - {"event": "listening"}        — connection confirmed
      - {"event": "wake_detected"}    — wake word heard, start command
      - {"event": "error", "detail"}  — something went wrong
    """

    # Validate JWT before accepting connection
    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_json({"event": "listening"})
    print(f"[Wake WS] Client connected: {payload.get('sub')}")

    reset_wake_model()  # clean state for new session

    try:
        while True:
            # Receive raw PCM audio chunk from browser
            audio_chunk = await websocket.receive_bytes()

            if not audio_chunk:
                continue

            # Run wake word detection
            detected = await process_audio_chunk(audio_chunk)

            if detected:
                await websocket.send_json({"event": "wake_detected"})
                print("[Wake WS] Wake word detected — notified client")
                reset_wake_model()  # reset after detection to avoid repeat triggers

    except WebSocketDisconnect:
        print("[Wake WS] Client disconnected")
    except Exception as e:
        print(f"[Wake WS] Error: {e}")
        try:
            await websocket.send_json({"event": "error", "detail": str(e)})
        except Exception:
            pass