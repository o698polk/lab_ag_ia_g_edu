# Evidencia F6-O1 — IAM

| Campo | Valor |
|---|---|
| Fase | F6 — Desarrollo / Oleada O1 |
| Skills | K-013, K-014, K-015, K-016, K-024, K-006 |
| Fecha | 2026-09-20 |

## Entregado

- Modelos IAM + Alembic `0001_iam`
- Auth JWT access/refresh + Argon2
- APIs `/auth`, `/users`, `/roles`, `/permissions`
- Deny by Default (`require_permission` revalida desde DB)
- Seed `scripts/seed_iam.py`
- Tests SQLite: **11 passed**

## MySQL

XAMPP MySQL no estaba activo en la máquina. Para entorno local MySQL:

```powershell
# 1) Arrancar XAMPP MySQL y crear DB siga
# 2) Luego:
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\seed_iam.py
uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

Usuarios seed: `admin` / `Admin123!`, `teacher1` / `Teacher123!`, `student1` / `Student123!`

## Próximo

O2 — Catálogo académico (students/teachers/careers/subjects/terms)
