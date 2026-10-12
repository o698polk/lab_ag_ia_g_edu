from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_limiter.util import get_remote_address

from app.extensions import db, limiter
from app.models import RefreshToken, User
from app.permissions.decorators import get_current_user, get_impersonator_id
from app.services.audit import log_event

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _token_claims(user: User, impersonator_id=None) -> dict:
    claims = {
        "roles": user.get_role_codes(),
        "permissions": sorted(user.get_permissions()),
        "username": user.username,
        "full_name": user.full_name,
    }
    if impersonator_id:
        claims["impersonator_id"] = impersonator_id
    return claims


def _issue_tokens(user: User, impersonator_id=None):
    claims = _token_claims(user, impersonator_id)
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)
    jti = get_jwt().get("jti") if False else None  # placeholder; decode after create
    from flask_jwt_extended import decode_token

    decoded = decode_token(refresh)
    rt = RefreshToken(
        jti=decoded["jti"],
        user_id=user.id,
        impersonator_id=impersonator_id,
        expires_at=datetime.utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    )
    db.session.add(rt)
    db.session.commit()
    return access, refresh


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401

    if user.locked_until and user.locked_until > datetime.utcnow():
        mins = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        return jsonify({"error": f"Cuenta bloqueada. Intente en {mins} minutos"}), 423

    if not user.is_active:
        return jsonify({"error": "Usuario inactivo"}), 403

    if not user.check_password(password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        max_attempts = current_app.config["LOGIN_MAX_ATTEMPTS"]
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=current_app.config["LOGIN_LOCK_MINUTES"]
            )
            user.failed_login_attempts = 0
            db.session.commit()
            log_event(user.id, "LOGIN_LOCKED", "auth", f"IP={get_remote_address()}")
            return jsonify({"error": "Cuenta bloqueada por intentos fallidos"}), 423
        db.session.commit()
        log_event(user.id, "LOGIN_FAILED", "auth", f"IP={get_remote_address()}")
        return jsonify({"error": "Credenciales inválidas"}), 401

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    access, refresh = _issue_tokens(user)
    log_event(user.id, "LOGIN_SUCCESS", "auth", f"IP={get_remote_address()}")

    return jsonify(
        {
            "access_token": access,
            "refresh_token": refresh,
            "user": user.to_dict(include_perms=True),
        }
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    from flask_jwt_extended import decode_token

    claims = get_jwt()
    jti = claims.get("jti")
    rt = RefreshToken.query.filter_by(jti=jti, revoked=False).first()
    if not rt or rt.expires_at < datetime.utcnow():
        return jsonify({"error": "Refresh token inválido o revocado"}), 401

    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return jsonify({"error": "Usuario no válido"}), 401

    impersonator_id = claims.get("impersonator_id")
    access, refresh_tok = _issue_tokens(user, impersonator_id)
    rt.revoked = True
    db.session.commit()
    return jsonify({"access_token": access, "refresh_token": refresh_tok})


@auth_bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    claims = get_jwt()
    jti = claims.get("jti")
    rt = RefreshToken.query.filter_by(jti=jti).first()
    if rt:
        rt.revoked = True
        db.session.commit()
    log_event(int(get_jwt_identity()), "LOGOUT", "auth", "")
    return jsonify({"message": "Sesión cerrada"})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "No encontrado"}), 404
    data = user.to_dict(include_perms=True)
    data["impersonator_id"] = get_impersonator_id()
    return jsonify(data)


@auth_bp.put("/theme")
@jwt_required()
def update_theme():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    theme = data.get("theme", "light")
    if theme not in ("light", "dark"):
        return jsonify({"error": "Tema inválido"}), 400
    user.theme = theme
    db.session.commit()
    return jsonify({"theme": theme})


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    current = data.get("current_password", "")
    new = data.get("new_password", "")
    if len(new) < 8:
        return jsonify({"error": "La nueva contraseña debe tener al menos 8 caracteres"}), 400
    if not user.check_password(current) and not user.must_change_password:
        return jsonify({"error": "Contraseña actual incorrecta"}), 400
    if user.must_change_password and current and not user.check_password(current):
        return jsonify({"error": "Contraseña actual incorrecta"}), 400
    user.set_password(new)
    user.must_change_password = False
    db.session.commit()
    log_event(user.id, "PASSWORD_CHANGED", "auth", "")
    return jsonify({"message": "Contraseña actualizada"})


@auth_bp.post("/return-to-admin")
@jwt_required()
def return_to_admin():
    impersonator_id = get_impersonator_id()
    if not impersonator_id:
        return jsonify({"error": "No está en sesión de impersonación"}), 400
    admin = User.query.get(int(impersonator_id))
    if not admin or not admin.is_active:
        return jsonify({"error": "Administrador no válido"}), 400
    access, refresh = _issue_tokens(admin)
    log_event(admin.id, "IMPERSONATION_END", "users", f"returned_from={get_jwt_identity()}")
    return jsonify(
        {
            "access_token": access,
            "refresh_token": refresh,
            "user": admin.to_dict(include_perms=True),
        }
    )
