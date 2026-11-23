# PROMPTSMASTER — Sistema de Gestión Académica Institucional

> Metodología: **Spec as Skill** | Agente IA: **DeepSeek** | Stack: Python · Flask · MySQL · Bootstrap · JS

---

## 📌 Descripción General del Proyecto

Sistema web de gestión académica institucional construido con un agente de inteligencia artificial basado en el modelo **DeepSeek**, capaz de gestionar de forma completa y autónoma todos los módulos del sistema. El sistema aplica roles y permisos granulares, seguridad OWASP Top 10 2025, diseño moderno y tecnológico, y es completamente configurable desde el panel de administración.

---

## 🗂️ Estructura del Proyecto (Spec as Skill)

```
/
├── Spec/                        → Especificaciones del sistema
│   ├── SPEC-001-arquitectura.md
│   ├── SPEC-002-seguridad.md
│   ├── SPEC-003-roles-permisos.md
│   ├── SPEC-004-modulos.md
│   ├── SPEC-005-agente-ia.md
│   ├── SPEC-006-ui-ux.md
│   ├── SPEC-007-base-datos.md
│   ├── SPEC-008-impersonacion.md
│   ├── SPEC-009-visibilidad-perfil.md
│   ├── SPEC-010-tema-institucional.md
│   ├── SPEC-011-seeder-academico-coherente.md
│   ├── SPEC-012-materias-docente.md
│   ├── SPEC-013-proveedores-ia.md
│   ├── SPEC-014-dashboard-restringido.md
│   ├── SPEC-015-asistencia-roster-cupo.md
│   ├── SPEC-016-agente-gateway-crud.md
│   ├── SPEC-017-conversaciones-reportes-ia.md
│   ├── SPEC-018-fix-persistencia-chat.md
│   ├── SPEC-019-filtros-export-modulos.md
│   ├── SPEC-020-historial-conversaciones-ia.md
│   ├── SPEC-021-descarga-directa-artifacts.md
│   ├── SPEC-022-respuestas-fluida-agente.md
│   ├── SPEC-023-sanitizar-markup-tools-dsml.md
│   ├── SPEC-024-editar-eliminar-conversaciones.md
│   ├── SPEC-025-fix-pdf-agente.md
│   ├── SPEC-026-modulo-logia.md
│   ├── SPEC-027-typing-apa7-presentacion.md
│   ├── SPEC-028-bloqueos-seguridad-logia-audit.md
│   ├── SPEC-029-logia-pregunta-bloqueo-escalada.md
│   ├── SPEC-030-minimo-privilegio-tools-intent.md
│   └── SPEC-031-modo-inseguro-laboratorio.md
│
├── Skill/                       → Habilidades del agente IA
│   ├── SKILL-001-arquitecto-flask.md
│   ├── SKILL-002-auditor-seguridad.md
│   ├── SKILL-003-modelador-bd.md
│   ├── SKILL-004-desarrollador-modulos.md
│   ├── SKILL-005-integrador-ia.md
│   ├── SKILL-006-disenador-ui.md
│   ├── SKILL-007-gestor-roles.md
│   ├── SKILL-008-implementador-visibilidad.md
│   ├── SKILL-009-tema-institucional.md
│   ├── SKILL-010-sembrador-academico.md
│   ├── SKILL-011-materias-docente.md
│   ├── SKILL-012-proveedores-ia.md
│   ├── SKILL-013-dashboard-restringido.md
│   ├── SKILL-014-asistencia-roster-cupo.md
│   ├── SKILL-015-agente-gateway-crud.md
│   ├── SKILL-016-conversaciones-reportes-ia.md
│   ├── SKILL-017-fix-persistencia-chat.md
│   ├── SKILL-018-filtros-export-modulos.md
│   ├── SKILL-019-historial-conversaciones-ia.md
│   ├── SKILL-020-descarga-directa-artifacts.md
│   ├── SKILL-021-respuestas-fluida-agente.md
│   ├── SKILL-022-sanitizar-markup-tools-dsml.md
│   ├── SKILL-023-editar-eliminar-conversaciones.md
│   ├── SKILL-024-fix-pdf-agente.md
│   ├── SKILL-025-modulo-logia.md
│   ├── SKILL-026-typing-apa7-presentacion.md
│   ├── SKILL-027-bloqueos-seguridad-logia-audit.md
│   ├── SKILL-028-logia-pregunta-bloqueo-escalada.md
│   ├── SKILL-029-minimo-privilegio-tools-intent.md
│   └── SKILL-030-modo-inseguro-laboratorio.md
│
└── App/                         → Código fuente del sistema
    ├── backend/
    │   ├── app/
    │   │   ├── api/
    │   │   ├── auth/
    │   │   ├── models/
    │   │   ├── services/
    │   │   ├── permissions/
    │   │   └── ai/
    ├── frontend/
    │   ├── templates/
    │   ├── static/
    │   │   ├── css/
    │   │   ├── js/
    │   │   └── assets/
    └── database/
        ├── migrations/
        └── seeds/
```

