# SPEC-019 — Filtros de búsqueda y exportación Excel/PDF en todos los módulos

**Objetivo:** Homogeneizar la usabilidad de listados: cada módulo de datos debe ofrecer **búsqueda por texto**, **filtros contextuales** (roles, fechas, carrera, periodo, curso, estado, etc.) y **descarga Excel + PDF** de los registros visibles/filtrados, respetando permisos y scope del usuario.

**Skills relacionadas:** SKILL-018  
**Specs relacionadas:** SPEC-004, SPEC-006, SPEC-009

---

## 1. Problema

Hoy solo Notas, Asistencia, Matrículas y Estudiantes tienen barra avanzada + export. Usuarios y el resto quedan con búsqueda simple o sin export, dificultando auditorías y operación diaria.

---

## 2. Filtros por módulo

| Módulo | Texto | Filtros adicionales | Export |
| --- | --- | --- | --- |
| Usuarios | Sí | **rol**, **estado** (activo/inactivo), **fechas** (created_at) | xlsx/pdf |
| Estudiantes | Sí | carrera, estado | xlsx/pdf (ya) |
| Docentes | Sí | estado (si aplica) | xlsx/pdf |
| Carreras | Sí | estado activa | xlsx/pdf |
| Materias | Sí | carrera | xlsx/pdf |
| Periodos | Sí | estado habilitado, fechas inicio | xlsx/pdf |
| Cursos | Sí | carrera, periodo | xlsx/pdf |
| Matrículas | Sí | fechas, carrera, periodo, curso, estado | xlsx/pdf (ya) |
| Horarios | Sí | periodo, curso | xlsx/pdf |
| Notas | Sí | carrera, periodo, curso, estado | xlsx/pdf (ya) |
| Asistencia | Sí | fechas, carrera, periodo, curso, estado | xlsx/pdf (ya) |
| Notificaciones | Sí | fechas, leída | xlsx/pdf |
| Auditoría | Sí | fechas, módulo (status/options) | xlsx/pdf |

Filtros son **client-side** sobre filas (`data-*`) + los mismos criterios se envían al export server-side.

---

## 3. Contrato export

`GET /api/v1/reports/{type}.xlsx|pdf?q=&from=&to=&career_id=&term_id=&course_id=&status=&role=`

Tipos nuevos: `users`, `teachers`, `careers`, `subjects`, `terms`, `courses`, `schedules`, `notifications`, `audit`.

Permisos: `reports.export` **o** el `.view` del módulo correspondiente.

---

## 4. UI

Extender `moduleHeader`:

- `filters`: `dates | career | term | course | status | role`
- `exportType`: string del catálogo
- `roleOptions` / meta.roles para Usuarios

---

## 5. Criterios de aceptación

1. Usuarios: filtrar por rol ADMIN y por rango de fechas → tabla y Excel coinciden en cantidad aproximada.
2. Cada módulo listado en §2 muestra búsqueda + al menos un filtro útil + botones Excel/PDF (si el usuario tiene permiso).
3. STUDENT/TEACHER solo exportan lo que su scope permite (igual que listados).
4. Sin permiso de vista del módulo → 403 en export.

---

## 6. Modelos sugeridos

Composer / Claude Sonnet — leer SPEC-019 + SKILL-018.
