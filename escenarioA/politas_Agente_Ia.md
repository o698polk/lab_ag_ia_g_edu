# Políticas y controles de seguridad del Agente IA

Documento de análisis del estado **actual** del Sistema de Gestión Académica respecto a la seguridad del asistente de inteligencia artificial: reglas, permisos, controles ante *prompt injection* / *jailbreak*, principios de **Zero Trust** y **mínimo privilegio**, y limitaciones conocidas.

| Campo | Valor |
| --- | --- |
| Versión del documento | 1.2 |
| Fecha | 2026-10-11 |
| Verificado contra código | 2026-10-11 |
| Metodología | Spec as Skill (SPEC-002 … SPEC-030; en particular SPEC-026/028/029/030) |
| Complementa | `permisos_role.md`, `PROMPTSMASTER — Sistema de Gestión Académica.md` |

---

## 1. Resumen ejecutivo

El agente IA **no ejecuta acciones solo porque el modelo lo pida**. Toda operación sensible pasa por capas de control en el servidor:

1. Autenticación JWT y permiso de entrada (`ai.use`).
2. Escaneo anti *prompt injection* / *jailbreak* / escalada de rol **antes** de llamar al LLM.
3. Escaneo de intención NL no autorizada (`scan_unauthorized_intent`) pre-LLM.
4. Catálogo cerrado de tools; el LLM solo recibe `tools_for_user` (filtrado por permiso).
5. Permiso IAM por tool + re-chequeo en handlers.
6. Alcance de datos (visibilidad) por rol; reportes de estudiantes acotados a cursos propios.
7. Confirmación humana obligatoria en mutaciones.
8. Registro en LogIA (con `user_question`) y auditoría de dominio (doble canal en bloqueos).
9. Controles adicionales: rate limit, anti-SSRF, artifacts firmados, sanitización de salida.

**Zero Trust:** el modelo no es fuente de autoridad. **Mínimo privilegio:** el agente hereda la identidad y permisos del usuario; no amplía poderes.

---

## 2. Modelo de amenazas que el sistema intenta cubrir

| Amenaza | Descripción | Controles actuales |
| --- | --- | --- |
| **Prompt injection** | Mensaje que intenta anular el system prompt o forzar conducta | Escáner regex pre-LLM + bloqueo + LogIA/Auditoría |
| **Jailbreak** | “Actúa como DAN / admin / sin reglas” | Mismos patrones + tono institucional en system prompt |
| **Escalada NL / spoofing de rol** | «hazme admin», «cambia mi rol» | Patrones `privilege_escalation` (SPEC-029) |
| **Abuso de tools** | El LLM inventa acciones o el usuario pide lo que no puede | `tools_for_user` + catálogo cerrado + IAM + scope |
| **Intención fuera de permiso** | Pedir en NL lo que el rol no puede | `scan_unauthorized_intent` (SPEC-030) |
| **Exfiltración de secretos** | API keys, system prompt, dumps técnicos | Clave cifrada/enmascarada; sanitización DSML/JSON; APA7 |
| **SSRF** | Forzar llamadas HTTP a hosts internos vía proveedor | Allowlist de URL del LLM |
| **Descarga indebida de reportes** | Acceso a artifacts ajenos | HMAC firmado + JWT dueño/ADMIN + caducidad |
| **Flood / abuso de API** | Spam de chat | Rate limit 20/min en `/ai/chat` |

---

## 3. Arquitectura de defensa en profundidad

```
Usuario (JWT)
    │
    ▼
[API] permission_required("ai.use") + rate limit
    │
    ▼
[Orquestador] scan_prompt_injection ──bloquea──► LogIA + Auditoría
    │ OK
    ▼
[Orquestador] scan_unauthorized_intent ──bloquea──► privilege_block
    │ OK
    ▼
[LLM] system prompt endurecido + tools_for_user(user)
    │
    ▼
[Executor] tool existe? → permiso IAM? → ¿mutante? → confirmación
    │
    ▼
[Handlers] has_permission + visibility/scope + auditoría
    │
    ▼
[Respuesta] strip DSML / compose / format APA7 → UI
```

**Fuentes de código principales**

