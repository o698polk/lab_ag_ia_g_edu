import uuid
from datetime import datetime, timedelta

from app.extensions import db


def _uuid():
    return str(uuid.uuid4())


class AIConversation(db.Model):
    __tablename__ = "ai_conversations"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200))
    pending_action = db.Column(db.JSON, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("ai_conversations", lazy="dynamic"))
    messages = db.relationship(
        "AIMessage",
        back_populates="conversation",
        order_by="AIMessage.created_at",
        cascade="all, delete-orphan",
    )
    artifacts = db.relationship("AIArtifact", back_populates="conversation", lazy="dynamic")

    def to_dict(self, include_messages=False, message_limit=100):
        from app.ai.conversations import conversation_to_dict

        return conversation_to_dict(self, include_messages=include_messages, message_limit=message_limit)


class AIMessage(db.Model):
    __tablename__ = "ai_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(20), default="api")
    tool_name = db.Column(db.String(80))
    tool_payload = db.Column(db.JSON)
    artifact_id = db.Column(db.Integer, db.ForeignKey("ai_artifacts.id"), nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    conversation = db.relationship("AIConversation", back_populates="messages")
    artifact = db.relationship("AIArtifact", foreign_keys=[artifact_id])

    def to_dict(self):
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "channel": self.channel,
            "tool_name": self.tool_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.artifact_id:
            data["artifact_id"] = self.artifact_id
            if self.artifact:
                data["artifact"] = self.artifact.to_dict()
        return data


class AIArtifact(db.Model):
    __tablename__ = "ai_artifacts"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("ai_conversations.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    format = db.Column(db.String(10), nullable=False)
    report_type = db.Column(db.String(40), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    filters = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=72))

    conversation = db.relationship("AIConversation", back_populates="artifacts")
    user = db.relationship("User")

    def to_dict(self):
        # SPEC-021: URL firmada descargable sin JWT en el navegador
        from app.services.artifact_links import artifact_download_path

        path = artifact_download_path(self)
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "format": self.format,
            "report_type": self.report_type,
            "filename": self.filename,
            "download_url": path,
            "download_path": path,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIAgentLog(db.Model):
    """LogIA — auditoría del agente (SPEC-026)."""

    __tablename__ = "ai_agent_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    username = db.Column(db.String(80))
    role_codes = db.Column(db.String(255))
    conversation_id = db.Column(db.String(36), index=True)
    event_type = db.Column(db.String(40), nullable=False, index=True)
    severity = db.Column(db.String(20), default="info", index=True)
    summary = db.Column(db.String(500))
    detail = db.Column(db.JSON)
    keywords = db.Column(db.Text)
    user_question = db.Column(db.Text)  # SPEC-029
    channel = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "role_codes": self.role_codes,
            "conversation_id": self.conversation_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "summary": self.summary,
            "detail": self.detail,
            "keywords": self.keywords,
            "user_question": self.user_question,
            "channel": self.channel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ElevationRequest(db.Model):
    __tablename__ = "elevation_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    requested_permissions = db.Column(db.JSON, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolution_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "requested_permissions": self.requested_permissions,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
