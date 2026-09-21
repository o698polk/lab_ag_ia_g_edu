# Checklist F5 — Configuración (K-004)

| Campo | Valor |
|---|---|
| Fase | F5 |
| Skill | K-004 Agent Configurator |
| BL | BL-QA-001 |
| Fecha | 2026-09-20 |

## Criterios Gate F5

- [x] Estructura `app/backend`, `app/frontend`, `tests`, `policies`, `scripts`, `evidence`
- [x] `.env.example` sin secretos reales
- [x] `.gitignore` excluye `.env`, `.venv`, logs
- [x] `requirements.txt` con stack obligatorio
- [x] Settings + logging + health/ready
- [x] Policies v1 placeholders (Deny by Default)
- [x] Scripts `check_env.py` / `check_mysql.py`
- [x] Tests unitarios de health
- [x] venv creado + dependencias instaladas (evidencia abajo)
- [x] `pytest` health verde
- [x] MySQL XAMPP reachable **o** WARN documentado

## Comandos

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r app/backend/requirements.txt
copy .env.example .env
python scripts/check_env.py
python scripts/check_mysql.py
pytest tests/unit/test_health.py
uvicorn app.main:app --app-dir app/backend --host 127.0.0.1 --port 8000
```

## Notas

- F5 **no** implementa módulos de negocio (F6).
- JWT_SECRET placeholder debe cambiarse antes de auth real.
- Bind obligatorio: `127.0.0.1` (ADR-009).