| Capa | Ruta |
| --- | --- |
| Orquestador | `App/backend/app/ai/gateway/orchestrator.py` |
| Executor | `App/backend/app/ai/gateway/executor.py` |
| Registro + `tools_for_user` | `App/backend/app/ai/gateway/registry.py` |
| Handlers | `App/backend/app/ai/gateway/handlers.py` |
| Proveedor LLM / SSRF / DSML | `App/backend/app/ai/provider.py` |
| Anti-injection + intent + LogIA | `App/backend/app/services/ai_agent_log.py` |
| Visibilidad | `App/backend/app/services/visibility.py` |
| Artifacts firmados | `App/backend/app/services/artifact_links.py` |
| Decoradores IAM | `App/backend/app/permissions/decorators.py` |
| Seed de roles | `App/database/seeds/seed_data.py` |

---

## 4. Permisos IAM del módulo IA

Formato de permiso: `{módulo}.{acción}`.

| Permiso | Quién lo tiene (seed típico) | Qué habilita |
| --- | --- | --- |
| `ai.use` | ADMIN, RECTOR, COORDINATOR, TEACHER, STUDENT, SECRETARY | Chat, conversaciones, tools del gateway, artifacts propios |
| `ai.configure` | ADMIN, IT_SUPPORT | Configurar proveedor, API key, modelo, system prompt |
| `ai.view_logs` | ADMIN, AUDITOR, IT_SUPPORT | Módulo **LogIA** (listar / exportar xlsx, pdf, json) |

### 4.1 Separación de privilegios (mínimo privilegio)

- Un **AUDITOR** puede ver LogIA (`ai.view_logs`) **sin** poder chatear (`ai.use` no está en su seed).
- Un **STUDENT** puede usar el chat; no recibe tools de escritura ni `system_stats` / `users_list` en el schema.
- **IT_SUPPORT** configura IA y ve logs, pero no opera el dominio académico completo.
- El frontend oculta menús con `hasPerm()`; la **autoridad real** está en el backend.

### 4.2 Doble verificación de permisos

| Momento | Mecanismo |
| --- | --- |
| Entrada HTTP | Claims JWT + `@permission_required` |
| Schema LLM | `tools_for_user` (solo tools permitidas) |
| Ejecución de tool | `User.has_permission(perm)` contra BD (en vivo) |
| Handler | Muchas funciones vuelven a comprobar el permiso del dominio |

**Nota operativa:** si se cambian roles en BD, el JWT del API puede quedar desactualizado hasta re-login; el gateway del agente lee permisos desde BD.

---

## 5. Catálogo de tools y política de mutación

Solo existen las tools registradas en `HANDLERS` / `TOOL_SCHEMAS`. Una tool desconocida se rechaza (`Tool desconocida`).

El proveedor recibe **`tools_for_user(user)`**, no el catálogo completo (SPEC-030). El executor sigue revalidando IAM.

### 5.1 Tools de lectura (sin confirmación; con permiso y scope)

Ejemplos: `careers_list`, `subjects_list`, `terms_list`, `courses_list`, `students_list`, `teachers_list`, `enrollments_list`, `grades_list`, `attendance_list`, `users_list`, `roles_list`, `audit_logs_list`, `reports_list_types`, `system_stats` (solo visión institucional).

### 5.2 Tools mutantes (confirmación obligatoria)

| Tool | Permiso típico | Efecto |
| --- | --- | --- |
| `careers_create` | `careers.create` | Alta de carrera |
| `careers_update` | `careers.edit` | Edición de carrera |
| `enrollments_create` | `enrollments.create` | Matrícula |
| `grades_upsert` | `grades.manage` | Notas |
| `attendance_upsert` | `attendance.manage` | Asistencia |
| `users_assign_roles` | `users.edit` | Asignación de roles |

**Política:** si `mutating=True` y no hay `confirm`, el executor responde `needs_confirm` y la conversación guarda `pending_action`.

### 5.3 Reportes

`reports_generate` exige `user_can_report` y aplica filtros de visibilidad. Reportes de estudiantes para docentes: solo alumnos de `owned_course_ids`.

### 5.4 Límites operativos

- Máximo **8** tool-calls por turno.
- Listados paginados con tope (p. ej. `per_page` ≤ 100).
- Rate limit chat: **20 solicitudes por minuto**.

---

## 6. Controles anti prompt injection y jailbreak

### 6.1 Escáner de entrada (`scan_prompt_injection`) — SPEC-026 / SPEC-029

Ubicación: `App/backend/app/services/ai_agent_log.py`.

