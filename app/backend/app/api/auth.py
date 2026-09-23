# Ref: BL-O1-002 | Skill: K-015 | Fase: F6/F8
"""Auth API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.iam import (
    ChangePasswordRequest,
    ForgotPasswordOut,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    user_to_out,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", include_in_schema=False)
def login_get() -> RedirectResponse:
    """Browsers open this URL with GET → would be 405; send them to the UI."""
    return RedirectResponse(url="/ui/pages/auth/login.html", status_code=307)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    svc = AuthService(db)
    try:
        tokens = svc.login(
            body.username,
            body.password,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as exc:
        code = str(exc)
        AuditService(db).record_security(
            request_id=AuditService.new_request_id(),
            user_id=None,
            event_type="LOGIN_FAILURE",
            severity="MED",
            details={"username": body.username, "reason": code},
        )
        status_code = (
            status.HTTP_403_FORBIDDEN
            if code == "USER_INACTIVE"
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(status_code=status_code, detail=code) from exc
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Annotated[Session, Depends(get_db)]):
    svc = AuthService(db)
    try:
        tokens = svc.refresh(body.refresh_token)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: LogoutRequest, db: Annotated[Session, Depends(get_db)]):
    AuthService(db).logout(body.refresh_token)
    return None


@router.get("/me", response_model=UserOut)
def me(current: Annotated[CurrentUser, Depends(get_current_user)]):
    return user_to_out(current.user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        AuthService(db).change_password(
            current.user, body.current_password, body.new_password
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return None


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(body: ForgotPasswordRequest, db: Annotated[Session, Depends(get_db)]):
    token = AuthService(db).request_password_reset(body.username)
    return ForgotPasswordOut(accepted=True, reset_token=token)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: ResetPasswordRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        AuthService(db).reset_password(body.token, body.new_password)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_RESET_TOKEN"
        ) from exc
    return None
