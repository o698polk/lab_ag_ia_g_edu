from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.models import User


def permission_required(permission: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            perms = claims.get("permissions", [])
            roles = claims.get("roles", [])
            if "ADMIN" in roles or permission in perms:
                return fn(*args, **kwargs)
            return jsonify({"error": "Acceso denegado", "required": permission}), 403

        return wrapper

    return decorator


def any_permission_required(*permissions):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            perms = set(claims.get("permissions", []))
            roles = claims.get("roles", [])
            if "ADMIN" in roles or any(p in perms for p in permissions):
                return fn(*args, **kwargs)
            return jsonify({"error": "Acceso denegado", "required": list(permissions)}), 403

        return wrapper

    return decorator


def get_current_user() -> User | None:
    uid = get_jwt_identity()
    if uid is None:
        return None
    return User.query.get(int(uid))


def get_impersonator_id():
    claims = get_jwt()
    return claims.get("impersonator_id")
