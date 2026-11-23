# SPEC-016 — Gateway del agente IA (CRUD + privilegios/roles)

**Objetivo:** Dotar al agente de IA de un **gateway de herramientas (tools)** que le permita consultar y ejecutar operaciones **CRUD** sobre los recursos del sistema (todas las tablas de dominio expuestas vía API), responder cualquier consulta operativa dentro del alcance del usuario, y **gestionar o solicitar elevación de roles/privilegios** de forma controlada, auditada y alineada a IAM existente.

**Skills relacionadas:** SKILL-015  
**Specs relacionadas:** SPEC-002 (seguridad), SPEC-003 (roles), SPEC-005 (agente), SPEC-008 (impersonación), SPEC-013 (proveedores)

---

## 1. Problema actual

Hoy `POST /ai/chat` solo envía texto + un resumen estático de conteos (`build_system_context`). El modelo **no puede** invocar APIs reales: no crea/edita registros, no asigna roles y no genera acciones verificables. Las respuestas se inventan o se limitan a conteos.

---

## 2. Principios de seguridad (obligatorios)

1. **Sin bypass silencioso:** el gateway **nunca** omite `permission_required` / scope de curso / periodos.
2. **Identidad del invocador:** toda tool se ejecuta con el JWT del usuario que chatea (mismo `User` que `get_current_user()`).
3. **Catálogo cerrado:** solo tools registradas; no SQL arbitrario ni ORM “raw” sobre tablas no listadas.
4. **Confirmación:** creates/updates/deletes y cambios de roles requieren `confirm=true` en un segundo turno (o flag explícito del usuario: “confirma”, “sí, ejecuta”).
5. **Auditoría:** cada tool call → `AuditLog` + `AILog` (tool name, args sanitizados, resultado OK/error).
6. **Secretos:** nunca devolver API keys, hashes de password, refresh tokens ni `api_key_encrypted`.
7. **Tablas internas sensibles:** `refresh_tokens` y campos de cifrado **no** tienen tool de lectura de secretos; como máximo `list` metadatos (id, user_id, expires) si hay `users.view` + ADMIN.

---

## 3. Recursos (tablas / entidades) cubiertos

| Recurso | Tabla | Tools típicas | Permisos base |
| --- | --- | --- | --- |
| users | users | list, get, create, update, deactivate | users.* |
| roles | roles | list, get, assign_user_roles | roles.view / users.edit |
| permissions | permissions | list, get, set_role_permissions | permissions.view / roles.* |
| students | students | CRUD | students.* |
| teachers | teachers | CRUD | teachers.* |
| careers | careers | CRUD | careers.* |
| subjects | subjects | CRUD | subjects.* |
| curriculum | curriculum | list, create, update, delete | curriculum.* |
| terms | terms | CRUD | terms.* |
| courses | courses | CRUD | courses.* |
| assignments | assignments | list, create, delete | assignments.* |
| enrollments | enrollments | CRUD | enrollments.* |
| schedules | schedules | CRUD | schedules.* |
| grades | grades | list, upsert | grades.* |
| attendance | attendance | list, upsert, bulk | attendance.* |
| notifications | notifications | list, send | notifications.* |
| audit_logs | audit_logs | list (solo lectura) | audit.view |
| system_config | system_config | get, update | ai.configure / admin config |
| ai_config / ai_providers | ai_* | get, update (sin exponer key) | ai.configure |
| ai_logs | ai_logs | list | ai.view_logs |
| conversations | ai_conversations* | list, get (SPEC-017) | ai.use (propias) |

\* Tablas nuevas de conversación se definen en SPEC-017; el gateway las incluye como recurso `conversations`.

El gateway **reutiliza** la lógica de `app/api/*` (servicios/handlers), no duplica reglas de negocio.

---

## 4. Arquitectura del gateway

```text
Usuario (chat fijo | flotante)
    → POST /api/v1/ai/chat  { conversation_id?, message, confirm? }
    → AgentOrchestrator
         → LLM (proveedor activo SPEC-013) con tool schemas
         → ToolGateway.execute(tool, args, user)
              → valida permiso + confirma si mutate
              → llama servicio/API interna
              → audit + resultado
         → LLM formula respuesta final
    → { reply, conversation_id, tool_calls[], artifacts[] }
```

### 4.1 Formato de tools (contrato interno)

Cada tool:

```json
{
  "name": "grades.upsert",
  "description": "Crea o actualiza nota de un estudiante en un curso",
  "parameters": { "type": "object", "properties": { "...": {} }, "required": [] },
  "permission": "grades.manage",
  "mutating": true
}
```

Convención de nombres: `{resource}.{action}`  
Acciones: `list` | `get` | `create` | `update` | `delete` | `upsert` | `assign_roles` | `set_permissions` | `export` (ver SPEC-017 reportes).

### 4.2 Endpoint de chat ampliado

`POST /api/v1/ai/chat`

```json
{
  "message": "Matricula al estudiante EST0005 en el curso 12",
  "conversation_id": "uuid-opcional",
  "channel": "panel" | "float",
  "confirm": false,
  "context": ""
}
```

Respuesta:

```json
{
  "reply": "Para matricular necesito confirmación…",
  "conversation_id": "…",
  "pending_action": {
    "tool": "enrollments.create",
    "args": { "student_id": 5, "course_id": 12 },
    "summary": "Crear matrícula activa EST0005 → curso 12"
  },
  "tool_calls": [],
  "artifacts": []
}
```

Si el usuario confirma (`confirm: true` o mensaje afirmativo y hay `pending_action` en la conversación), el gateway ejecuta y limpia el pendiente.

---

## 5. Elevación de privilegios / roles

Interpretación de producto (**no** es vulneración de IAM):

### 5.1 Gestión directa (si el invocador ya puede)

Si el usuario tiene `users.edit` / permisos de roles:

| Tool | Efecto |
| --- | --- |
| `users.assign_roles` | Asigna/reemplaza roles de un usuario |
| `roles.set_permissions` | Actualiza permisos de un rol |
| `users.escalate_temp` | (Opcional fase 2) marca rol temporal con TTL |

Siempre `mutating=true` + confirmación + auditoría `ROLE_CHANGE` / `PERMISSION_CHANGE`.

### 5.2 Solicitud de elevación (si el invocador no puede)

Cuando la consulta o acción requiere un permiso que el usuario **no** tiene:

1. El agente **explica** qué permiso falta.
2. Tool `privileges.request_elevation`:
   - Crea registro `elevation_requests` (user_id, requested_permissions[], reason, status=`pending`).
   - Notifica a usuarios con rol ADMIN (vía `notifications`).
3. Un ADMIN aprueba/rechaza (`privileges.resolve_elevation`) → si aprueba, opción A: asignar rol/permiso permanente; opción B: **token de elevación** TTL corto (similar espíritu SPEC-008) con claims extra, auditado.
4. El agente **nunca** se auto-asigna ADMIN sin aprobación humana.

### 5.3 Consultas “cualquier pregunta”

El agente debe:

1. Intentar resolver con tools de lectura permitidas + contexto de conversación.
2. Si faltan datos por permiso → ofrecer solicitud de elevación o indicar rol necesario.
3. No inventar filas de BD; si la tool falla, decir el error real.

---

## 6. Límites operativos

| Límite | Valor sugerido |
| --- | --- |
| Tool calls por mensaje | ≤ 8 |
| Filas en `list` | ≤ 100 (paginar con `page`/`per_page`) |
| Timeout LLM + tools | ≤ 60 s |
| Rate limit chat | existente / reforzar (ej. 20/min) |
| Deletes masivos | prohibidos; solo por id |

---

## 7. Criterios de aceptación

1. Usuario con `grades.manage` pide “pon P1=8 al estudiante X en curso Y” → tras confirmación, la nota existe en BD.
2. Usuario STUDENT pide borrar un curso → tool denegada; mensaje claro sin ejecutar.
3. ADMIN pide “asigna rol COORDINATOR a docente01” → tras confirmación, roles actualizados + audit.
4. TEACHER pide datos de dashboard global → denegado (SPEC-014); puede solicitar elevación.
5. No aparece SQL libre ni endpoints “/ai/raw”.
6. Chat sigue funcionando sin API key (fallback) pero **sin** tools mutantes en fallback.

---

## 8. Fuera de alcance

- Ejecución de shell / filesystem.
- Modificar `.env` o secretos de infraestructura.
- Impersonación completa (ya SPEC-008); el gateway puede *sugerir* impersonar solo si el usuario tiene ese permiso.

---

## 9. Modelos de IA sugeridos

Composer / Claude Sonnet — leer SPEC-016 + SKILL-015 (+ SPEC-017 si toca chat/reportes) antes de implementar.
