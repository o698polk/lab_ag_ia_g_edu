
## 4.10 API REST `/api/v1`

### 4.10.1 Autenticación (`auth_bp`, prefijo `/api/v1/auth`)

Incluye login, refresh, me/perfil, cambio de contraseña y flujos asociados a JWT y bloqueo por intentos. Los tokens incorporan claims de roles y permisos.

### 4.10.2 Usuarios (`users_bp`, `/api/v1/users`)

Listado/creación/edición/borrado de usuarios y `POST /<user_id>/login-as` para impersonación.

### 4.10.3 Académico (`academic_bp`)

Endpoints para careers, subjects, terms, curriculum, courses, assignments, enrollments, schedules, grades, attendance, students, teachers (CRUD según permisos y reglas). La listados aplican scoping de visibilidad.

### 4.10.4 Sistema (`system_bp`)

Dashboard, roles/permissions, notificaciones, auditoría, configuración de marca/sistema, configuración IA, chat IA y conversaciones, artifacts, LogIA (`/ai/agent-logs`), kárdex y reportes genéricos ` /reports/<tipo>.xlsx|.pdf`, catálogo y summary.

El endpoint de chat invoca `run_agent_chat`. En laboratorioIA existe `ai_security_mode` para exponer el estado del modo inseguro a la UI.

## 4.11 Tool Gateway en detalle

### 4.11.1 Registry (`registry.py`)

`TOOL_SCHEMAS` define schemas estilo OpenAI function calling. `tools_for_user(user)` filtra el catálogo:

- En modo inseguro (IA): devuelve el catálogo completo.
- En modo seguro: incluye tools solo si el usuario tiene el permiso asociado en `HANDLERS`, con lógica especial para `system_stats` y `reports_generate`.

### 4.11.2 Executor (`executor.py`)

`execute_tool(user, tool_name, args, confirm=False, conversation_id=None)`:

1. Si tool no está en `HANDLERS` → error `unknown_tool` y log de privilegio (salvo inseguro).
2. Si hay permiso requerido y el usuario no lo tiene → deny con `needs_elevation=True` y log Zero Trust.
3. Si es mutación y no hay confirmación → `needs_confirm` (salvo inseguro).
4. Ejecuta handler; en error registra `AI_TOOL_ERROR`; siempre puede registrar `AI_TOOL_CALL`.

`_log_privilege_block` escribe detalle con `zero_trust: True` y `least_privilege: True`.

### 4.11.3 Handlers registrados (`HANDLERS`)

Tools de lectura: `system_stats`, `careers_list`, `careers_get`, `subjects_list`, `terms_list`, `courses_list`, `students_list`, `teachers_list`, `enrollments_list`, `grades_list`, `attendance_list`, `users_list`, `roles_list`, `audit_logs_list`, `reports_list_types`.

Tools de mutación: `careers_create`, `careers_update`, `enrollments_create`, `grades_upsert`, `attendance_upsert`, `users_assign_roles`.

Reportes: `reports_generate` (chequeo propio vía `user_can_report`).

### 4.11.4 Parcial: `privileges_request_elevation`

La función crea `ElevationRequest` y una `Notification` a rol `ADMIN`, y audita `ELEVATION_REQUEST`. **No** está incluida en el diccionario `HANDLERS`; por tanto, no es tool invocable por el flujo estándar del registry/executor. Estado: **parcial**.

### 4.11.5 Orchestrator (`orchestrator.py`)

`run_agent_chat` persiste el mensaje de usuario, aplica guards, resuelve confirmaciones pendientes, llama al LLM con tools, ejecuta tool calls en bucle, compone respuesta humana (SPEC-022/027), evita dumps crudos de tools (SPEC-023) y registra eventos. Ambos laboratorios comparten esta estructura general; difieren en la ubicación/modularización del intent guard y en la presencia del modo inseguro.

## 4.12 LogIA y heurísticas