---

## ⚙️ Stack Tecnológico

| Capa | Tecnología | Versión sugerida |
| --- | --- | --- |
| Backend | Python + Flask | 3.11+ / Flask 3.x |
| Base de datos | MySQL + XAMPP | MySQL 8.x |
| ORM | SQLAlchemy + Flask-Migrate | Latest |
| Autenticación | JWT (Flask-JWT-Extended) | Latest |
| Frontend | HTML5 + CSS3 + Bootstrap | Bootstrap 5.3 |
| Interactividad | JavaScript (Vanilla + Fetch API) | ES2023 |
| Agente IA | DeepSeek API | deepseek-chat / deepseek-coder |
| Seguridad | OWASP Top 10 2025 | — |
| Estilos | CSS Variables + Dark/Light Mode | — |

---

## 📁 ESPECIFICACIONES — Carpeta `Spec/`

---

### SPEC-001 — Arquitectura General

**Objetivo:** Definir la estructura y arquitectura del sistema web.

- Arquitectura MVC con Flask Blueprints por módulo.
- API RESTful con prefijo `/api/v1/`.
- Autenticación stateless con JWT (access token + refresh token).
- Separación total entre backend (API) y frontend (templates Jinja2 + JS).
- Configuración centralizada en `.env` y tabla `system_config` en base de datos.
- Sistema multirrol con permisos granulares por módulo y acción.
- Soporte completo para modo claro y oscuro (CSS variables + localStorage).
- El agente IA tiene acceso a todos los módulos mediante endpoints protegidos.

**Modelos de IA para esta spec:** Claude Sonnet, GPT-4o

---

### SPEC-002 — Seguridad (OWASP Top 10 2025)

**Objetivo:** Garantizar la seguridad del sistema en todos sus niveles.

| # | Riesgo OWASP | Mitigación implementada |
| --- | --- | --- |
| A01 | Broken Access Control | Permisos granulares verificados en cada endpoint |
| A02 | Cryptographic Failures | Contraseñas con bcrypt, JWT firmado RS256, HTTPS |
| A03 | Injection | ORM con parámetros preparados, sanitización de inputs |
| A04 | Insecure Design | Especificaciones de seguridad desde el diseño |
| A05 | Security Misconfiguration | Variables de entorno, cabeceras de seguridad |
| A06 | Vulnerable Components | Dependencias auditadas y actualizadas |
| A07 | Auth & Identity Failures | JWT + refresh, bloqueo por intentos fallidos |
| A08 | Software Integrity | Validación de integridad en actualizaciones |
| A09 | Logging & Monitoring | Auditoría completa de eventos críticos |
| A10 | SSRF | Validación de URLs externas en integración IA |

**Reglas adicionales:**

- Cabeceras HTTP de seguridad: `X-Frame-Options`, `CSP`, `HSTS`, `X-Content-Type-Options`.
- Rate limiting en endpoints de login y API IA.
- Tokens de impersonación con tiempo de vida limitado.
- Validación de API Key de DeepSeek desde administración, nunca expuesta al frontend.
- Logs de seguridad con IP, timestamp, usuario y acción.

