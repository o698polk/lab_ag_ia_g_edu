# Ref: BL-O6-003/006 | Skill: K-014/K-019/K-021 | Fase: F6
# Ref: A02 ERD | RF-AUD/AI/GW
"""Zero Trust / IA / Audit ORM models."""

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


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[Optional[str]] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64), index=True)
    module: Mapped[str] = mapped_column(String(64), default="security")
    resource: Mapped[Optional[str]] = mapped_column(String(64))
    resource_id: Mapped[Optional[str]] = mapped_column(String(64))
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    ip: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32))
    reason: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="MED")
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AiConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    messages: Mapped[List["AiMessage"]] = relationship(back_populates="conversation")


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped[AiConversation] = relationship(back_populates="messages")


class ToolRegistryEntry(Base):
    __tablename__ = "tool_registry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(16))
    endpoint: Mapped[str] = mapped_column(String(255))
    parameters_schema: Mapped[Optional[str]] = mapped_column(Text)
    required_permissions: Mapped[Optional[str]] = mapped_column(Text)
    allowed_roles: Mapped[Optional[str]] = mapped_column(Text)
    resource_type: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    invocations: Mapped[List["ToolInvocation"]] = relationship(back_populates="tool")


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tool_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tool_registry.id"))
    tool_name: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_messages.id"))
    parameters: Mapped[Optional[str]] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(16))
    reason_code: Mapped[str] = mapped_column(String(64))
    policy_id: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tool: Mapped[Optional[ToolRegistryEntry]] = relationship(back_populates="invocations")
