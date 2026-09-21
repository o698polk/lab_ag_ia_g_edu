# F11 — Deployment localhost (K-010)

| Campo | Valor |
|---|---|
| Fase | F11 — Deployment |
| Skill | K-010 Deployment Orchestrator |
| Fecha | 2026-09-20 |
| Gate previo | F10 **GO CONDICIONADO** |
| Bind | **127.0.0.1:8000** (no Internet) |

---

## 1. Checklist ejecutado

| Paso | Resultado |
|---|---|
| `.env` local (JWT no placeholder) | ✅ |
| `scripts/check_env.py` | ✅ APP_HOST=127.0.0.1 |
| XAMPP MySQL arrancado | ✅ |
| DB `siga` creada | ✅ |
| `scripts/init_db.py` + `alembic stamp head` → `0006_zero_trust` | ✅ |
| `scripts/seed_iam.py` | ✅ admin / teacher1 / student1 |
| `scripts/check_mysql.py` | ✅ SELECT 1 |
| uvicorn `--host 127.0.0.1 --port 8000` | ✅ en ejecución |
| Smoke health / ready / ui / docs / login | ✅ |

---

## 2. Smoke verify

| URL | Esperado | Resultado |
|---|---|---|
| `http://127.0.0.1:8000/api/v1/health` | status ok · phase F11 | ✅ |
| `http://127.0.0.1:8000/api/v1/ready` | ready · host 127.0.0.1 | ✅ |
| `http://127.0.0.1:8000/ui/` | HTML dashboard | ✅ 200 |
| `http://127.0.0.1:8000/docs` | OpenAPI | ✅ 200 |
| `POST /api/v1/auth/login` (admin) | access_token | ✅ |

Detalle: `evidence/f11/smoke-verify.json`

---

## 3. Restricciones ADR-009

```text
Bind exclusivo: 127.0.0.1 / localhost
NO publicar 0.0.0.0 ni Internet sin autorización humana
```

---

## 4. Notas lab

- Schema bootstrap vía `create_all` + stamp Alembic (tablas ya existían al upgrade).
- Credenciales seed lab: ver `seed-iam.txt` (solo entorno local).
- Condiciones F10 (gaps P1/P2 · ADR-013) siguen vigentes.

---

## 5. Artefactos

| Archivo | Contenido |
|---|---|
| `check-env.txt` | Config |
| `check-mysql.txt` | MySQL OK |
| `init-db.txt` | create_all |
| `alembic-stamp.txt` | stamp → 0006 |
| `seed-iam.txt` | usuarios demo |
| `smoke-verify.json` | probes HTTP |
| `GATE-F11.md` | decisión humana → F12 |

---

## 6. Próximo (si GO)

F12 — Evaluation · Skill K-011
