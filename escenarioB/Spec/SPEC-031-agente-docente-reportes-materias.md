# SPEC-031 — Agente docente: reportes de materias y respuestas con datos reales

**Objetivo:** Corregir el comportamiento del agente para el perfil **TEACHER** (caso LogIA `docente30`): las consultas legítimas sobre **materias/cursos que imparte**, generación de **Excel/PDF** y listados de **estudiantes de su materia** deben devolver nombres y archivos reales, sin falsos bloqueos ni respuestas vacías de solo conteos.

**Skills relacionadas:** SKILL-030  
**Specs relacionadas:** SPEC-015, SPEC-016, SPEC-022, SPEC-030, `permisos_role.md`

---

## 1. Hallazgos LogIA (`docente30`)

| Pregunta | Comportamiento observado | Causa |
| --- | --- | --- |
| Pruebas de “todos los usuarios” / spoof admin | Bloqueo correcto (`privilege_block`) | SPEC-030 OK |
| «genera un reportes de las materias que doy clase» | Sin Excel; solo totales | Sin `report_type=courses`; brief sin nombres |
| «nombre de la materia…» | No nombra *Mecanización de Cosecha* | `_tool_result_brief` → `{count}` |
| «listado de usuarios en mi materia» (estudiantes) | Respuesta de denegación / sin Excel | Prompt rígido + sin `reports_generate` students |
| «dame el reporte» | Sin artifact | LLM no invoca `reports_generate` |

Asignación real: `MAG104-2025-2-A` — Mecanización de Cosecha (2025-2).

---

## 2. Requisitos

### 2.1 Briefs y composición con nombres

1. `_tool_result_brief`: para listas, incluir hasta N ítems slim (`id`, `code`, `name`, `full_name`, `subject_name`, `enrolled_count` según tool).
2. `_compose_user_reply`: listar nombres de `courses_list`, `subjects_list`, `grades_list` (no solo users/students/teachers).
3. Preferir `courses_list` (scoped) para «materias que doy / que dicto».

### 2.2 Reportes del agente

Añadir a `REPORT_TYPES` del agente:

| Tipo | Permiso | Scope |
| --- | --- | --- |
| `courses` | `reports.export` **o** `courses.view` | `filter_courses` (ya scoped) |
| `subjects` (opcional) | `reports.export` **o** `subjects.view` | Si el usuario es TEACHER scoped → solo subjects de sus courses |

Enum de `reports_generate` y `tools_for_user` deben incluir los tipos permitidos.

Ante «reporte de las materias que doy» → `reports_generate` `courses` + `xlsx` (o pdf).

### 2.3 Intent / prompt

1. No bloquear NL que pida usuarios/estudiantes **de mi materia/curso** (scope propio); sí bloquear directorio institucional.
2. System prompt: permitir listar/exportar estudiantes y cursos **propios**; prohibir directorio global de usuarios.

### 2.4 `subjects_list` para docente

Si el usuario tiene `owned_course_ids` (lista), filtrar subjects a las materias de esos cursos (o documentar que «materias que dicto» = `courses_list`).

---

## 3. Criterios de aceptación

1. `docente30`: «¿qué materia doy?» → responde con **Mecanización de Cosecha** (nombre visible).
2. «genera un reporte excel de las materias que doy» → artifact descargable `courses_*.xlsx`.
3. «excel de los estudiantes de mi materia» → `students` report o listado con nombres; **no** `privilege_block` institucional.
4. Pruebas de «todos los usuarios del sistema» siguen bloqueadas.
5. SPEC/SKILL + PROMPTSMASTER actualizados.

---

## 4. Modelos sugeridos

Composer — SPEC-031 + SKILL-030; asistencia roster en paralelo vía SPEC-015 / SKILL-014.
