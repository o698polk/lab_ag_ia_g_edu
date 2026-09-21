# Ref: BL-O5-* | Skill: K-014/K-021/K-023 | Fase: F6
# Ref: A02 ERD | RF-REP/NTF/DSH/AUD-002
"""Platform: reports, report_logs, notifications, user_history (≠ audit)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Report(Base):
    """Catalog of available report definitions."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    logs: Mapped[List["ReportLog"]] = relationship(back_populates="report")


class ReportLog(Base):
    __tablename__ = "report_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id"))
    report_type: Mapped[str] = mapped_column(String(64), index=True)
    format: Mapped[str] = mapped_column(String(16))  # HTML|CSV|JSON
    parameters: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    result_status: Mapped[str] = mapped_column(String(32), default="SUCCESS")
    row_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped[Optional[Report]] = relationship(back_populates="logs")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))  # INFO|WARNING|SUCCESS|ALERT|SECURITY|ACADEMIC
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    read_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserHistoryEvent(Base):
    """User-facing activity history — distinct from audit_events (O6)."""

    __tablename__ = "user_history_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    module: Mapped[str] = mapped_column(String(64), default="platform")
    summary: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
