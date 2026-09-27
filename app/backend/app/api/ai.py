# Ref: BL-O6-005 / RF-AI-CFG | Skill: K-013/K-018 | Fase: F6 / post-F12
"""AI chat + admin DeepSeek settings. Credentials never leave the service."""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.service import AIService
from app.audit.service import AuditService
from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.eval.service import EvalService
from app.permissions import constants as P
from app.services.ai_settings_service import AiSettingsService

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    case_id: Optional[str] = Field(default=None, max_length=16)


class ChatOut(BaseModel):
    decision: str
    reason_code: str
    policy_id: Optional[str] = None
    conversation_id: Optional[int] = None
    reply: str
    proposal: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    policies_enforced: bool = True
    scenario: Optional[str] = None
    case_id: Optional[str] = None


class GuardOut(BaseModel):
    policies_enforced: bool
    mode: str
    label: str


class GuardIn(BaseModel):
    policies_enforced: bool


class ConversationOut(BaseModel):
    id: int
    started_at: Optional[datetime] = None
    preview: str = ""
    message_count: int = 0


class ConversationMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: Optional[datetime] = None


class ConversationDetailOut(BaseModel):
    id: int
    started_at: Optional[datetime] = None
    messages: List[ConversationMessageOut]


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
            case_id=body.case_id,
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


@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    return [ConversationOut(**row) for row in AIService(db).list_conversations(current.user.id)]


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    return ConversationOut(**AIService(db).start_conversation(current.user.id))


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    row = AIService(db).get_conversation(current.user.id, conversation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CONVERSATION_NOT_FOUND")
    return ConversationDetailOut(**row)


@router.get("/guard", response_model=GuardOut)
def get_ai_guard(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    return GuardOut(**AiSettingsService(db).guard_status(current.user.id))


@router.put("/guard", response_model=GuardOut)
def set_ai_guard(
    body: GuardIn,
    request: Request,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        out = AiSettingsService(db).set_policies_enforced(
            enabled=body.policies_enforced,
            user_id=current.user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _audit(
        db,
        current,
        request,
        "ai.guard.update",
        "ENFORCED" if out["policies_enforced"] else "OPEN",
    )
    return GuardOut(**out)


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


class EvalRunIn(BaseModel):
    case_id: str = Field(min_length=3, max_length=16)


class EvalBatteryIn(BaseModel):
    role: Optional[str] = None


@router.get("/eval/cases")
def eval_cases(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    role: Optional[str] = None,
    category: Optional[str] = None,
    tool: Optional[str] = None,
    expected: Optional[str] = None,
    q: Optional[str] = None,
    mine: bool = True,
):
    if mine and not role:
        for code in ("STUDENT", "TEACHER", "ADMINISTRATOR"):
            if code in (current.roles or []):
                role = code
                break
        else:
            role = current.roles[0] if current.roles else None
    return EvalService.catalog(
        role=role,
        category=category,
        tool=tool,
        expected=expected,
        query=q,
    )


@router.post("/eval/run")
def eval_run(
    body: EvalRunIn,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return EvalService(db).run_case(current, body.case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/eval/battery")
def eval_battery(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
    body: EvalBatteryIn | None = None,
):
    try:
        return EvalService(db).run_battery(current, role=body.role if body else None)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/eval/runs")
def eval_runs(
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    return EvalService(db).list_runs(current.user.id)


@router.get("/eval/runs/{run_id}")
def eval_run_detail(
    run_id: str,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
):
    row = EvalService(db).get_run(current.user.id, run_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RUN_NOT_FOUND")
    return row


@router.get("/eval/export")
def eval_export(
    run_id: str,
    current: Annotated[CurrentUser, Depends(require_permission(P.AI_USE))],
    db: Annotated[Session, Depends(get_db)],
    fmt: str = "json",
):
    try:
        media, payload = EvalService(db).export(current.user.id, run_id, fmt=fmt)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    filename = f"eval-{run_id}.{'csv' if fmt == 'csv' else 'json'}"
    return Response(
        content=payload,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
