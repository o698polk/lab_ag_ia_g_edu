# Ref: RF-AI-CFG | Skill: K-018 | Fase: post-F12
"""Admin DeepSeek credential: encrypt, validate, never expose plaintext."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.deepseek import DEFAULT_BASE_URL, DEFAULT_MODEL, validate_key
from app.core.config import get_settings
from app.core.secret_box import decrypt_secret, encrypt_secret, key_hint
from app.models import AiProviderSetting, User

PROVIDER = "deepseek"
MIN_KEY_LEN = 20


@dataclass
class RuntimeAiConfig:
    api_key: str
    model: str
    base_url: str
    source: str


class AiSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _row(self) -> Optional[AiProviderSetting]:
        return self.db.scalar(
            select(AiProviderSetting).where(AiProviderSetting.provider == PROVIDER)
        )

    def _ensure(self) -> AiProviderSetting:
        row = self._row()
        if row is None:
            row = AiProviderSetting(
                provider=PROVIDER,
                model=DEFAULT_MODEL,
                base_url=DEFAULT_BASE_URL,
                status="EMPTY",
            )
            self.db.add(row)
            self.db.flush()
        return row

    def public_status(self) -> dict:
        row = self._row()
        if row is None or not row.api_key_encrypted:
            return {
                "provider": PROVIDER,
                "configured": False,
                "status": "EMPTY",
                "model": DEFAULT_MODEL,
                "base_url": DEFAULT_BASE_URL,
                "key_hint": "",
                "last_validated_at": None,
            }
        return {
            "provider": PROVIDER,
            "configured": True,
            "status": row.status,
            "model": row.model,
            "base_url": row.base_url,
            "key_hint": row.key_hint or "",
            "last_validated_at": row.last_validated_at,
        }

    def decrypt_stored(self) -> Optional[str]:
        row = self._row()
        if row is None or not row.api_key_encrypted:
            return None
        try:
            return decrypt_secret(row.api_key_encrypted)
        except ValueError:
            return None

    def runtime_config(self) -> Optional[RuntimeAiConfig]:
        stored = self.decrypt_stored()
        if stored:
            row = self._row()
            return RuntimeAiConfig(
                api_key=stored,
                model=(row.model if row else DEFAULT_MODEL) or DEFAULT_MODEL,
                base_url=(row.base_url if row else DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
                source="database",
            )
        env_key = (get_settings().ai_api_key or "").strip()
        if env_key:
            settings = get_settings()
            return RuntimeAiConfig(
                api_key=env_key,
                model=settings.ai_model or DEFAULT_MODEL,
                base_url=settings.ai_base_url or DEFAULT_BASE_URL,
                source="env",
            )
        return None

    def save(
        self,
        *,
        api_key: Optional[str],
        model: Optional[str],
        base_url: Optional[str],
        user_id: int,
    ) -> dict:
        row = self._ensure()
        incoming = (api_key or "").strip()
        if incoming:
            self._assert_key_shape(incoming)
            row.api_key_encrypted = encrypt_secret(incoming)
            row.key_hint = key_hint(incoming)
            row.status = "CONFIGURED"
            row.last_validated_at = None
        elif not row.api_key_encrypted:
            raise ValueError("API_KEY_REQUIRED")
        if model:
            row.model = model.strip()[:64]
        if base_url:
            cleaned = base_url.strip().rstrip("/")
            if not cleaned.startswith("https://"):
                raise ValueError("BASE_URL_MUST_BE_HTTPS")
            row.base_url = cleaned[:255]
        row.updated_by_user_id = user_id
        row.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(row)
        return self.public_status()

    def clear(self, *, user_id: int) -> dict:
        row = self._row()
        if row is None:
            return self.public_status()
        row.api_key_encrypted = None
        row.key_hint = None
        row.status = "EMPTY"
        row.last_validated_at = None
        row.updated_by_user_id = user_id
        row.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self.public_status()

    def policies_enforced(self, user_id: int | None = None) -> bool:
        if user_id is None:
            return True
        user = self.db.get(User, int(user_id))
        if user is None:
            return True
        return bool(getattr(user, "policies_enforced", True))

    def guard_status(self, user_id: int | None = None) -> dict:
        enforced = self.policies_enforced(user_id)
        return {
            "policies_enforced": enforced,
            "mode": "enforced" if enforced else "open",
            "label": "Mínimo privilegio activo" if enforced else "Políticas desactivadas",
        }

    def set_policies_enforced(self, *, enabled: bool, user_id: int) -> dict:
        user = self.db.get(User, int(user_id))
        if user is None:
            raise ValueError("USER_NOT_FOUND")
        user.policies_enforced = bool(enabled)
        self.db.commit()
        return self.guard_status(user_id)

    def validate(self, *, user_id: int) -> dict:
        cfg = self.runtime_config()
        if cfg is None:
            raise ValueError("API_KEY_REQUIRED")
        validate_key(api_key=cfg.api_key, base_url=cfg.base_url)
        row = self._row()
        if row and row.api_key_encrypted:
            row.status = "VALID"
            row.last_validated_at = datetime.now(timezone.utc)
            row.updated_by_user_id = user_id
            self.db.commit()
        return {**self.public_status(), "valid": True}

    @staticmethod
    def _assert_key_shape(api_key: str) -> None:
        if len(api_key) < MIN_KEY_LEN or any(ch.isspace() for ch in api_key):
            raise ValueError("API_KEY_INVALID")
        if api_key.lower() in {"changeme", "your-api-key", "sk-xxx"}:
            raise ValueError("API_KEY_INVALID")
