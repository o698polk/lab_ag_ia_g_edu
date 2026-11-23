# SPEC-001 — Arquitectura General

**Objetivo:** Definir la estructura y arquitectura del sistema web.

## Requisitos

- Arquitectura MVC con Flask Blueprints por módulo.
- API RESTful con prefijo `/api/v1/`.
- Autenticación stateless con JWT (access token + refresh token).
- Separación total entre backend (API) y frontend (templates Jinja2 + JS).
- Configuración centralizada en `.env` y tabla `system_config` en base de datos.
- Sistema multirrol con permisos granulares por módulo y acción.
- Soporte completo para modo claro y oscuro (CSS variables + localStorage).
- El agente IA tiene acceso a todos los módulos mediante endpoints protegidos.

## Estructura

```
App/
├── backend/app/   → API, auth, models, services, permissions, ai
├── frontend/      → templates, static (css, js, assets)
└── database/      → migrations, seeds
```

## Endpoints base

| Prefijo | Descripción |
| --- | --- |
| `/api/v1/auth` | Autenticación |
| `/api/v1/users` | Usuarios e impersonación |
| `/api/v1/*` | Módulos académicos y administrativos |
| `/` | Frontend Jinja2 |
