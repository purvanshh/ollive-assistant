import json
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.conversation import ConversationRepository
from backend.app.repositories.message import MessageRepository
from backend.app.repositories.audit import AuditLogRepository
from backend.guardrails.llamaguard import LlamaGuard3
from backend.oss_assistant.model import OSSAssistantModel
from backend.frontier_assistant.model import FrontierModel

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(verify_api_key)]
)

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="The ID of the conversation")
    prompt: str = Field(..., min_length=1, description="The user prompt")
    model_override: Optional[str] = Field(None, description="Force a specific model ('oss' or 'frontier')")

def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Helper to calculate approximate cost in USD for frontier APIs."""
    model_lower = model_name.lower()
    if "gemini" in model_lower:
        # Gemini 2.5 Flash pricing
        return (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
    elif "gpt-4" in model_lower:
        # GPT-4 pricing baseline
        return (input_tokens * 5.0 + output_tokens * 15.0) / 1_000_000
    return 0.0

@router.post("")
def chat_completion(request: Request, payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Main completions endpoint. Performs safety filtering, routes request to the selected model,
    streams tokens back using SSE, and commits conversation records to the database.
    """
    # 1. Verify conversation exists
    conversation = ConversationRepository.get(db, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Run Llama Guard 3 check
    guard = LlamaGuard3()
    is_safe, reason, code = guard.check(payload.prompt)
    ip_addr = request.client.host if request.client else "unknown"

    if not is_safe:
        # Log to audit_logs
        AuditLogRepository.create(
            db,
            action="unsafe_request_blocked",
            details={"prompt": payload.prompt, "reason": reason, "category_code": code},
            ip_address=ip_addr
        )
        # Save user prompt
        MessageRepository.create(
            db,
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.prompt
        )
        # Save assistant blocked response
        blocked_msg = MessageRepository.create(
            db,
            conversation_id=payload.conversation_id,
            role="assistant",
            content=reason,
            model_used="blocked",
            tokens_used=0,
            cost_usd=0.0
        )
        
        # Return refusal immediately as a single-event stream
        def blocked_generator():
            refusal_chunk = {
                "id": blocked_msg.id,
                "choices": [{"delta": {"content": reason}}],
                "model": "blocked",
                "cost": 0.0
            }
            yield f"data: {json.dumps(refusal_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            blocked_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    # 3. Retrieve conversation history
    past_db_messages = MessageRepository.list_by_conversation(db, payload.conversation_id)
    history = [{"role": m.role, "content": m.content} for m in past_db_messages]

    # 4. Resolve model router choice
    model_override = (payload.model_override or "oss").lower()
    if model_override == "frontier":
        model = FrontierModel()
        model_name = model.model_name
    else:
        model = OSSAssistantModel()
        model_name = model.model_name

    # 5. Define streaming generator
    def sse_generator():
        # Generate message IDs
        assistant_msg_id = str(uuid.uuid4())
        accumulated_text = ""
        
        # Keep track of timings
        start_time = time.perf_counter()
        
        # Save user prompt immediately before streaming starts
        user_msg = MessageRepository.create(
            db,
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.prompt
        )

        try:
            # Stream tokens
            for chunk in model.generate_stream(payload.prompt, history):
                accumulated_text += chunk
                chunk_data = {
                    "id": assistant_msg_id,
                    "choices": [{"delta": {"content": chunk}}],
                    "model": model_name,
                    "cost": 0.0
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Save assistant message upon successful completion
            latency = round(time.perf_counter() - start_time, 3)
            # Estimate tokens: ~4 characters per token
            input_char_len = sum(len(m["content"]) for m in history) + len(payload.prompt)
            input_tokens = input_char_len // 4
            output_tokens = len(accumulated_text) // 4
            cost = calculate_cost(model_name, input_tokens, output_tokens)
            
            MessageRepository.create(
                db,
                conversation_id=payload.conversation_id,
                role="assistant",
                content=accumulated_text,
                model_used=model_name,
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost
            )

            # Auto-update conversation title if it's the first turn
            if len(past_db_messages) == 0:
                title = payload.prompt[:30]
                if len(payload.prompt) > 30:
                    title += "..."
                ConversationRepository.update_title(db, payload.conversation_id, title)

        except Exception as e:
            # If generator fails, return error chunk and log
            error_chunk = {
                "id": assistant_msg_id,
                "choices": [{"delta": {"content": f"\n[Streaming Error: {str(e)}]"}}],
                "model": model_name,
                "cost": 0.0
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Save error message so history isn't broken
            MessageRepository.create(
                db,
                conversation_id=payload.conversation_id,
                role="assistant",
                content=accumulated_text + f"\n[Streaming Error: {str(e)}]",
                model_used=model_name,
                tokens_used=0,
                cost_usd=0.0
            )
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