Si hay coincidencia (y no es confirmación con `pending_action`):

1. No se llama al proveedor ni se ejecutan tools.
2. Respuesta de política de seguridad.
3. LogIA + Auditoría: `prompt_injection` y `policy_block` (`severity=block`), con `user_question`.

**Patrones base (EN/ES):** ignore previous instructions, revelar system prompt, DAN/jailbreak, bypass security, actúa como admin, override safety, `<system>`, developer mode, do anything now.

**Escalada / spoofing de rol (`kind=privilege_escalation`):** cambia mi rol, hazme admin, soy un usuario administrador, dame todos los permisos, grant me all permissions, bypass mínimo privilegio / Zero Trust, etc.

**No se bloquean** consultas legítimas: «¿cuál es mi rol?» / «¿qué permisos tengo?».

### 6.2 Intent guard (`scan_unauthorized_intent`) — SPEC-030

Tras el escáner de injection, bloquea NL con intención clara fuera de permiso (p. ej. reporte/lista de todos los usuarios sin `users.view`/`reports.export`; auditoría sin `audit.view`; estadísticas globales sin visión institucional). Evento: `privilege_block` + `AI_PRIVILEGE_BLOCK`.

### 6.3 Endurecimiento del system prompt

En `provider.py` (y contexto base en `deepseek.py`): solo `tool_calls` de API, sin DSML al usuario, confirmación en mutaciones, presentación APA 7 (SPEC-027).

### 6.4 Sanitización de salida

| Control | Función |
| --- | --- |
| Parseo DSML como tools (SPEC-023) | Pasa por el executor (misma IAM) |
| `strip_tool_markup` / `_is_raw_tool_dump` | Evita dumps técnicos al usuario |
| `format_apa_plain` | Elimina markdown ornamental |
| Frontend `ai-chat.js` | Red de seguridad UX |

---

## 7. Visibilidad y aislamiento de datos (scope)

| Rol / perfil | Alcance típico vía agente |
| --- | --- |
| ADMIN / staff amplio | Lectura amplia según permisos IAM |
| TEACHER | Cursos asignados; reportes de estudiantes solo de esos cursos |
| STUDENT | Solo sus matrículas, notas y asistencia |
| GUARDIAN | En seed habitualmente **sin** `ai.use` |

---

## 8. Controles de infraestructura y secretos

### 8.1 Anti-SSRF del proveedor LLM

Allowlist en `provider.py`; ruta legada `deepseek.py` más estricta. URL desde configuración, no del chat.

### 8.2 API keys

Cifradas en `AIConfig`; respuestas enmascaradas; no se exponen al modelo ni al frontend.

### 8.3 Artifacts / reportes (SPEC-021)

Caducidad ~72 h; descarga HMAC-SHA256 o JWT dueño/ADMIN; vencido → 410.

### 8.4 Cabeceras y límites HTTP

X-Frame-Options, nosniff, CSP, HSTS (no-debug), CORS, rate limiters.

---

## 9. Registro, monitoreo y trazabilidad (LogIA + Auditoría)

| Tipo de evento | Uso |
| --- | --- |
| `chat` / `tool_call` / `tool_error` / `report` / `confirm` | Operación normal |
| `prompt_injection` / `policy_block` | Injection / jailbreak / escalada NL (**rojo**) |
| `privilege_block` | IAM, scope, intent NL, tool desconocida (**rojo**) |

**SPEC-028:** doble canal LogIA + Auditoría (`ai_security`).

**SPEC-029:** cada evento del turno guarda `user_question` (UI columna Pregunta, búsqueda y exports).

---

## 10. Principios Zero Trust y mínimo privilegio

| Principio | Materialización |
| --- | --- |
| Nunca confiar, siempre verificar | LLM no autoriza; servidor revalida |
| Verificar explícitamente | JWT + endpoint + schema tools + tool + scope |
| Mínimo privilegio | Matriz rol→permiso; `tools_for_user`; intent guard; scope |
| Asumir incumplimiento | Logs de bloqueo, artifacts con caducidad |
| Segmentación | Catálogo cerrado; UI ≠ backend |
| Identidad como perímetro | Agente = usuario del token |

---

## 11. Matriz de controles vs ataque (estado actual)

