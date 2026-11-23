# Permisos, roles y seguridad del agente IA

Documento de referencia del **Sistema de Gestión Académica**: qué roles existen, qué puede hacer cada uno y cómo se aplican los controles de seguridad cuando el usuario interactúa con el **asistente IA**.

Fuentes principales: `App/database/seeds/seed_data.py`, `App/backend/app/models/iam.py`, `App/backend/app/permissions/decorators.py`, `App/backend/app/ai/gateway/*`, `App/backend/app/services/visibility.py`, specs SPEC-003 / SPEC-009 / SPEC-014 / SPEC-016.

---

## 1. Modelo de seguridad (capas)

| Capa | Qué controla | Cómo |
| --- | --- | --- |
| **JWT + claims** | Acceso a endpoints HTTP (`/api/v1/...`) | Decoradores `permission_required` / `any_permission_required`. El token lleva `roles` y `permissions`. |
| **Modelo `User.has_permission`** | Tools del agente IA, reportes, lógica de negocio | Consulta roles/permisos en BD (en vivo). `ADMIN` = acceso total. |
| **Visibilidad (scope)** | Qué filas ve un usuario (cursos, periodos, notas…) | `visible_term_ids`, `owned_course_ids`, `apply_course_scope`. |
| **Agente IA (gateway)** | Qué tools puede invocar y si muta datos | Registro de tools + permiso por tool + confirmación en mutaciones. |
| **Frontend** | Menús y botones | `hasPerm()`: rol `ADMIN` o permiso en el payload de login. |

**Importante:** tras cambiar roles/permisos en BD, el usuario debe **volver a iniciar sesión** para refrescar el JWT. El agente IA, en cambio, usa `has_permission` sobre la BD, así que refleja cambios sin re-login.

---

## 2. Roles del sistema

| Código | Nombre | Enfoque |
| --- | --- | --- |
| `ADMIN` | Administrador General | Control total (bypass de permisos) |
| `RECTOR` | Rector / Director | Supervisión e informes |
| `COORDINATOR` | Coordinador Académico | Gestión académica |
| `TEACHER` | Docente | Sus cursos: notas y asistencia |
| `STUDENT` | Estudiante | Solo sus datos |
| `SECRETARY` | Secretaría | Matrículas y registros |
| `REVIEWER` | Revisor | Lectura / revisión |
| `AUDITOR` | Auditor | Logs y auditoría |
| `GUARDIAN` | Tutor / Representante | Consulta del estudiante a cargo |
| `IT_SUPPORT` | Soporte TI | Usuarios, roles, config IA |

---

## 3. Catálogo de permisos (`módulo.acción`)

Formato: `{module}.{action}` (ej. `grades.manage`, `ai.use`).

| Módulo | Acciones típicas |
| --- | --- |
| `users` | `view`, `create`, `edit`, `delete`, `login-as` |
| `roles` / `permissions` | `view`, `create`, `edit`, `delete` (+ `assign` en permissions) |
| `students` / `teachers` | `view`, `create`, `edit` |
| `careers` / `subjects` / `terms` / `courses` / `schedules` | `view`, `create`, `edit` |
| `curriculum` | `view`, `manage` |
| `assignments` | `view`, `manage` |
| `enrollments` | `view`, `create`, `edit` |
| `grades` / `attendance` | `view`, `manage` |
| `kardex` | `view`, `export` |
| `dashboard` | `view` |
| `reports` | `view`, `export`, `schedule` |
| `notifications` | `view`, `send` |
| `history` | `view` |
| `audit` | `view` |
| **`ai`** | **`use`**, **`configure`**, **`view_logs`** |

---

## 4. Matriz resumida por rol (permisos clave)

| Rol | Dashboard | Académico (lectura) | Mutaciones fuertes | Reportes | IA |
| --- | --- | --- | --- | --- | --- |
| **ADMIN** | Sí (todo) | Todo | Todo | Todo | `use`, `configure`, `view_logs` |
| **RECTOR** | Sí | Amplia (view) | No típicas | `view`/`export` | `use` |
| **COORDINATOR** | Sí | Carreras, cursos, periodos, etc. | Gestión académica | `view`/`export` | `use` |
| **TEACHER** | **No** | Solo sus cursos (scope) | Notas/asistencia de sus cursos | Limitado | `use` |
| **STUDENT** | **No** | Solo lo propio | No | No típicos | `use` |
| **SECRETARY** | Sí | Estudiantes, matrículas… | Matrículas / registros | `view`/`export` + kárdex | `use` |
| **REVIEWER** | Sí | Lectura (notas, asistencia…) | No | `view` | — (sin `ai.use` en seed) |
| **AUDITOR** | Sí | Enfoque logs | No | `view`/`export` | `view_logs` (no `use` en seed) |
| **GUARDIAN** | **No** | Notas/asistencia/kárdex/horarios | No | — | — (sin `ai.use` en seed) |
| **IT_SUPPORT** | Sí | Usuarios/roles (view/edit) | Usuarios | — | `configure`, `view_logs` |