`AIAgentLog` almacena `event_type`, `severity`, `summary`, `detail` JSON, `keywords`, `user_question`, roles y conversación. `scan_prompt_injection` usa patrones; `log_security_block` dual-escribe LogIA + `AuditLog` (módulo de seguridad AI). Listado y exportación están en `system_api` (`agent_logs_list`, `agent_logs_export`).

## 4.13 Diferencias de implementación IA vs IB (núcleo de seguridad del agente)

### laboratorioIA

- Archivo `app/ai/insecure_mode.py` con `is_insecure_mode()` leyendo `AI_INSECURE_MODE`.
- `.env.example` documenta el flag y advierte no usarlo en producción.
- `scan_unauthorized_intent` vive en `ai_agent_log.py` y se desactiva en modo inseguro.
- Handlers/executor/registry/provider consultan `is_insecure_mode()` para relajar IAM del agente, confirmaciones y catálogo de tools.
- Endpoint/UI de modo de seguridad del agente.

### laboratorioIB

- Archivo dedicado `app/services/ai_intent_guard.py` con reglas `_INTENT_RULES` y excepciones de ámbito docente.
- No existe `insecure_mode.py` en el árbol IB inspeccionado.
- El orquestador importa `scan_unauthorized_intent` desde `ai_intent_guard`.
- El escenario IB se interpreta como laboratorio de denegación NL endurecida/modularizada, frente al escenario IA que añade un interruptor experimental de inseguridad.

Ambos mantienen injection heuristics y LogIA. Ninguno implementa PDP/PAP formales.

## 4.14 Seeds, esquema y persistencia

- `db.create_all()` + `seed_all` / `seed_coherent` / `seed_massive`.
- `Flask-Migrate` está en requirements, pero `database/migrations` no contiene revisiones útiles en la inspección realizada.
- Dumps SQL permiten recrear esquemas/datos fuera de Alembic.
- Esto implica que la evolución de esquema es pragmática de laboratorio, no un pipeline de migraciones maduro.

## 4.15 Frontend

Templates (`login.html`, `app.html`) y estáticos (`app.js`, `ai-chat.js`, `api.js`) consumen la API JWT. El chatbot flotante y el panel de conversaciones dependen de endpoints `/api/v1/ai/*`. La presentación del asistente se formatea hacia texto formal (SPEC-027, `ai_text_format.py`).

## 4.16 Mapeo CHANGELOG / comentarios SPEC (trazabilidad parcial)

CHANGELOG 1.0.0–1.1.0 referencia SPEC-001 a SPEC-008 (estructura Flask, OWASP headers/rate limit, modelos/seeds, roles, módulos académicos, impersonación, DeepSeek AES, UI, kárdex/reportes) y seeder/chatbot. El código añade referencias SPEC-009 (visibilidad), SPEC-012, SPEC-014, SPEC-016 (gateway), SPEC-017/018/020/024 (conversaciones), SPEC-019 (reportes), SPEC-021 (artifacts firmados), SPEC-022/023/025/027 (respuesta/parseo/PDF/APA), SPEC-026/028/029 (LogIA/bloques), SPEC-030 (intent), SPEC-031 (inseguro). Dado que `/Spec` no existe, este mapeo es **trazabilidad por etiquetas**, no verificación contra documentos Spec externos.

## 4.17 Decisiones de diseño relevantes

1. **Un solo usuario JWT como subject del agente:** evita service account omnisciente (Shostack, 2014; Rose et al., 2020).
2. **Allowlist de tools:** denegación por defecto de nombres desconocidos.
3. **Confirmación de mutaciones:** reduce cambios accidentales por NL ambiguo.
4. **Doble logging:** facilita análisis forense de laboratorio.
5. **Scoping además de RBAC:** mínimo privilegio sobre filas, no solo sobre endpoints.
6. **Modo inseguro explícito (IA):** habilita contraste experimental consciente, no un bypass silencioso.
7. **Intent guard (IB/IA seguro):** defensa antes del LLM para pedidos claramente fuera de permiso.

