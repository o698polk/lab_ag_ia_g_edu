"""Validación SPEC-019: filtros + export Excel/PDF."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "database" / "seeds"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from run import app
from app.services.reports import REPORT_CATALOG, build_report
from app.models import User


def main():
    c = app.test_client()
    with app.app_context():
        r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"})
        token = r.get_json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        user = User.query.filter_by(username="admin").first()

        types = list(REPORT_CATALOG.keys())
        print("CATALOG", len(types), ",".join(types))

        # users with role filter
        cfg, headers, rows = build_report("users", user, {"role": "ADMIN"})
        print("USERS_ADMIN_ROWS", len(rows), "cols", len(headers))
        assert len(rows) >= 1

        for t in ("users", "teachers", "careers", "subjects", "terms", "courses", "schedules", "notifications", "audit", "students", "grades"):
            rx = c.get(f"/api/v1/reports/{t}.xlsx", headers=h)
            rp = c.get(f"/api/v1/reports/{t}.pdf", headers=h)
            print(f"{t}: xlsx={rx.status_code} pdf={rp.status_code} bytes_x={len(rx.data)} bytes_p={len(rp.data)}")
            assert rx.status_code == 200, (t, rx.get_json())
            assert rp.status_code == 200, (t, rp.get_json())

        # role query on users export
        ru = c.get("/api/v1/reports/users.xlsx?role=TEACHER&status=activo", headers=h)
        print("USERS_FILTERED", ru.status_code, len(ru.data))
        assert ru.status_code == 200

        print("ALL_CHECKS_PASSED")


if __name__ == "__main__":
    main()