Notas de seed / sync de visibilidad:

- **STUDENT** y **TEACHER** no tienen `dashboard.view` ni `kardex.*`.
- **GUARDIAN** tampoco tiene `dashboard.view`.
- Roles con **`ai.use`** habitualmente: ADMIN, RECTOR, COORDINATOR, TEACHER, STUDENT, SECRETARY.

---

## 5. Permisos específicos de IA

| Permiso | Quién lo usa | Para qué |
| --- | --- | --- |
| `ai.use` | Roles operativos (arriba) | Chat, conversaciones, artifacts, tools del gateway |
| `ai.configure` | ADMIN, IT_SUPPORT | Configurar proveedor / API key / modelo |
| `ai.view_logs` | ADMIN, AUDITOR, IT_SUPPORT | Ver **LogIA** (auditoría del agente, bloqueos anti prompt-injection) |

Endpoints típicos:

- `POST /api/v1/ai/chat`, conversaciones (incl. renombrar/eliminar) → `ai.use`
- Config IA → `ai.configure`
- **LogIA** `GET /api/v1/ai/agent-logs` + `export.xlsx|pdf|json` → `ai.view_logs`
- Descarga de reportes generados por el agente → URL firmada **o** JWT del dueño / ADMIN (+ `ai.use` si no es admin)

---

## 6. Cómo el agente IA aplica seguridad

El flujo es:

1. El usuario debe tener **`ai.use`** para hablar con el asistente.
2. El LLM propone una **tool** (o se parsea markup DSML interno; ese markup **nunca** se muestra al usuario).
3. El **executor** comprueba:
   - ¿La tool existe?
   - ¿El usuario tiene el permiso requerido de esa tool? (`User.has_permission`)
   - ¿Es **mutante**? → pide **confirmación** (`confirma`, `sí`, `ok`, …) antes de ejecutar.
4. Los handlers aplican **scope** adicional (cursos/periodos propios, estudiante solo ve lo suyo).
5. Si falta permiso → error claro; opcionalmente se contempla elevación (ver limitaciones).

### Confirmación de mutaciones

Tools que **cambian datos** no se aplican al primer intento. El sistema responde pidiendo confirmación. Solo tras confirmar se escribe en BD.

Ejemplos mutantes: `enrollments_create`, `grades_upsert`, `attendance_upsert`, `careers_create`, `users_assign_roles`, etc.

### Visibilidad dentro del agente

| Perfil | Efecto en tools de listado / upsert |
| --- | --- |
| Staff (ADMIN, RECTOR, COORDINATOR, SECRETARY, …) | Suele ver datos amplios según permiso |
| **TEACHER** | Solo cursos asignados y periodos activos |
| **STUDENT** | Solo sus matrículas / notas / asistencia |
| Periodos inactivos | Ocultos para roles restringidos |

Esto alinea el chat con las mismas reglas que la UI (SPEC-009 / SPEC-014).

---

## 7. Tools del agente y permisos requeridos

| Tool | Permiso del executor | ¿Mutante? | Notas |
| --- | --- | --- | --- |
| `system_stats` | *(ninguno)* | No | Conteos globales; ver limitaciones |
| `careers_list` / `careers_get` | `careers.view` | No | |
| `careers_create` | `careers.create` | **Sí** | |
| `subjects_list` | `subjects.view` | No | |
| `terms_list` | `terms.view` | No | Filtra periodos visibles |
| `courses_list` | `courses.view` | No | Scope de cursos |
| `students_list` | `students.view` | No | Scope / propios |
| `teachers_list` | `teachers.view` | No | |
| `enrollments_list` | `enrollments.view` | No | Scope; STUDENT → propios |
| `enrollments_create` | `enrollments.create` | **Sí** | Cupo / validaciones |
| `grades_list` | `grades.view` | No | Scope |
| `grades_upsert` | `grades.manage` | **Sí** | Solo cursos propios (docente) |
| `attendance_list` | `attendance.view` | No | Scope |
| `attendance_upsert` | `attendance.manage` | **Sí** | Solo cursos propios |
| `users_list` | `users.view` | No | Soporta búsqueda; sin passwords |
| `roles_list` | `roles.view` | No | |
| `users_assign_roles` | `users.edit` | **Sí** | Usuarios protegidos → ADMIN |
| `audit_logs_list` | `audit.view` | No | |
| `reports_list_types` | `reports.view` | No | Según tipos permitidos |
| `reports_generate` | *(vía tipo de reporte)* | No* | Requiere `reports.export` **o** el `*.view` del tipo |