## 4.18 Limitaciones de implementación reconocidas en este capítulo

No hay PDP/PAP. No hay Spec folders. Elevación parcial. Migrations vacías. Dependencia de proveedor externo DeepSeek. Heurísticas regex de injection/intent son by-design incompletas frente a adversarios sofisticados (Kang et al., 2023; Azad et al., 2024; Deng et al., 2025). El laboratorio es el lugar correcto para exponer esas limitaciones con honestidad.

## 4.19 Descripción modular por rutas de archivo (núcleo backend)

El paquete `app/auth` concentra la emisión y renovación de tokens JWT, el registro de refresh tokens y el control de bloqueo por intentos fallidos, de modo que el resto de la API asume un sujeto autenticado. El paquete `app/permissions` aporta decoradores que leen roles/permisos del JWT o de la base y cortocircuitan con 403 cuando falta autorización, incluyendo el bypass explícito de `ADMIN`. El paquete `app/api` divide responsabilidades: `academic.py` expresa el dominio educativo, `users.py` la administración de identidades e impersonación, y `system_api.py` el tablero, la auditoría, los reportes, el kárdex y todo el plano conversacional de IA. El paquete `app/services` agrupa reglas reutilizables (`grades`, `attendance`, `visibility`, `reports`, `ai_reports`, `ai_agent_log`, `artifact_links`, `audit`), evitando que los handlers del gateway dupliquen lógica divergente respecto de la API REST. El paquete `app/ai` encapsula proveedor DeepSeek, conversaciones, modo inseguro (IA) y el gateway. Esta modularización facilita la comparación A/B: la mayoría de archivos son análogos entre laboratorios, y las divergencias de seguridad del agente quedan localizadas en pocos módulos, lo que fortalece la validez interna del diseño experimental descrito en el Capítulo III.

## 4.20 Flujo de una mutación mediada por el agente

Cuando un docente autenticado solicita en lenguaje natural actualizar una nota, el orquestador, en modo seguro, primero descarta inyecciones e intenciones no autorizadas. Luego el LLM, si propone `grades_upsert`, solo puede hacerlo si esa tool está en `tools_for_user` (requiere `grades.manage`). El executor exige confirmación textual (`si`, `confirma`, etc.) antes de escribir. El handler valida periodo abierto, pertenencia del curso (`owned_course_ids`) y reglas de `apply_grade_rules`. El resultado se audita como `AI_TOOL_UPSERT` / `AI_TOOL_CALL` y la respuesta al usuario se reformula sin volcar JSON crudo. Este flujo operacionaliza mínimo privilegio y verificación por acción, en la línea interpretativa de Rose et al. (2020) y Deng et al. (2025), sin pretender exhaustividad adversaria.

## 4.21 Flujo de un reporte y artifact

`reports_generate` construye un artefacto persistido (`AIArtifact`) con filtros, formato (`pdf`, `xlsx`, `json`, `md` según catálogo AI) y ruta de almacenamiento. La descarga usa URL firmada con `sig` y `expires` (SPEC-021), permitiendo al navegador obtener el archivo sin reenviar el JWT en ciertos flujos. `validate_ai_chat.py` y `validate_filters_export.py` ejercitan partes de esta cadena. La autorización de reportes combina permisos `reports.*` y funciones `user_can_report`, y en modo inseguro IA se relaja el catálogo expuesto al modelo.

## 4.22 Configuración y secretos

`.env.example` declara, entre otras: `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `LOGIN_MAX_ATTEMPTS`, `LOGIN_LOCK_MINUTES`, `AES_SECRET_KEY`, `DEEPSEEK_API_URL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `AI_INSECURE_MODE` (IA), `SYSTEM_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_USERNAME`. El informe solo enumera nombres, no valores secretos reales de `.env` locales.
