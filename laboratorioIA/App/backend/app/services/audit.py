from flask import request

from app.extensions import db
from app.models import AuditLog


def log_event(user_id, action: str, module: str, details: str = ""):
    ip = request.remote_addr if request else None
    entry = AuditLog(
        user_id=user_id,
        action=action,
        module=module,
        details=details,
        ip_address=ip,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
