# SKILL-014 — Roster de asistencia + cupo por paralelo

**Spec:** SPEC-015  
**También aplica:** SPEC-004, SPEC-006, SPEC-009, SPEC-011

## Rol del agente

Implementar toma de asistencia usable (tabla roster con estados editables) y forzar realismo de cupo (máx. 60 por paralelo, división A/B/C en seeders y validación API).

## Procedimiento

### A. Constantes y validación backend

1. Leer SPEC-015.
2. Definir constante `MAX_COURSE_CAPACITY = 60` (p. ej. en `app/services/enrollment.py` o `config`).
3. En `create_course` / `update_course` (`academic.py`):
   - Rechazar `capacity > 60` o `capacity < 1` con 400.
   - En update: si hay más matrículas activas que el nuevo cupo → 400.
4. En `create_enrollment`:
   - Contar `Enrollment` activas del curso; si `>= course.capacity` → 409.
5. Opcional: añadir `enrolled_count` / `seats_left` en `Course.to_dict()`.

### B. API roster + bulk

1. `GET /attendance/roster?course_id=&session_date=`:
   - Scope: `apply_course_scope` / `_teacher_owns_course` / estudiante solo si es su curso (o denegar roster a STUDENT).
   - Join matrículas activas + usuario; left join `Attendance` de esa fecha.
   - Orden alfabético por nombre.
2. `POST /attendance/bulk`:
   - Validar docente del curso, estados, fecha, tamaño ≤ 60.
   - Upsert cada registro (reutilizar lógica de `create_attendance`).
   - Devolver lista + alertas de ausencia crítica.
3. No eliminar `POST /attendance` individual.

### C. Frontend (`app.js` + CSS mínimo si hace falta)

1. Sustituir el flujo principal de `Pages.attendance` cuando `hasPerm("attendance.manage")`:
   - Selectores **Curso** + **Fecha**.
   - Botón/cargar roster → tabla con `#`, código, nombre, estado (select o botones P/A/T/J), notes.
   - Acciones: “Todos presentes”, “Guardar sesión” → `POST /attendance/bulk`.
2. Mantener vista historial (tabla actual + filtros/export) debajo o en pestaña secundaria.
3. Estudiantes: solo historial propio (sin roster editable).
4. Formulario de curso: `max="60"` en input cupo; texto ayuda “Máx. 60; si hay más alumnos, crear otro paralelo”.

### D. Seeders (realismo)

1. En `seed_coherent.py` / `seed_massive.py`:
   - `capacity ≤ 60` (recomendado 40 o 60).
   - Particionar estudiantes de la carrera en chunks de `capacity`.
   - Crear curso por chunk con `parallel` A, B, C… y código que incluya el paralelo.
   - Matricular, calificar y asistir solo dentro de ese chunk.
2. Re-ejecutar seeder solo si el entorno es demo/SQLite regenerable; no borrar producción sin confirmación.

### E. Verificación

1. Docente: roster muestra N filas = matrículas activas del paralelo.
2. Guardar sesión → `GET /attendance?course_id=&` refleja estados del día.
3. Matrícula 61 en curso capacity 60 → 409.
4. Curso capacity 80 → 400.
5. Tras seed: `max(count activas por course_id) ≤ 60`.

## Restricciones

- No abrir un modal por cada estudiante en el flujo principal.
- No mezclar alumnos de distintos paralelos en el mismo roster.
- No subir cupo por encima de 60 “para conveniencia”.
- Respetar scope SPEC-009 (docente solo sus cursos).
- No reescribir el módulo de Notas; solo inspirar el layout de tabla editable.
