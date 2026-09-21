# Informe técnico — Navegación, autenticación y persistencia JWT

| Campo | Valor |
|---|---|
| Fecha | 2026-09-21 |
| Spec | RF-AUTH-001…004, RF-IAM-001, RNF-UX-001, ADR-005 |
| Skills | K-022 Frontend Engineer, K-015 JWT Security, K-006 Test Engineer |
| Alcance | Corrección de fallas existentes; sin auto-registro público (no está en spec) |

## Método (Spec-as-Skill)

Analizar → Especificar → Causa → Skill → Implementar → Probar → Validar.

No se añadió `POST /auth/register`. El alta de usuarios sigue siendo `POST /users` con permiso `users.create` (administrador).

## Arquitectura encontrada

- SPA estática en `/ui/` (FastAPI StaticFiles). Backend FastAPI `/api/v1`.
- Auth: access JWT + refresh opaco; `/auth/me` revalida identidad en BD (JWT no autoriza solo).
- UI no autoriza; el servidor responde ALLOW/DENY.

## Matriz de pruebas

| Prueba | Resultado esperado | Evidencia | Estado |
|---|---|---|---|
| Abrir Home | Home cargado | `GET /ui/` 200, `#/home` | CORREGIDO |
| Ir a Login | Login funcional | `#/login`, POST `/auth/login` | CORREGIDO |
| Registrar usuario | Alta vía API admin | `POST /users` 201; UI Catálogo | CORREGIDO |
| Login correcto | Dashboard | 200 + `#/dashboard` | CORREGIDO |
| Login incorrecto | Mensaje claro | 401 `INVALID_CREDENTIALS` → texto UI | CORREGIDO |
| JWT válido + recargar | Mantener sesión | `localStorage` + `GET /auth/me` (+ refresh) | CORREGIDO |
| JWT inválido + recargar | Login | clearSession + `#/login` | CORREGIDO |
| Dashboard → Módulo A | Navegación | hash `#/grades` | CORREGIDO |
| Módulo A → Módulo B | Navegación | hashchange | CORREGIDO |
| Módulo → Dashboard | Retorno | `#/dashboard` | CORREGIDO |
| Botón Atrás | Estado anterior | historial hash | CORREGIDO |
| Botón Adelante | Estado siguiente | historial hash | CORREGIDO |
| Cerrar sesión | Tokens eliminados | logout 204 + localStorage vacío | CORREGIDO |
| Ruta protegida sin sesión | Login | `#/dashboard` → `#/login` | CORREGIDO |
| Backend caído | Error controlado | status 0 / NETWORK en UI | CORREGIDO |

Pytest: `tests/unit/test_ui_session_navigation.py` + IAM/health → **24 passed**.

## Hallazgos y correcciones

### 1. Recarga volvía al login

- **Causa raíz:** La sesión vivía solo en memoria JS. `setAuthed(true)` forzaba el dashboard y no había guard de arranque que llamara a `/auth/me`. No era un fallo de emisión JWT en backend.
- **Archivos:** `app/frontend/js/api.js`, `app/frontend/js/app.js`, `app/frontend/index.html`
- **Corrección:** Persistencia `siga.lab.session`; arranque `ensureSession()` → `GET /auth/me`; si 401, `POST /auth/refresh`; máscara de boot hasta comprobar. Si el token es inválido se limpia y se muestra login.
- **Prueba:** login 200, `/auth/me` 200 con el mismo access; refresh 200; token basura 401.
- **Estado:** CORREGIDO

### 2. Barra de módulos sin historial / Atrás-Adelante

- **Causa raíz:** Paneles con `display` y botones `type=button` sin URL. El navegador no tenía historial de módulo.
- **Archivos:** `index.html`, `app.js`, `main.css`
- **Corrección:** Router hash `#/home|login|registro|dashboard|grades|attendance|ai|notifications|catalog|reports|profile`; enlaces `<a href="#/…">`; `hashchange`.
- **Estado:** CORREGIDO

### 3. Login con error silencioso / 405

- **Causa raíz:** GET a `/auth/login` o submit nativo; 401 no se traducía a un mensaje de UI estable.
- **Archivos:** `index.html` (bootstrap POST JSON), `app.js` `friendlyLoginError`
- **Corrección:** Mensaje **«Credenciales incorrectas. Verifica tu usuario y contraseña.»** en 401. Vacío, 422, 429, red y backend caído tienen textos propios. No recarga la página.
- **Estado:** CORREGIDO

### 4. Registro

- **Causa raíz:** No existe endpoint público de registro (spec RF-IAM-001 = CRUD admin).
- **Corrección:** Vista pública `#/registro` (cuentas seed). Alta real: Catálogo → `POST /users` (admin). Estudiante recibe 403 DENY.
- **Estado:** CORREGIDO (sin inventar auto-registro)

### 5. Perfil / cerrar sesión

- **Causa:** No había superficie de perfil ni invalidación visible del refresh.
- **Corrección:** `#/profile` con `GET /auth/me`. Cerrar sesión llama `POST /auth/logout`, borra localStorage y hash `#/login`.
- **Estado:** CORREGIDO

## Backend

No se cambió el contrato de auth. El 401/403/204 ya cumplían spec. El fallo de persistencia y navegación era de Frontend (estado + routing).

## Arquitectura frontend (A01) — multi-página

```
app/frontend/
├── index.html          → redirige a pages/home.html
├── pages/              → HTML independientes (Bootstrap + CSS)
│   ├── home.html, login.html, registro.html
│   └── dashboard.html, grades.html, attendance.html, ai.html,
│       notifications.html, catalog.html, reports.html, profile.html
├── css/main.css
└── js/
    ├── api.js, ui-common.js, auth-guard.js
    └── pages/*.js      → solo fetch + rellenar DOM existente
```

Entrada: http://127.0.0.1:8000/ui/pages/home.html  
Login: http://127.0.0.1:8000/ui/pages/login.html (`admin` / `Admin123!`)

## Cómo verificar en el navegador

1. Reinicia `start-siga.bat` (o uvicorn) y abre http://127.0.0.1:8000/ui/pages/home.html (Ctrl+F5)
2. Login → Dashboard (página HTML real, no hash SPA)
3. Navega por enlaces del menú (`/ui/pages/grades.html`, etc.)
4. Recarga: JWT en `localStorage` + `auth-guard.js` restaura sesión vía `/auth/me`
5. Perfil → Cerrar sesión → vuelve a `login.html`