**Modelos de IA para esta spec:** Claude Opus, GPT-o1

---

### SPEC-003 — Roles y Permisos Granulares

**Objetivo:** Definir todos los roles del sistema y sus niveles de acceso.

#### 🎭 Roles del Sistema

| # | Rol | Código | Descripción |
| --- | --- | --- | --- |
| 1 | Administrador General | `ADMIN` | Control total del sistema, configuración, usuarios, IA |
| 2 | Rector / Director | `RECTOR` | Supervisión institucional, reportes globales, sin edición |
| 3 | Coordinador Académico | `COORDINATOR` | Gestión de carreras, mallas, horarios, cursos |
| 4 | Docente | `TEACHER` | Registro de notas, asistencia, visualización de cursos asignados |
| 5 | Estudiante | `STUDENT` | Consulta de notas, asistencia, horarios y kardex propio |
| 6 | Secretaría / Administrativo | `SECRETARY` | Matrículas, registros de estudiantes, reportes administrativos |
| 7 | Revisor | `REVIEWER` | Revisión de notas y asistencia sin edición, solo lectura con observaciones |
| 8 | Auditor | `AUDITOR` | Acceso a logs, historial, eventos de seguridad, reportes de auditoría |
| 9 | Tutor / Representante | `GUARDIAN` | Consulta de notas y asistencia del estudiante a su cargo |
| 10 | Soporte TI | `IT_SUPPORT` | Gestión técnica del sistema, configuración, sin acceso a datos académicos sensibles |

---

#### 🔐 Módulos IAM y Permisos Granulares (22 módulos)

| Módulo | Acciones | Descripción |
| --- | --- | --- |
| `users` | `view`, `create`, `edit`, `delete`, `login-as` | Gestión de usuarios e impersonación |
| `roles` | `view`, `create`, `edit`, `delete` | Gestión de roles |
| `permissions` | `view`, `create`, `edit`, `delete`, `assign` | Catálogo y asignación de permisos |
| `students` | `view`, `create`, `edit` | Gestión de estudiantes |
| `teachers` | `view`, `create`, `edit` | Gestión de docentes |
| `careers` | `view`, `create`, `edit` | Carreras institucionales |
| `subjects` | `view`, `create`, `edit` | Materias y asignaturas |
| `curriculum` | `view`, `manage` | Mallas curriculares |
| `terms` | `view`, `create`, `edit` | Periodos académicos |
| `courses` | `view`, `create`, `edit` | Cursos y paralelos |
| `assignments` | `view`, `manage` | Asignaciones docente–curso |
| `enrollments` | `view`, `create`, `edit` | Matrículas estudiantiles |
| `schedules` | `view`, `create`, `edit` | Horarios de clases |
| `grades` | `view`, `manage` | Calificaciones y notas |
| `attendance` | `view`, `manage` | Registro de asistencia |
| `kardex` | `view`, `export` | Kárdex académico del estudiante |
| `dashboard` | `view` | Panel principal con métricas |
| `reports` | `view`, `export`, `schedule` | Reportes académicos e institucionales |
| `notifications` | `view`, `send` | Avisos y notificaciones |
| `history` | `view` | Historial de actividad del usuario |
| `ai` | `use`, `configure`, `view_logs` | Asistente IA y configuración del modelo |
| `audit` | `view` | Auditoría y registros de seguridad |

---

### SPEC-004 — Módulos del Sistema

**Objetivo:** Describir el comportamiento funcional de cada módulo.

#### 4.1 Módulo de Autenticación (`/auth`)

- Login con usuario y contraseña.
- Generación de JWT (access 15 min + refresh 7 días).
- Bloqueo tras 5 intentos fallidos (15 minutos).
- Logout con revocación de refresh token.
- Cambio de contraseña obligatorio en primer acceso.

#### 4.2 Módulo de Usuarios (`/users`)

- CRUD completo de usuarios (solo desde administración).
- Asignación de roles y permisos granulares.
- Activar / desactivar usuarios.
- Impersonación con permiso `users.login-as`.
- Historial de sesiones por usuario.

