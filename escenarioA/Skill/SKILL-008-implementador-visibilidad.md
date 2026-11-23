# SKILL-008 — Implementador de Visibilidad por Perfil

**Spec:** SPEC-009  
**También aplica:** SPEC-003, SPEC-004, SPEC-002 (A01)

## Rol del agente

Aplicar scope de datos por rol (STUDENT / TEACHER) en backend y frontend, alinear horarios con cursos/materias del usuario, y excluir el módulo Kárdex de estudiantes y docentes.

## Antes de codificar

1. Leer `Spec/SPEC-009-visibilidad-perfil.md` completa.
2. Revisar `App/backend/app/services/visibility.py` y listados en `academic.py` / `system_api.py`.
3. Revisar `ROLE_PERMS` en `App/database/seeds/seed_data.py` y menú en `App/frontend/static/js/app.js`.
4. No “arreglar” solo el UI: el filtro debe vivir en la API.

## Procedimiento (orden obligatorio)

### Paso A — Permisos IAM
1. En `ROLE_PERMS`:
   - STUDENT: eliminar `kardex.view`, `kardex.export`; añadir `enrollments.view`.
   - TEACHER: eliminar `kardex.view`.
2. Implementar `sync_profile_visibility_perms()` que:
   - Quite permisos de kárdex a roles STUDENT y TEACHER en BD existente.
   - Añada `enrollments.view` a STUDENT si falta.
3. Invocarla desde `run.py` (tras `seed_all`) y/o seeder masivo.

### Paso B — Servicio de visibilidad
En `visibility.py` centralizar helpers:
- `owned_course_ids(user) -> list[int] | None`  
  - `None` = sin restricción de propiedad (staff).  
  - Lista (posible vacía) = IDs permitidos para STUDENT/TEACHER.
- Reutilizar `filter_courses_query` y/o filtrar queries con `Course.id.in_(owned_course_ids or [-1])`.

### Paso C — Endpoints
Aplicar scope en:
- `GET /schedules` → cursos owned + periodos visibles; enriquecer `Schedule.to_dict` con `subject_name`, `term_name`, `parallel`.
- `GET /grades`, `GET /attendance`, `GET /enrollments` → owned según rol.
- `GET /students` → TEACHER solo estudiantes de sus cursos.
- `GET /kardex/<id>` y PDF → 403 si rol es STUDENT o TEACHER (salvo que SPEC se relaje en el futuro; hoy: exclusión total).

### Paso D — Frontend
1. `navItems()`: no mostrar Kárdex si roles incluyen STUDENT o TEACHER (aunque exista permiso residual).
2. Página Horarios: columnas Curso, Materia, Periodo, Día, Hora, Aula.
3. Página Cursos/Notas: ya consumen API scoped; no pedir `/students` completo si no aplica.
4. Matrículas visible para STUDENT (solo lectura).

### Paso E — Verificación
Con servidor en marcha:
```text
POST /auth/login  { est0001 / Estudiante123! }
GET  /courses, /grades, /schedules  → solo propios; counts > 0 si hay periodo activo
GET  /kardex/1 → 403
POST /auth/login  { docente01 / Docente123! }
GET  /courses, /schedules → solo asignados; sin menú kárdex
```

## Restricciones

- No exponer listados globales a STUDENT/TEACHER “por conveniencia”.
- No eliminar el módulo Kárdex del sistema; solo ocultarlo a esos roles.
- Mantener periodos múltiples visibles (`Term.is_active`) para roles restringidos.
- No degradar permisos de ADMIN/SECRETARY/RECTOR sobre kárdex.

## Entregables

- SPEC-009 (ya creada) + esta SKILL.
- Cambios en seeds, `visibility.py`, `academic.py`, `system_api.py`, `app.js`, modelo `Schedule.to_dict` si aplica.
- Prueba de humo documentada (login estudiante/docente).
