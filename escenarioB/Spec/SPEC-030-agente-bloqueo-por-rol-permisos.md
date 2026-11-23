# SPEC-030 — Agente IA: bloqueo por rol y permisos (mínimo privilegio)

**Objetivo:** El asistente IA debe respetar **exactamente** la matriz IAM del usuario. Un docente o estudiante **no** puede obtener por chat (ni Excel/PDF) datos o acciones que su rol no permite en la UI (p. ej. «reporte de todos los usuarios del sistema»). Toda solicitud fuera de permiso se **bloquea**, se registra en LogIA/Auditoría y no se entrega el archivo.

**Skills relacionadas:** SKILL-029  
**Specs relacionadas:** SPEC-003, SPEC-016, SPEC-026, SPEC-028, SPEC-029, `permisos_role.md`, `politas_Agente_Ia.md`

---

## 1. Principio

| Regla | Detalle |
| --- | --- |
| Paridad UI ↔ Agente | Si el rol no tiene el permiso en REST/UI, tampoco vía lenguaje natural ni tools. |
| Tools filtradas | El LLM solo recibe schemas de tools para las que el usuario tiene permiso (o política especial válida). |
| Intent pre-LLM | Solicitudes sensibles en lenguaje natural se validan **antes** del LLM si implican un permiso que el usuario no tiene. |
| Scope de datos | Aunque haya permiso de vista parcial (p. ej. `students.view` de docente), los listados/reportes se limitan a cursos propios. |
| Observabilidad | Bloqueos → `privilege_block` / `policy_block` + dual-log SPEC-028 + `user_question` SPEC-029. |

---

## 2. Matriz operativa (roles con `ai.use`)

Referencia seed (`seed_data.py` / `permisos_role.md`). Resumen de lo **prohibido** vía agente:

| Rol | No puede solicitar vía agente (ejemplos) | Sí puede (ejemplos acotados) |
| --- | --- | --- |
| **TEACHER** | Usuarios del sistema, roles, auditoría, docentes globales, reportes institucionales (`reports.export`), stats globales | Notas/asistencia/estudiantes **de sus cursos**, tools con sus `.view`/`.manage` |
| **STUDENT** | Usuarios, estudiantes ajenos, docentes, roles, reportes globales, stats globales | Sus notas/asistencia/matrículas (scope propio) |
| **SECRETARY** | Asignar roles admin, config IAM avanzada sin permiso | Estudiantes, matrículas, reportes según seed |
| **RECTOR / COORDINATOR** | Mutaciones sin permiso; tools IAM sin `users.*` | Lectura amplia + `reports.*` según seed |
| **ADMIN** | — (bypass) | Todo |

Cualquier tool del catálogo (`HANDLERS`) exige su permiso executor; si falta → bloqueo (ya SPEC-028). Esta SPEC cierra huecos: tools sin permiso expuesto al LLM, reportes sin scope, NL de exfiltración.

---

## 3. Controles técnicos

### 3.1 Catálogo de tools por usuario (`tools_for_user`)

1. Partir de `TOOL_SCHEMAS` ∩ `HANDLERS`.
2. Omitir tools cuyo `perm` el usuario no tenga.
3. `system_stats`: solo si tiene `dashboard.view` **o** `reports.view` **o** `users.view` (no TEACHER/STUDENT del seed).
4. `reports_generate` / `reports_list_types`: solo si `user_can_report` es true para **al menos** un tipo; el enum `report_type` se reduce a los tipos permitidos.
5. No exponer tools huérfanas (schema sin handler).

### 3.2 Escáner de intención no autorizada (`scan_unauthorized_intent`)

Antes del LLM (después de anti-injection), detectar NL que implique:

| Intent | Patrones típicos (ES/EN) | Permiso(s) cualquiera |
| --- | --- | --- |
| Directorio de usuarios | «reporte/listado de todos los usuarios», «usuarios del sistema» | `users.view` o `reports.export` |
| Roles IAM | «lista de roles», «todos los roles» | `roles.view` |
| Auditoría | «logs de auditoría», «ver auditoría» | `audit.view` |
| Docentes globales | «todos los docentes/profesores del sistema» | `teachers.view` o `reports.export` |
| Export institucional masivo de estudiantes | «todos los estudiantes del sistema/institución» (no «mis estudiantes») | `reports.export` **o** (`students.view` **y** sin restricción de cursos / staff) |

Si no hay permiso → bloquear sin LLM, mensaje de política, `log_security_block` (`privilege_block` + `policy_block` opcional), `user_question` = mensaje.

### 3.3 Reportes y scope

1. `filter_students` debe aplicar el mismo scope que `students_list` (`owned_course_ids`).
2. `user_can_report` se mantiene (OR de `reports.export` y permiso de dominio).
3. Sin `reports.export`, un TEACHER solo obtiene estudiantes de **sus** cursos (nunca el directorio completo).
4. Pedidos de «usuarios del sistema» nunca deben mapearse a un Excel amplio vía `students` si faltan `users.view`/`reports.export` (intent guard + tools filtradas).

### 3.4 System prompt

Recordar al modelo: roles/permisos del usuario actual; no inventar tools; no intentar datos fuera de alcance; si el usuario pide algo no autorizado, indicar que no tiene permiso (el sistema ya habrá bloqueado intents claros).

---

## 4. Criterios de aceptación

1. Login como **TEACHER** → «Necesito un reporte de todos los usuarios del sistema» → **bloqueado**, sin Excel, fila roja LogIA con la pregunta.
2. TEACHER → «reporte de mis estudiantes» / notas de su curso → permitido y **solo** scope propio.
3. **STUDENT** → pedido de usuarios o todos los estudiantes → bloqueado.
4. Rol con `users.view` / `reports.export` → puede generar reporte/listado de usuarios según catálogo.
5. El LLM no recibe schemas de `users_list` si el usuario no tiene `users.view`.
6. SPEC/SKILL + PROMPTSMASTER + `permisos_role.md` / politas actualizados.

---

## 5. Modelos sugeridos

Composer — leer SPEC-030 + SKILL-029 e implementar.
