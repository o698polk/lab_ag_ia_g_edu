# Configuración — variables de entorno

| Campo | Valor |
|---|---|
| Fase | F9 |
| Skill | K-008 |
| Fuente | `.env.example` · `app/backend/app/core/config.py` |

## Archivos

| Archivo | Uso |
|---|---|
| `.env.example` | Plantilla versionada (sin secretos reales) |
| `.env` | Local — **nunca** en Git |

```powershell
copy .env.example .env
```

## Variables principales

| Variable | Descripción | Default / nota |
|---|---|---|
| `APP_NAME` | Nombre del servicio | SIGA |
| `APP_ENV` | `local` \| `test` \| … | `local` |
| `APP_HOST` | Bind | `127.0.0.1` |
| `APP_PORT` | Puerto | `8000` |
| `APP_DEBUG` | Expone `/docs` si true | `true` en lab |
| `APP_API_PREFIX` | Prefijo API | `/api/v1` |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL XAMPP | root sin password típico lab |
| `DATABASE_URL` | Override completo (tests SQLite) | opcional |
| `JWT_SECRET` | Secreto HS256 (≥32) | **cambiar** placeholder |
| `JWT_ACCESS_TTL_MINUTES` | TTL access | 30 |
| `JWT_REFRESH_TTL_DAYS` | TTL refresh | 7 |
| `PASSWORD_HASHER` | `argon2` \| `bcrypt` | `argon2` |
| `POLICY_PATH` | PAP YAML | `policies/v1` |
| `AI_PROVIDER` | `mock` \| … | `mock` |
| `AI_API_KEY` | Solo si proveedor externo | vacío |
| `CORS_ORIGINS` | Orígenes permitidos | solo localhost |

## Checklist de seguridad de config

- [ ] `JWT_SECRET` no es el placeholder `CHANGE_ME_…`
- [ ] `.env` no está commiteado
- [ ] `APP_HOST=127.0.0.1`
- [ ] `AI_API_KEY` vacío salvo uso controlado
- [ ] `/api/v1/ready` no reporta warning de JWT por defecto (tras cambio)

## Políticas (PAP)

Las políticas versionadas viven en `policies/v1/*.yaml`. El PDP las carga al arrancar (memoria). Cambios requieren recarga de proceso o reinicio del loader PAP.
