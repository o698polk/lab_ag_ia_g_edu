# A04 — Diagrama de despliegue (localhost)

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F3 — Arquitectura |
| Skill | K-002 Architecture Designer |
| Spec | S09 ADR-009, PromptMaster F11 |
| Fecha | 2026-09-20 |

---

## 1. Deployment — entorno local de desarrollo

```mermaid
deploymentDiagram
  title SIGA Local Deployment (F11)

  node "Developer Workstation" {
    node "Browser" {
      artifact "Frontend HTML/JS/CSS"
    }

    node "Python 3.11+ venv" {
      artifact "Uvicorn"
      artifact "FastAPI App (127.0.0.1:8000)"
    }

    node "XAMPP" {
      artifact "MySQL 8 (3306)"
      artifact "phpMyAdmin (admin only)"
    }

    node "Filesystem" {
      artifact "policies/v1/*.yaml"
      artifact ".env (local, not in git)"
      artifact "evidence/"
      artifact "logs/"
    }
  }

  node "External (optional)" {
    artifact "LLM API"
  }

  Browser --> "FastAPI App (127.0.0.1:8000)" : HTTP
  "FastAPI App (127.0.0.1:8000)" --> "MySQL 8 (3306)" : SQLAlchemy
  "FastAPI App (127.0.0.1:8000)" --> "policies/v1/*.yaml" : PAP load
  "FastAPI App (127.0.0.1:8000)" --> "LLM API" : HTTPS (or mock)
```

---

## 2. Puertos y binds

| Servicio | Bind | Puerto | Nota |
|---|---|---|---|
| FastAPI / Uvicorn | `127.0.0.1` | `8000` | No `0.0.0.0` sin autorización |
| Frontend | `127.0.0.1` | `5500` o servido por FastAPI StaticFiles | Local only |
| MySQL | `127.0.0.1` | `3306` | XAMPP default |
| phpMyAdmin | localhost | `80` | Solo administración DB |

---

## 3. Variables de entorno (categorías — sin secretos reales)

```text
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=siga
DB_USER=...
DB_PASSWORD=...

JWT_SECRET=...
JWT_ACCESS_TTL=...
JWT_REFRESH_TTL=...

AI_PROVIDER=mock|openai|other
AI_API_KEY=...
AI_BASE_URL=...

POLICY_PATH=policies/v1
```

Fuente normativa: `.env.example` en F5 (ADR-002/011 pendientes de cierre operativo).

---

## 4. Restricciones de despliegue

1. Sin publicación a Internet en baseline.  
2. Secretos fuera de Git.  
3. MySQL solo red local.  
4. LLM opcional; tests con mock.  
5. phpMyAdmin no es parte de la App; no exponer lógica de negocio ahí.

---

## 5. Diagrama de red lógico

```text
[Browser 127.0.0.1]
        |
        |  HTTP :8000 / static
        v
[FastAPI 127.0.0.1:8000]
   |           |            |
   | SQL       | read       | HTTPS (opt)
   v           v            v
[MySQL]   [policies/]   [LLM API]
```

---

## 6. Criterio Gate F11 (referencia)

- App responde en `http://127.0.0.1:8000/health` (o equivalente).  
- Login funciona contra MySQL local.  
- No hay bind público accidental.
