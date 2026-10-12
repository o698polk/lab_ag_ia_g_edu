"""Crea BD MySQL (XAMPP) desde cero según DATABASE_URL del .env, tablas y seeds."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymysql
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "database" / "seeds"))


def _parse_database_url(url: str) -> dict:
    """mysql+pymysql://user:pass@host:port/dbname → dict de conexión."""
    if not url or not url.startswith("mysql"):
        raise SystemExit(
            "DATABASE_URL debe ser MySQL, p. ej. "
            "mysql+pymysql://root:@127.0.0.1:3306/laboratorioA"
        )
    # urlparse no entiende mysql+pymysql; normalizar
    normalized = re.sub(r"^mysql\+[^:]+://", "mysql://", url)
    parsed = urlparse(normalized)
    db_name = (parsed.path or "").lstrip("/").split("?")[0]
    if not db_name:
        raise SystemExit("DATABASE_URL sin nombre de base de datos.")
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": db_name,
    }


def recreate_database(cfg: dict) -> None:
    """DROP + CREATE la base (desde cero)."""
    conn = pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        port=cfg["port"],
        autocommit=True,
    )
    cur = conn.cursor()
    db = cfg["database"]
    cur.execute(f"DROP DATABASE IF EXISTS `{db}`")
    cur.execute(
        f"CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.execute("SHOW DATABASES LIKE %s", (db,))
    print("DB:", cur.fetchall())
    cur.close()
    conn.close()


def main() -> None:
    url = os.getenv("DATABASE_URL", "")
    cfg = _parse_database_url(url)
    print("Creando BD desde cero:", cfg["database"], "@", f"{cfg['host']}:{cfg['port']}")
    recreate_database(cfg)

    from run import app
    from app.extensions import db
    from seed_data import seed_all, sync_profile_visibility_perms
    from sqlalchemy import text

    with app.app_context():
        print("URI:", app.config["SQLALCHEMY_DATABASE_URI"])
        # Esquema (equivalente a migración inicial vía modelos)
        db.drop_all()
        db.create_all()
        seeded = seed_all(app)
        sync_profile_visibility_perms(db)
        print("SEED:", "ok (nuevo)" if seeded else "omitido (ya había datos)")

        rows = db.session.execute(text("SHOW TABLES")).fetchall()
        print("TABLES:", len(rows), [r[0] for r in rows])
        from app.models import User, Role

        print("USERS:", User.query.count(), "ROLES:", Role.query.count())
        print("Listo. Base:", cfg["database"])


if __name__ == "__main__":
    main()
