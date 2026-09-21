# Instalación local — SIGA

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| Ref | A04 · RNF-DEP-001 · ADR-009 |

## Requisitos

- Windows 10/11 (laboratorio validado)
- Python 3.11+ (probado también con 3.14 en lab)
- XAMPP con MySQL 8+ (opcional para UI local; tests usan SQLite en memoria)
- Git

## Pasos

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r app\backend\requirements.txt
copy .env.example .env
# Editar .env: JWT_SECRET (>=32 chars), DB_* si usa MySQL
python scripts\check_env.py
python scripts\check_mysql.py
```

### Base de datos (MySQL / XAMPP)

1. Iniciar MySQL en XAMPP.
2. Crear schema `siga` (o el nombre de `DB_NAME`).
3. Aplicar migraciones y seed:

```powershell
cd app\backend
alembic upgrade head
cd ..\..
python scripts\seed_iam.py
# demo UI (notas/asistencia): python scripts\seed_demo_academic.py
# opcional: python scripts\init_db.py
```

### Arranque API

```powershell
uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

### Verificación

| URL | Esperado |
|---|---|
| http://127.0.0.1:8000/api/v1/health | `status: ok`, `phase: F12` |
| http://127.0.0.1:8000/docs | OpenAPI (si `APP_DEBUG=true`) |
| http://127.0.0.1:8000/ui/ | Dashboard mínimo |

### Tests

```powershell
$env:PYTHONPATH = "d:\PROYECTOS\lab_ag_ia_g_edu\app\backend"
pytest tests -q
```

## Restricción

Solo **localhost / 127.0.0.1**. No publicar en Internet sin autorización (ADR-009).
