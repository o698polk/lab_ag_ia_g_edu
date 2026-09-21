# Ref: BL-O1-001 | Skill: K-014 | Fase: F6
"""Create IAM tables (dev bootstrap). Prefer Alembic when MySQL is available."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from app.db.session import Base, engine
import app.models  # noqa: F401 — register models


def main() -> int:
    Base.metadata.create_all(bind=engine)
    print(f"OK: tables created on {engine.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
