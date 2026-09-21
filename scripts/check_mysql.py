# Ref: BL-QA-001 | Skill: K-004 | Fase: F5 | K-014
"""Check MySQL connectivity for local XAMPP. Non-fatal if DB is down (reports WARN)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))


def main() -> int:
    from sqlalchemy import text

    from app.core.config import get_settings
    from app.db.session import engine

    settings = get_settings()
    print(f"Trying MySQL at {settings.db_host}:{settings.db_port}/{settings.db_name} ...")
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT 1")).scalar()
        print(f"OK: MySQL reachable (SELECT 1 => {row})")
        return 0
    except Exception as exc:  # noqa: BLE001 — intentional diagnostic script
        root = exc
        while getattr(root, "__cause__", None) is not None:
            root = root.__cause__  # type: ignore[assignment]
        print("WARN: MySQL not reachable yet (expected if XAMPP/MySQL not started)")
        print(f"  detail: {type(root).__name__}: {root}")
        print("  checklist:")
        print("    1. Start XAMPP MySQL")
        print("    2. Create database `siga` in phpMyAdmin")
        print("    3. Copy .env.example → .env and set DB_USER/DB_PASSWORD")
        print("    4. Re-run: python scripts/check_mysql.py")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
