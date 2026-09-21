# Ref: BL-O1-003 | Skill: K-015 | Fase: F6 | ADR-002
"""Password hashing (Argon2 preferred, bcrypt fallback)."""

from passlib.context import CryptContext

from app.core.config import get_settings

_argon2 = CryptContext(schemes=["argon2"], deprecated="auto")
_bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _ctx() -> CryptContext:
    settings = get_settings()
    if settings.password_hasher.lower() == "bcrypt":
        return _bcrypt
    return _argon2


def hash_password(plain: str) -> str:
    return _ctx().hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _ctx().verify(plain, password_hash)
    except Exception:  # noqa: BLE001
        # Cross-scheme verify (migration path)
        for ctx in (_argon2, _bcrypt):
            try:
                if ctx.verify(plain, password_hash):
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False
