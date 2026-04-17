import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.auth import decode_token
from services.connection_manager import manager
from services.groq_service import stream_groq
from services.memory_service import MemoryManager

router = APIRouter()
memory = MemoryManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(None)):
    if not token:
        # FastAPI might return 403 if Query(...) fails, so we make it optional 
        # and handle the missing case manually for better control.
        await websocket.close(code=1008)
        return

    # ── Auth ────────────────────────────────────────
    try:
        payload = decode_token(token)
        user_id = payload["sub"]
    except Exception as e:
        print(f"[WS AUTH ERROR] {str(e)}")
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                parsed = json.loads(data)
                user_message = parsed.get("message", "").strip()
            except Exception:
                user_message = data.strip()

            if not user_message:
                continue

            # ── Memory pipeline ──────────────────────
            await memory.add_message("user", user_message)
            tier3_context = await memory.search_tier3(user_message)
            tier2_context = memory.get_recent_summaries()
            messages = memory.get_messages_for_groq()

            if tier2_context:
                messages.insert(0, {"role": "user", "content": tier2_context})
                messages.insert(1, {"role": "assistant", "content": "Got it. I remember."})
            if tier3_context:
                messages.insert(0, {"role": "user", "content": tier3_context})
                messages.insert(1, {"role": "assistant", "content": "Noted from long-term memory."})

            # ── Stream tokens ────────────────────────
            full_reply = ""
            async for token in stream_groq(messages):
                full_reply += token
                await websocket.send_json({"type": "token", "content": token})

            await memory.add_message("assistant", full_reply)
            await websocket.send_json({"type": "done", "model": "groq"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
        except Exception:
            pass
        manager.disconnect(user_id)