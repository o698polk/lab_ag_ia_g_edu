"""
Crea la BD MySQL (XAMPP) desde cero según DATABASE_URL del .env,
aplica tablas (create_all) y seeders base + coherente (SPEC-033).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymysql
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent
APP_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(APP_ROOT / "database" / "seeds"))

load_dotenv(APP_ROOT / ".env")
load_dotenv(APP_ROOT.parent / ".env")

DEFAULT_DB = "laboratorioB"


def _parse_database_url(url: str) -> dict:
    """mysql+pymysql://user:pass@host:port/dbname → dict conexión."""
    raw = (url or "").strip()
    if not raw or raw.startswith("sqlite"):
        raise SystemExit(
            "DATABASE_URL debe ser MySQL (XAMPP), ej:\n"
            f"  mysql+pymysql://root:@127.0.0.1:3306/{DEFAULT_DB}"
        )
    # sqlalchemy usa mysql+pymysql:// — urlparse necesita esquema estándar
    normalized = re.sub(r"^mysql\+pymysql://", "mysql://", raw, flags=re.I)
    parsed = urlparse(normalized)
    db_name = (parsed.path or "").lstrip("/").split("?")[0] or DEFAULT_DB
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": db_name,
    }


def recreate_database(cfg: dict) -> None:
    print(f"Conectando a MySQL {cfg['host']}:{cfg['port']} como {cfg['user']}…")
    conn = pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        port=cfg["port"],
        autocommit=True,
    )
    cur = conn.cursor()
    db = cfg["database"]
    print(f"DROP DATABASE IF EXISTS `{db}` …")
    cur.execute(f"DROP DATABASE IF EXISTS `{db}`")
    print(f"CREATE DATABASE `{db}` …")
    cur.execute(
        f"CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.execute("SHOW DATABASES LIKE %s", (db,))
    print("DB:", cur.fetchall())
    cur.close()
    conn.close()


def main() -> None:
    url = os.getenv("DATABASE_URL", f"mysql+pymysql://root:@127.0.0.1:3306/{DEFAULT_DB}")
    cfg = _parse_database_url(url)
    print("DATABASE_URL ->", f"{cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}")

    recreate_database(cfg)

    from run import app
    from app.extensions import db
    from seed_data import seed_all, sync_profile_visibility_perms
    from seed_coherent import seed_coherent
    from sqlalchemy import text

    with app.app_context():
        print("URI app:", app.config["SQLALCHEMY_DATABASE_URI"])
        print("Creando tablas (db.create_all)…")
        db.create_all()
        print("Seed base (roles, permisos, admin)…")
        seeded = seed_all(app)
        print("SEED base:", seeded)
        sync_profile_visibility_perms(db)
        print("Seed coherente testing avanzado (SPEC-033)…")
        coherent = seed_coherent(app, reset=True)
        print("SEED coherent:", coherent)

        db.session.remove()
        rows = db.session.execute(text("SHOW TABLES")).fetchall()
        print("TABLES:", len(rows), [r[0] for r in rows])
        from app.models import User, Role, Career, Student, Teacher, Term, Course, Enrollment

        print(
            "USERS:", User.query.count(),
            "ROLES:", Role.query.count(),
            "CAREERS:", Career.query.count(),
            "TERMS:", Term.query.count(),
            "STUDENTS:", Student.query.count(),
            "TEACHERS:", Teacher.query.count(),
            "COURSES:", Course.query.count(),
            "ENROLLMENTS:", Enrollment.query.count(),
        )
        print("Listo. BD:", cfg["database"])


if __name__ == "__main__":
    main()
