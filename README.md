# SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`)

Metodología **PolkDev**: `SPEC → SKILL → APP`.

## Estado actual

| Fase | Estado |
|---|---|
| F1 Planificación | ✅ |
| F2 SPEC | ✅ |
| F3 Arquitectura | ✅ |
| F4 Skills | ✅ |
| F5 Configuración | ✅ |
| F6 Desarrollo | ⏳ O1–O5 ✅ · O6 pendiente |
| F7+ | Pendiente |

## Stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic, JWT
- DB: MySQL 8+ (XAMPP local)
- Frontend: HTML/CSS/JS + Bootstrap 5
- Seguridad: RBAC + ABAC + PAP/PDP + Tool Gateway (F6)

## Arranque local (F5)

```powershell
cd d:\PROYECTOS\lab_ag_ia_g_edu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r app\backend\requirements.txt
copy .env.example .env
python scripts\check_env.py
python scripts\check_mysql.py
pytest tests\unit\test_health.py
uvicorn app.main:app --app-dir app\backend --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/api/v1/health  
- UI scaffold: http://127.0.0.1:8000/ui/

## Documentación PolkDev

- Spec: `spec/`
- Skills: `skills/`
- Arquitectura: `documentation/architecture/`
- PromptMaster: `prompt_master.md`

## Regla

Ningún secreto en Git. Ningún código de negocio sin Spec + Skill + Gate.