#### 4.3 Módulo de Estudiantes (`/students`)

- Registro desde administración o secretaría.
- Datos personales, contacto, representante/tutor.
- Vinculación automática a carrera y periodo activo.
- Generación de credenciales de acceso al sistema.
- Vista de perfil para el propio estudiante (solo lectura).

#### 4.4 Módulo de Docentes (`/teachers`)

- Registro con perfil profesional y materias habilitadas.
- Asignación a cursos y paralelos por periodo.
- Visualización de cursos, horarios y estudiantes asignados.
- Registro de notas y asistencia en sus cursos.

#### 4.5 Módulo de Carreras, Periodos y Materias

- **Carreras:** CRUD con descripción, duración y estado.
- **Periodos académicos:** CRUD con fechas de inicio/fin y estado activo.
- **Materias:** CRUD con código, nombre, créditos y carrera asociada.
- **Mallas curriculares:** asignación de materias por carrera y nivel.

#### 4.6 Módulo de Cursos y Horarios

- **Cursos/Paralelos:** definición por materia, periodo y carrera.
- **Asignaciones:** docente asignado a cada curso.
- **Horarios:** día, hora inicio/fin, aula, docente, curso.
- **Cronogramas:** vista semanal visual para docentes y estudiantes.

#### 4.7 Módulo de Matrículas (`/enrollments`)

- Matrícula de estudiantes a cursos del periodo activo.
- Validación de requisitos previos (malla curricular).
- Generación de comprobante de matrícula.
- Estado: activa, retirada, congelada.

#### 4.8 Módulo de Notas (`/grades`)

**Reglas de calificación:**

| Tipo | Descripción | Condición |
| --- | --- | --- |
| Primer Parcial | Nota 1–10 | Siempre habilitado |
| Segundo Parcial | Nota 1–10 | Siempre habilitado |
| Supletorio | Nota 1–10 | Solo si promedio \< 7.0 |

- Promedio = (Primer Parcial + Segundo Parcial) / 2.
- Si promedio \< 7.0 → habilitar campo Supletorio automáticamente.
- Nota final: si hay supletorio → nota supletorio es la definitiva.
- Solo el docente asignado puede ingresar notas de su curso.
- Cierre de notas por periodo: solo admin puede reabrir.
- Registro de auditoría en cada modificación de nota.

#### 4.9 Módulo de Asistencia (`/attendance`)

- Registro por clase/sesión: presente, ausente, tardanza, justificada.
- Solo el docente del curso puede registrar asistencia.
- Alerta automática al superar 25% de faltas.
- Reportes de asistencia por estudiante, curso y periodo.

#### 4.10 Módulo de Kárdex (`/kardex`)

- Vista consolidada del historial académico del estudiante.
- Notas por materia, periodo y estado (aprobado/reprobado).
- Exportable en PDF.
- Accessible para el estudiante, docentes asignados, secretaría y admin.

#### 4.11 Módulo de Reportes (`/reports`)

- Reporte de notas por curso, carrera y periodo.
- Reporte de asistencia.
- Reporte de matrículas.
- Reporte de usuarios activos.
- Exportación en PDF y Excel.
- Programación de reportes automáticos.

#### 4.12 Módulo de Notificaciones (`/notifications`)

- Notificaciones internas del sistema (campana en navbar).
- Envío de avisos por rol o usuario específico.
- Alertas automáticas: notas ingresadas, asistencia crítica, nuevo periodo.

#### 4.13 Módulo de Auditoría (`/audit`)

- Log de todos los eventos críticos: login, logout, cambio de notas, impersonación, cambio de configuración.
- Filtros por usuario, acción, módulo, fecha.
- Solo visible para roles `AUDITOR` y `ADMIN`.
- No editable ni eliminable (append-only).

---

### SPEC-005 — Agente de Inteligencia Artificial

**Objetivo:** Integrar el modelo DeepSeek como agente capaz de gestionar todo el sistema.

