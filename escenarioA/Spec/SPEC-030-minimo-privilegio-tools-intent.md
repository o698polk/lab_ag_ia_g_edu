# SPEC-030 — Mínimo privilegio: tools filtradas + intent NL + scope reportes

**Objetivo:** El LLM solo recibe tools que el usuario puede usar; bloqueos pre-LLM de intenciones NL claramente fuera de permiso; `system_stats` y reportes de estudiantes respetan visión institucional / cursos propios.

**Skills relacionadas:** SKILL-029  
**Specs relacionadas:** SPEC-003, SPEC-009, SPEC-016, SPEC-029, `politas_Agente_Ia.md`

---

## 1. `tools_for_user(user)`

| Regla | Detalle |
| --- | --- |
| Fuente | `TOOL_SCHEMAS` ∩ permisos de `HANDLERS` |
| `perm` definido | Incluir solo si `user.has_permission(perm)` |
| `system_stats` | Solo con `dashboard.view` **o** `reports.view` **o** `users.view` (ADMIN bypass vía `has_permission`) |
| `reports_generate` | Solo si el usuario puede al menos un tipo (`user_can_report`) |
| Proveedor | `call_llm(..., use_tools=True)` usa `tools_for_user`, no el catálogo completo |

La denegación en executor se mantiene (defensa en profundidad).

---

## 2. `scan_unauthorized_intent(user, message)`

Bloqueo pre-LLM (después o junto a injection), con LogIA `privilege_block` + Auditoría `AI_PRIVILEGE_BLOCK`.

Ejemplos (heurística):

- «reporte/lista de todos los usuarios del sistema» sin `users.view` / `reports.export`
- Dump/listado masivo de auditoría sin `audit.view`

**No bloquear:** «¿cuál es mi rol?» / «¿qué permisos tengo?».

Excepción: mensajes de confirmación con `pending_action`.

---

## 3. Scope de reportes de estudiantes

`filter_students` (y reportes IA equivalentes) deben acotar a estudiantes de `owned_course_ids` cuando el usuario es docente/restringido (misma lógica que `students_list` del gateway).

---

## 4. Criterios de aceptación

1. STUDENT no recibe `users_list` ni `system_stats` en el schema del LLM.
2. STUDENT pide «reporte de todos los usuarios del sistema» → bloqueo `privilege_block` sin LLM.
3. TEACHER genera reporte `students` → solo alumnos de sus cursos.
4. TEACHER/STUDENT del seed no obtienen `system_stats` vía tool.
