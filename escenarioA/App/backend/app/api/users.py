from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Role, User
from app.permissions.decorators import get_current_user, get_impersonator_id, permission_required
from app.services.audit import log_event

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.get("")
@jwt_required()
@permission_required("users.view")
def list_users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(User.username.ilike(like), User.email.ilike(like), User.first_name.ilike(like))
        )
    users = query.order_by(User.id.desc()).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.post("")
@jwt_required()
@permission_required("users.create")
def create_user():
    data = request.get_json(silent=True) or {}
    required = ["username", "email", "password", "first_name", "last_name"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Campo requerido: {f}"}), 400
    if User.query.filter((User.username == data["username"]) | (User.email == data["email"])).first():
        return jsonify({"error": "Usuario o email ya existe"}), 409

    user = User(
        username=data["username"].strip(),
        email=data["email"].strip().lower(),
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        is_active=data.get("is_active", True),
        must_change_password=True,
    )
    user.set_password(data["password"])
    role_codes = data.get("roles") or []
    if role_codes:
        roles = Role.query.filter(Role.code.in_(role_codes)).all()
        user.roles = roles
    db.session.add(user)
    db.session.commit()
    log_event(get_current_user().id, "USER_CREATE", "users", f"id={user.id}")
    return jsonify(user.to_dict()), 201


@users_bp.put("/<int:user_id>")
@jwt_required()
@permission_required("users.edit")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    for field in ("first_name", "last_name", "email", "theme"):
        if field in data:
            setattr(user, field, data[field])
    if "is_active" in data and not user.is_protected:
        user.is_active = bool(data["is_active"])
    if "roles" in data:
        roles = Role.query.filter(Role.code.in_(data["roles"])).all()
        user.roles = roles
    if data.get("password"):
        user.set_password(data["password"])
        user.must_change_password = True
    db.session.commit()
    log_event(get_current_user().id, "USER_UPDATE", "users", f"id={user.id}")
    return jsonify(user.to_dict())


@users_bp.delete("/<int:user_id>")
@jwt_required()
@permission_required("users.delete")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_protected:
        return jsonify({"error": "Usuario protegido"}), 403
    me = get_current_user()
    if user.id == me.id:
        return jsonify({"error": "No puede eliminarse a sí mismo"}), 400
    db.session.delete(user)
    db.session.commit()
    log_event(me.id, "USER_DELETE", "users", f"id={user_id}")
    return jsonify({"message": "Usuario eliminado"})


@users_bp.post("/<int:user_id>/login-as")
@jwt_required()
@permission_required("users.login-as")
def login_as(user_id):
    from app.auth.routes import _issue_tokens

    if get_impersonator_id():
        return jsonify({"error": "ALREADY_IMPERSONATING"}), 400

    admin = get_current_user()
    target = User.query.get_or_404(user_id)

    if target.id == admin.id:
        return jsonify({"error": "No puede impersonarse a sí mismo"}), 400
    if target.is_protected:
        return jsonify({"error": "No se puede impersonar cuentas protegidas"}), 403
    if not target.is_active:
        return jsonify({"error": "Usuario inactivo"}), 400

    access, refresh = _issue_tokens(target, impersonator_id=admin.id)
    log_event(admin.id, "IMPERSONATION_START", "users", f"target={target.id}")
    return jsonify(
        {
            "access_token": access,
            "refresh_token": refresh,
            "user": target.to_dict(include_perms=True),
            "impersonator_id": admin.id,
        }
    )