**Capacidades del agente:**

- Consultar, crear, editar y eliminar datos en cualquier módulo vía API interna.
- Responder preguntas sobre el estado del sistema (notas, asistencia, estudiantes, etc.).
- Generar reportes y resúmenes en lenguaje natural.
- Detectar anomalías (estudiantes con muchas faltas, notas bajas, sin matrícula).
- Ejecutar acciones administrativas bajo confirmación del usuario autorizado.
- Configurarse desde el panel de administración (API Key, modelo, temperatura, instrucción base).

**Seguridad del agente:**

- La API Key de DeepSeek se almacena cifrada en base de datos (AES-256).
- Nunca se expone al frontend.
- El agente actúa con los permisos del usuario autenticado que lo invoca.
- Todas las acciones del agente se registran en auditoría.

**Endpoint principal:**

```
POST /api/v1/ai/chat
Authorization: Bearer <token>
Body: { "message": "...", "context": "..." }
```

**Modelos de IA para esta spec:** Claude Opus, GPT-o1

---

### SPEC-006 — Interfaz de Usuario (UI/UX)

**Objetivo:** Definir los estándares visuales y de usabilidad del sistema.

- Diseño moderno, tecnológico y limpio basado en Bootstrap 5.3.
- Paleta de colores configurable desde administración (CSS variables dinámicas).
- Modo claro y oscuro con toggle en navbar (persistido en `localStorage` y base de datos).
- Sidebar colapsable con íconos y etiquetas.
- Navbar fija con: nombre del sistema, usuario activo, notificaciones, toggle de tema, menú de perfil.
- Banner de impersonación fijo (visible en todas las páginas cuando aplica).
- Tablas con búsqueda, paginación y exportación.
- Formularios con validación en tiempo real (frontend + backend).
- Feedback visual: loaders, toasts de éxito/error, modales de confirmación.
- Dashboard con tarjetas de métricas, gráficas y accesos rápidos.
- Diseño responsive: funcional en escritorio, tablet y móvil.
- Fuentes: Inter o Poppins (Google Fonts).
- Íconos: Bootstrap Icons o Lucide.

**Modelos de IA para esta spec:** Claude Sonnet, Gemini Flash

---

### SPEC-007 — Base de Datos

**Objetivo:** Definir el modelo de datos del sistema.

**Motor:** MySQL 8.x gestionado con XAMPP. **ORM:** SQLAlchemy con migraciones Alembic.

**Tablas principales:**

| Tabla | Descripción |
| --- | --- |
| `users` | Usuarios del sistema |
| `roles` | Roles disponibles |
| `permissions` | Permisos granulares |
| `role_permissions` | Relación rol–permiso |
| `user_roles` | Relación usuario–rol |
| `students` | Datos de estudiantes |
| `teachers` | Datos de docentes |
| `careers` | Carreras institucionales |
| `subjects` | Materias |
| `curriculum` | Malla curricular |
| `terms` | Periodos académicos |
| `courses` | Cursos/paralelos |
| `assignments` | Docente asignado a curso |
| `enrollments` | Matrículas |
| `schedules` | Horarios |
| `grades` | Notas (parcial1, parcial2, supletorio) |
| `attendance` | Registro de asistencia |
| `notifications` | Notificaciones internas |
| `audit_logs` | Log de auditoría (append-only) |
| `refresh_tokens` | Tokens de sesión con impersonator_id |
| `system_config` | Configuración global del sistema |
| `ai_config` | Configuración del agente IA |
| `ai_logs` | Historial de conversaciones con el agente |
| `ai_conversations` / `ai_messages` / `ai_artifacts` | Chat persistente, mensajes y reportes generados |
| `ai_agent_logs` | LogIA — auditoría del agente + anti prompt-injection |

**Modelos de IA para esta spec:** Claude Opus, GPT-o1

---

### SPEC-008 — Impersonación de Usuarios

**Objetivo:** Permitir al administrador acceder temporalmente a la sesión de cualquier usuario activo.

**Flujo:**

