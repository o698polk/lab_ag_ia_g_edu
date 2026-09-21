# Ref: BL-O6-005 | Skill: K-013/K-018 | Fase: F6
"""AI chat API — proposes tools; Gateway/PDP enforce."""

from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.service import AIService
from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[int] = None


class ChatOut(BaseModel):
    decision: str
    reason_code: str
    policy_id: Optional[str] = None
    conversation_id: Optional[int] = None
    reply: str
    proposal: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatOut)
def ai_chat(
    body: ChatIn,
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    result = AIService(db).chat(
        current=current,
        message=body.message,
        conversation_id=body.conversation_id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ChatOut(**{k: result.get(k) for k in ChatOut.model_fields})
