# Ref: BL-O5-* | Skill: K-013/K-016/K-021/K-023 | Fase: F6
"""Platform API: dashboard, reports, notifications, user history."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.platform import (
    DashboardOut,
    NotificationCreate,
    NotificationOut,
    ReportCatalogOut,
    ReportGenerateIn,
    ReportGenerateOut,
    ReportLogOut,
    UserHistoryOut,
)
from app.services.platform_service import PlatformService
from app.services.role_service import AuthorizationError

router = APIRouter(tags=["platform"])


def _map_err(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": exc.reason_code},
        )
    if isinstance(exc, ValueError):
        code = str(exc)
        if code == "PDF_NOT_AVAILABLE_P2":
            return HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={"decision": "DENY", "reason_code": "PDF_P2_DEFERRED"},
            )
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)
    return HTTPException(status_code=500, detail="INTERNAL")


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    current: Annotated[CurrentUser, Depends(require_permission(P.DASHBOARD_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    data = PlatformService(db).dashboard_for(user=current.user, roles=current.roles)
    return DashboardOut(**data)


@router.get("/reports/catalog", response_model=List[ReportCatalogOut])
def report_catalog(
    _: Annotated[CurrentUser, Depends(require_permission(P.REPORTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    items = PlatformService(db).list_report_catalog()
    return [
        ReportCatalogOut(code=r.code, name=r.name, description=r.description)
        for r in items
    ]


@router.post("/reports", response_model=ReportGenerateOut)
def generate_report(
    body: ReportGenerateIn,
    current: Annotated[CurrentUser, Depends(require_permission(P.REPORTS_GENERATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = PlatformService(db)
    try:
        result = svc.generate_report(
            user=current.user,
            report_type=body.report_type,
            format_=body.format,
            parameters=body.parameters,
        )
        return ReportGenerateOut(**result)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/reports/logs", response_model=List[ReportLogOut])
def report_logs(
    current: Annotated[CurrentUser, Depends(require_permission(P.REPORTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    # Admin sees all; others see own logs
    user_id = None if "ADMINISTRATOR" in current.roles else current.user.id
    return list(PlatformService(db).list_report_logs(user_id=user_id))


@router.get("/notifications", response_model=List[NotificationOut])
def my_notifications(
    current: Annotated[CurrentUser, Depends(require_permission(P.NOTIFICATIONS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    unread_only: bool = Query(default=False),
):
    return list(
        PlatformService(db).list_notifications(
            current.user.id, unread_only=unread_only
        )
    )


@router.post("/notifications", response_model=NotificationOut, status_code=201)
def create_notification(
    body: NotificationCreate,
    current: Annotated[CurrentUser, Depends(require_permission(P.NOTIFICATIONS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = PlatformService(db)
    try:
        ntf = svc.create_notification(
            user_id=body.user_id,
            type_=body.type,
            title=body.title,
            body=body.body,
        )
        svc.record_history(
            user_id=current.user.id,
            action="notifications.create",
            summary=f"Notification to user {body.user_id}: {body.title}",
            module="notifications",
        )
        return ntf
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.put("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.NOTIFICATIONS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return PlatformService(db).mark_read(
            notification_id=notification_id, user_id=current.user.id
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/me/history", response_model=List[UserHistoryOut])
def my_history(
    current: Annotated[CurrentUser, Depends(require_permission(P.HISTORY_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return list(PlatformService(db).list_history(current.user.id))


@router.get("/users/{user_id}/history", response_model=List[UserHistoryOut])
def user_history(
    user_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.HISTORY_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    """Anti-IDOR: own history or ADMINISTRATOR."""
    if "ADMINISTRATOR" not in current.roles and current.user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": "RESOURCE_NOT_OWNED"},
        )
    return list(PlatformService(db).list_history(user_id))