```
Admin → Usuarios → botón "Entrar" (fila del usuario)
      → modal de confirmación
      → POST /api/v1/users/{id}/login-as
      → nuevos tokens con impersonator_id en claim JWT
      → redirigir al dashboard del usuario impersonado
      → banner: "Viendo como {usuario}" + botón "Regresar a mi cuenta"
      → POST /api/v1/auth/return-to-admin
      → restaurar tokens del admin
      → registrar evento IMPERSONATION_END en auditoría
```

**Restricciones:**

- Solo disponible con permiso `users.login-as`.
- No se puede impersonar: la propia cuenta, cuentas admin protegidas, usuarios inactivos.
- No se permite impersonación anidada (`ALREADY_IMPERSONATING`).
- El banner de impersonación debe ser visible en todas las páginas.
- Se registran eventos `IMPERSONATION_START` y `IMPERSONATION_END` en auditoría.

**Claim JWT durante impersonación:**

```json
{
  "sub": "<id del usuario impersonado>",
  "roles": ["TEACHER"],
  "permissions": ["..."],
  "impersonator_id": <id del admin>
}
```

---

## 📁 HABILIDADES — Carpeta `Skill/`

---

### SKILL-001 — Arquitecto Flask

**Spec asociada:** SPEC-001\
**Rol del agente:** Arquitecto de software backend

El agente debe diseñar y construir la estructura del proyecto Flask con Blueprints por módulo, configurar el ORM, las migraciones, el sistema de rutas y la configuración por entorno. Debe garantizar que el proyecto sea modular, escalable y separado por responsabilidades.

**Modelo sugerido:** Claude Opus

---

### SKILL-002 — Auditor de Seguridad

**Spec asociada:** SPEC-002\
**Rol del agente:** Especialista en seguridad web

El agente debe aplicar todas las medidas del OWASP Top 10 2025, implementar cabeceras de seguridad, validar inputs, gestionar tokens JWT de forma segura, implementar rate limiting y registrar todos los eventos de seguridad en auditoría.

**Modelo sugerido:** Claude Opus

---

### SKILL-003 — Modelador de Base de Datos

**Spec asociada:** SPEC-007\
**Rol del agente:** DBA y modelador de datos

El agente debe crear todos los modelos SQLAlchemy, relaciones entre tablas, índices, constraints de integridad referencial y scripts de seed iniciales (roles, permisos, usuario admin).

**Modelo sugerido:** GPT-o1

---

### SKILL-004 — Desarrollador de Módulos

**Spec asociada:** SPEC-004\
**Rol del agente:** Desarrollador fullstack (Flask + JS)

El agente debe construir cada módulo del sistema (CRUD, validaciones, reglas de negocio) siguiendo la spec correspondiente. Cada módulo incluye: modelo, servicio, endpoint API, template HTML y lógica JS.

**Modelo sugerido:** Claude Fable

---

### SKILL-005 — Integrador de IA (DeepSeek)

**Spec asociada:** SPEC-005\
**Rol del agente:** Ingeniero de integración IA

El agente debe integrar la API de DeepSeek, gestionar el contexto de conversación, conectar el chat con los servicios del sistema y garantizar que todas las acciones del agente queden registradas en auditoría. Debe manejar errores de API, rate limits y timeouts.

**Modelo sugerido:** Claude Opus

---

### SKILL-006 — Diseñador UI/UX

**Spec asociada:** SPEC-006\
**Rol del agente:** Diseñador frontend moderno

El agente debe construir todas las templates HTML con Bootstrap 5.3, implementar el sistema de temas claro/oscuro con CSS variables, el sidebar, el navbar, el banner de impersonación, los dashboards y los formularios según los estándares visuales definidos.

**Modelo sugerido:** Claude Sonnet, Gemini Flash

---

### SKILL-007 — Gestor de Roles y Permisos

**Spec asociada:** SPEC-003\
**Rol del agente:** Especialista en IAM

El agente debe implementar el sistema de roles y permisos granulares, los decoradores de autorización en Flask, los seeds de roles y permisos iniciales, y la UI de gestión de roles desde administración.