| Control | Prompt injection | Jailbreak | Abuso de tools | Exfiltracion | SSRF | Descarga indebida |
| --- | --- | --- | --- | --- | --- | --- |
| Escaner pre-LLM | fuerte | fuerte | parcial | nulo | nulo | nulo |
| Intent guard NL | nulo | nulo | fuerte | parcial | nulo | nulo |
| tools_for_user | nulo | parcial | fuerte | parcial | nulo | nulo |
| System prompt endurecido | parcial | fuerte | parcial | parcial | nulo | nulo |
| Catalogo + executor IAM | nulo | parcial | fuerte | fuerte | nulo | nulo |
| Confirmacion mutaciones | nulo | nulo | fuerte | nulo | nulo | nulo |
| Sanitizacion salida | parcial | parcial | nulo | fuerte | nulo | nulo |
| Allowlist URL LLM | nulo | nulo | nulo | nulo | fuerte | nulo |
| Artifact HMAC/JWT | nulo | nulo | nulo | parcial | nulo | fuerte |
| LogIA / audit | fuerte | fuerte | fuerte | fuerte | nulo | fuerte |
| Rate limit | nulo | nulo | parcial | nulo | nulo | nulo |

---

## 12. Flujos de política

- **P-01** Entrada: `ai.use` + JWT.
- **P-02** Injection/escalada: bloqueo sin LLM + LogIA/Auditoría.
- **P-03** Intent NL: bloqueo `privilege_block` si falta permiso.
- **P-04** Tools: schema filtrado + IAM + confirmación + scope.
- **P-05** Secretos: no exponer keys ni dumps técnicos.
- **P-06** Evidencia: LogIA con `user_question` + auditoría.
- **P-07** Presentación: SPEC-027 / APA 7 adaptada.

---

## 13. Limitaciones y riesgos residuales

1. Escáner e intent guard son heurísticos (regex); parafraseos pueden evadir.
2. Elevación de privilegios (SPEC-016) incompleta en `HANDLERS`.
3. Impersonación: el agente opera como identidad impersonada; aún sin marca dedicada en LogIA.
4. Artifacts: enlace firmado válido hasta expiración (sin one-time / IP binding).
5. Diferencias de rigor SSRF entre `provider.py` y `deepseek.py`.
6. CORS amplio (`*`) en API.

---

## 14. Backlog restante

1. Lista anti-injection/intent versionada y administrable + pruebas adversariales.
2. Completar elevación de privilegios con flujo ADMIN + LogIA.
3. Marcar `impersonator_id` en LogIA.
4. Unificar política SSRF.
5. Tokens de descarga de un solo uso / TTL corto.
6. Detección semántica / segundo modelo para jailbreaks sofisticados.

### Modo laboratorio inseguro (SPEC-031 / SKILL-030)

Flag `AI_INSECURE_MODE=1` (default apagado). Cuando está ON: sin scanners, sin `tools_for_user`, sin IAM/scope/confirmación en el gateway, system prompt débil, banner en el chat. JWT de login **no** se desactiva. Ver `guia_ejecute.md` y `promantiseguridadia.md`.

---

## 15. Referencias cruzadas

| Documento / spec | Tema |
| --- | --- |
| `permisos_role.md` | Matriz de roles y permisos |
| SPEC-026 / SKILL-025 | LogIA + anti prompt-injection |
| SPEC-028 / SKILL-027 | Dual-log bloqueos + UI roja |
| SPEC-029 / SKILL-028 | `user_question` + escalada/spoofing de rol |
| SPEC-030 / SKILL-029 | `tools_for_user` + intent NL + `system_stats` / reportes |
| SPEC-031 / SKILL-030 | Modo laboratorio inseguro (`AI_INSECURE_MODE`) |
| SPEC-016 / SPEC-021 / SPEC-023 / SPEC-027 | Gateway, artifacts, DSML, APA7 |

---

## 16. Conclusión

El sistema aplica seguridad en capas: identidad JWT, mínimo privilegio (schema filtrado + intent guard + IAM + scope), confirmación en mutaciones, bloqueos heurísticos pre-LLM, SSRF del proveedor, artifacts firmados y trazabilidad LogIA con pregunta del usuario.

**El modelo es no confiable; el servidor decide.** El agente no amplía poderes del usuario.

Cualquier cambio de política debe ir con nueva SPEC/SKILL y actualización de este documento y de `permisos_role.md`.