\*No exige confirmación de mutación de BD, pero genera un artifact descargable acotado a permisos y filtros del usuario.

### Reportes desde el agente

| Tipo | Permite si tiene |
| --- | --- |
| `grades` | `reports.export` **o** `grades.view` |
| `attendance` | `reports.export` **o** `attendance.view` |
| `enrollments` | `reports.export` **o** `enrollments.view` |
| `students` | `reports.export` **o** `students.view` |

ADMIN puede todos. La URL de descarga es firmada (caduca) o con JWT del dueño.

---

## 8. Ejemplos prácticos

| Usuario | Puede pedir al chat… | No debe poder… |
| --- | --- | --- |
| **ADMIN** | Cualquier consulta, reporte, mutación (con confirmación) | — |
| **SECRETARY** | Listar estudiantes, crear matrícula (confirma), exportar estudiantes | Asignar roles de sistema sin `users.edit` / política |
| **TEACHER** | Notas/asistencia de **sus** cursos; reportes si tiene permiso | Ver / editar cursos ajenos; dashboard institucional |
| **STUDENT** | Sus notas/asistencia/horarios; chat con `ai.use` | Listar todos los usuarios, mutar notas, kárdex/dashboard |
| **AUDITOR** | Logs (si usa APIs con `ai.view_logs` / `audit.view`) | Usar el chat si el seed no le dio `ai.use` |
| **IT_SUPPORT** | Configurar IA | Operar matrículas/notas sin permisos académicos |

---

## 9. Controles de mínimo privilegio del agente (SPEC-029 / SPEC-030)

| Control | Comportamiento |
| --- | --- |
| `tools_for_user` | El LLM solo recibe tools permitidas al usuario |
| Escalada NL | «hazme admin», «cambia mi rol», etc. → bloqueo pre-LLM |
| Intent NL | «reporte de todos los usuarios…» sin permiso → `privilege_block` |
| `system_stats` | Requiere `dashboard.view` **o** `reports.view` **o** `users.view` |
| Reportes `students` | Docente: solo alumnos de cursos propios |
| LogIA `user_question` | Pregunta original del turno en UI/exports |

Consultas legítimas («¿cuál es mi rol?», «¿qué permisos tengo?») **no** se bloquean.

## 10. Limitaciones / puntos a tener en cuenta

1. **`privileges_request_elevation`**: existe esquema/handler parcial; la elevación completa y su resolución no están totalmente cableadas al executor.
2. El markup interno tipo DSML/`invoke name=` **no es un error de permisos**: se parsea, se ejecuta la tool y se responde en lenguaje natural (SPEC-023); nunca debe mostrarse al usuario.
3. Mutaciones siempre deberían pasar por **confirmación** explícita; no se “ejecutan en silencio”.
4. Impersonación (`users.login-as`) es un permiso aparte y deja rastro en claims (`impersonator_id`); no debe usarse desde el agente sin controles de ADMIN.
5. El escáner de injection/intent es heurístico (regex); parafraseos elaborados pueden no coincidir.

---

## 11. Archivos de código relacionados

| Tema | Ruta |
| --- | --- |
| Seed roles/permisos | `App/database/seeds/seed_data.py` |
| Modelo User/Role/Permission | `App/backend/app/models/iam.py` |
| Decoradores JWT | `App/backend/app/permissions/decorators.py` |
| Login / claims | `App/backend/app/auth/routes.py` |
| Visibilidad | `App/backend/app/services/visibility.py` |
| Schemas tools LLM + `tools_for_user` | `App/backend/app/ai/gateway/registry.py` |
| Handlers + permisos | `App/backend/app/ai/gateway/handlers.py` |
| Executor + confirmación | `App/backend/app/ai/gateway/executor.py` |
| Orquestador chat | `App/backend/app/ai/gateway/orchestrator.py` |
| Anti-injection / intent / LogIA | `App/backend/app/services/ai_agent_log.py` |
| Reportes IA | `App/backend/app/services/ai_reports.py` |
| Specs | `Spec/SPEC-003`, `SPEC-009`, `SPEC-016`, `SPEC-023`, `SPEC-028`, `SPEC-029`, `SPEC-030` |

---

*Documento generado para el proyecto laboratorioIA. Si se añaden roles o tools, actualizar este archivo junto con el seed y el registry del gateway.*