**Modelo sugerido:** GPT-o1

---

## 🔑 Regla Principal

> **No se programa, no se codifica, ni se corrige nada que no esté en las especificaciones y sin la skill correcta para el agente.**

```
Necesidad detectada
       ↓
Crear / actualizar Spec en Spec/
       ↓
Crear / actualizar Skill en Skill/
       ↓
El agente ejecuta en App/ usando Spec + Skill
       ↓
Validación, prueba y documentación
```

---

## 📊 Tabla de Modelos por Actividad

| Actividad | Tipo | Modelos sugeridos |
| --- | --- | --- |
| Crear especificaciones | Descriptivo | Claude Sonnet, GPT-4o, Gemini Flash, Grok |
| Crear skills | Fundamental | Claude Opus, GPT-o1 |
| Codificar módulos | Codificador | Claude Fable, GPT-Astra |
| Diseño UI/UX | Descriptivo | Claude Sonnet, Gemini Flash |
| Seguridad y auditoría | Fundamental | Claude Opus, GPT-o1 |
| Integración IA DeepSeek | Fundamental + Codificador | Claude Opus + Claude Fable |

---

## 🚀 Orden de Construcción Recomendado

```
1. Base de datos y modelos (SPEC-007 + SKILL-003)
2. Autenticación JWT y roles (SPEC-002, SPEC-003 + SKILL-002, SKILL-007)
3. Módulo de usuarios e impersonación (SPEC-008 + SKILL-004)
4. Módulos académicos: carreras, periodos, materias, cursos (SPEC-004 + SKILL-004)
5. Módulos de docentes y estudiantes (SPEC-004 + SKILL-004)
6. Matrículas, horarios y asignaciones (SPEC-004 + SKILL-004)
7. Notas y asistencia con reglas de negocio (SPEC-004 + SKILL-004)
8. Kárdex y reportes (SPEC-004 + SKILL-004)
9. Integración DeepSeek (SPEC-005 + SKILL-005)
10. Panel de administración y configuración (SPEC-001, SPEC-006 + SKILL-006)
11. Auditoría y notificaciones (SPEC-004 + SKILL-002)
12. UI/UX final, temas y responsive (SPEC-006 + SKILL-006)
13. Pruebas de seguridad OWASP (SPEC-002 + SKILL-002)
```

---

## 📎 Convenciones del Proyecto

- `Spec/` → `SPEC-[ID]-[nombre].md`
- `Skill/` → `SKILL-[ID]-[nombre].md`
- `App/CHANGELOG.md` → registro de cada acción del agente con spec y skill usadas.
- Ningún cambio en `App/` sin entrada en `Spec/` y `Skill/`.
- Cada endpoint documentado con método, ruta, permisos requeridos y respuesta esperada.
- Variables de entorno en `.env.example` documentadas.

---

## ✅ Checklist de Entrega

- [ ] Base de datos creada con todas las tablas y seeds.
- [ ] Login funcional con JWT + bloqueo por intentos.
- [ ] Roles y permisos granulares aplicados en todos los endpoints.
- [ ] Módulos académicos completos (carreras, periodos, materias, cursos, horarios).
- [ ] Registro de notas con regla de supletorio (\< 7.0).
- [ ] Registro de asistencia por docente y curso.
- [ ] Kárdex académico con exportación PDF.
- [ ] Reportes exportables (PDF + Excel).
- [ ] Agente DeepSeek integrado y funcional.
- [ ] Panel de administración con configuración de colores, IA y modo de tema.
- [ ] Impersonación con banner y botón de retorno.
- [ ] Modo claro/oscuro con persistencia.
- [ ] OWASP Top 10 2025 aplicado y verificado.
- [ ] Auditoría completa de eventos críticos.
- [ ] Diseño responsive y moderno en todos los módulos.
- [ ] Notificaciones internas funcionales.
- [ ] Documentación de endpoints y modelos actualizada.

---

> *Spec as Skill — Sistema Académico con IA · Construye con intención. Documenta con precisión. Escala con confianza.*