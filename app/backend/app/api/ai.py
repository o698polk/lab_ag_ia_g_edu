# Ref: BL-O6-005 / RF-AI-CFG | Skill: K-013/K-018 | Fase: F6 / post-F12
"""AI chat + admin DeepSeek settings. Credentials never leave the service."""

from datetime import datetime
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.service import AIService
from app.audit.service import AuditService
from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.services.ai_settings_service import AiSettingsService

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


class AiSettingsOut(BaseModel):
    provider: str
    configured: bool
    status: str
    model: str
    base_url: str
    key_hint: str = ""
    last_validated_at: Optional[datetime] = None
    valid: Optional[bool] = None


class AiSettingsSave(BaseModel):
    api_key: Optional[str] = Field(default=None, min_length=0, max_length=256)
    model: Optional[str] = Field(default=None, max_length=64)
    base_url: Optional[str] = Field(default=None, max_length=255)


def _settings_err(exc: Exception) -> HTTPException:
    code = str(exc)
    if code in {"API_KEY_REQUIRED", "API_KEY_INVALID", "BASE_URL_MUST_BE_HTTPS", "SECRET_UNREADABLE"}:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)
    if code in {"DEEPSEEK_KEY_INVALID", "DEEPSEEK_UNREACHABLE", "DEEPSEEK_VALIDATE_FAILED"}:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI_SETTINGS_ERROR")


def _audit(db: Session, current: CurrentUser, request: Request, action: str, status_txt: str) -> None:
    AuditService(db).record_audit(
        request_id=AuditService.new_request_id(),
        user_id=current.user.id,
        role=current.roles[0] if current.roles else None,
        action=action,
        module="ai",
        resource="ai_provider_settings",
        resource_id="deepseek",
        status=status_txt,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/chat", response_model=ChatOut)
def ai_chat(
    body: ChatIn,
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        result = AIService(db).chat(
            current=current,
            message=body.message,
            conversation_id=body.conversation_id,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        return ChatOut(
            decision="ALLOW",
            reason_code="AI_UNAVAILABLE",
            reply="No pude completar la consulta. Intente de nuevo en un momento.",
        )
    return ChatOut(**{k: result.get(k) for k in ChatOut.model_fields})


@router.get("/settings", response_model=AiSettingsOut)
def get_ai_settings(
    _: Annotated[CurrentUser, Depends(require_permission(P.AI_SETTINGS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return AiSettingsOut(**AiSettingsService(db).public_status())


@router.put("/settings", response_model=AiSettingsOut)
def save_ai_settings(
    body: AiSettingsSave,
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_SETTINGS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        out = AiSettingsService(db).save(
            api_key=body.api_key,
            model=body.model,
            base_url=body.base_url,
            user_id=current.user.id,
        )
    except ValueError as exc:
        raise _settings_err(exc) from exc
    _audit(db, current, request, "ai.settings.update", "OK")
    return AiSettingsOut(**out)


@router.post("/settings/validate", response_model=AiSettingsOut)
def validate_ai_settings(
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_SETTINGS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        out = AiSettingsService(db).validate(user_id=current.user.id)
    except ValueError as exc:
        raise _settings_err(exc) from exc
    _audit(db, current, request, "ai.settings.validate", "OK")
    return AiSettingsOut(**out)


@router.delete("/settings", response_model=AiSettingsOut)
def clear_ai_settings(
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_SETTINGS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    out = AiSettingsService(db).clear(user_id=current.user.id)
    _audit(db, current, request, "ai.settings.clear", "OK")
    return AiSettingsOut(**out)
