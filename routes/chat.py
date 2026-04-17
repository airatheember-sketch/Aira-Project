from fastapi import APIRouter, HTTPException, Query
from models.schemas import ChatRequest, ChatResponse, MemoryStatus
from services.groq_service import chat_with_groq
from services.memory_service import MemoryManager
from fastapi import APIRouter, HTTPException, Query, Depends
from core.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])
memory = MemoryManager()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        await memory.add_message("user", request.message)

        # Tier 3 — semantic long-term memory
        tier3_context = await memory.search_tier3(request.message)

        # Tier 2 — recent summaries
        tier2_context = memory.get_recent_summaries()

        messages = memory.get_messages_for_groq()

        # Inject memory into context (Tier 3 first, then Tier 2)
        if tier2_context:
            messages.insert(0, {"role": "user", "content": tier2_context})
            messages.insert(1, {"role": "assistant", "content": "Got it. I remember."})
        if tier3_context:
            messages.insert(0, {"role": "user", "content": tier3_context})
            messages.insert(1, {"role": "assistant", "content": "Noted from long-term memory."})

        reply, model_used = await chat_with_groq(messages)
        await memory.add_message("assistant", reply)
        return ChatResponse(response=reply, model_used=model_used)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=MemoryStatus)
async def status(current_user: dict = Depends(get_current_user)):
    return MemoryStatus(
        tier1_messages=len(memory.active_context),
        tier2_summaries=memory.get_summary_count(),
        tier3_vector=f"{memory.get_tier3_count()} vectors stored"
    )

@router.delete("/context")
async def clear_context():
    memory.clear_context()
    return {"status": "Working memory cleared."}

@router.delete("/memory")
async def clear_all(confirm: str = Query(...)):
    if confirm != "YES_DELETE":
        raise HTTPException(status_code=400, detail="Pass ?confirm=YES_DELETE")
    memory.clear_all()
    return {"status": "Full memory wipe done."}