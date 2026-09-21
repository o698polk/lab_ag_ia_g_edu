# Ref: BL-QA-001 | Skill: K-004 | Fase: F5
"""Validate that required env keys exist (does not print secret values)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

REQUIRED = [
    "APP_HOST",
    "APP_PORT",
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "JWT_SECRET",
    "POLICY_PATH",
    "AI_PROVIDER",
]


def main() -> int:
    env_path = ROOT / ".env"
    source = env_path if env_path.exists() else ROOT / ".env.example"
    if not source.exists():
        print("FAIL: neither .env nor .env.example found")
        return 1

    values: dict[str, str] = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()

    missing = [k for k in REQUIRED if k not in values]
    if missing:
        print(f"FAIL: missing keys in {source.name}: {missing}")
        return 1

    from app.core.config import get_settings

    settings = get_settings()
    print(f"OK: config loaded from {source.name}")
    print(f"  APP_HOST={settings.app_host} APP_PORT={settings.app_port}")
    print(f"  DB={settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"  AI_PROVIDER={settings.ai_provider}")
    print(f"  POLICY_PATH={settings.policy_path}")
    if settings.is_jwt_secret_default:
        print("  WARN: JWT_SECRET is placeholder — replace before real auth (F6)")
    if settings.app_host not in ("127.0.0.1", "localhost"):
        print(f"  WARN: APP_HOST={settings.app_host} (prefer 127.0.0.1 in F5/F11)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
