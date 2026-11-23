# SPEC-015 — Asistencia por roster + cupo máximo por paralelo

**Objetivo:** Corregir la usabilidad grave del módulo **Asistencia**: dejar de registrar alumno por alumno en un modal, y pasar a una **tabla única tipo listado de Notas** con controles editables (check / estado rápido) sobre **todos los matriculados del curso** en una fecha. Además, limitar el realismo académico a **máximo 60 estudiantes por curso (paralelo)**; si la demanda supera 60, deben existir **paralelos distintos** (A, B, C…).

**Skills relacionadas:** SKILL-014  
**Specs relacionadas:** SPEC-004 (módulos), SPEC-006 (UI/UX), SPEC-007 (BD/cursos), SPEC-009 (visibilidad docente), SPEC-011 (seeder)

---

## 1. Problema actual

| Área | Hoy | Impacto |
| --- | --- | --- |
| UI Asistencia | Modal 1 estudiante × 1 fecha (`openAttendanceForm`) | Toma lenta, no usable en clase |
| Listado | Historial plano de registros individuales | No guía “pasar lista” |
| Notas (referencia) | Tabla con columnas editables conceptuales (P1/P2) + filtros curso | Modelo mental ya conocido por docentes |
| Cupo | `Course.capacity` default 40–50; seeder matricula **toda** la carrera en un solo paralelo | Cursos irreales de 100+ alumnos |

---

## 2. Reglas de negocio — cupo y paralelos

1. **Cupo máximo institucional:** `MAX_COURSE_CAPACITY = 60`.
2. Todo `Course.capacity` debe estar en rango `1…60`. Default recomendado al crear curso: **40** (configurable), nunca > 60.
3. Al **matricular** (`POST /enrollments`):
   - Contar matrículas con `status = "activa"` del `course_id`.
   - Si `count >= course.capacity` → **409** con mensaje claro: cupo lleno; sugerir otro paralelo.
4. Al **crear/editar curso** (`POST/PUT /courses`):
   - Si `capacity > 60` → **400**.
   - Si se reduce `capacity` por debajo del número actual de matrículas activas → **400** (o exigir reasignación previa).
5. **División en paralelos (realismo):**
   - Misma materia + mismo periodo + misma carrera pueden tener varios `Course` con `parallel` distinto (`A`, `B`, `C`…).
   - Código sugerido: `{subject.code}-{term.code}-{parallel}` (ej. `DSW103-2025-1-A`).
   - El seeder / carga masiva **no** debe poner más de 60 alumnos en un paralelo; repartir en A, B, C… (round-robin o bloques de ≤60).

---

## 3. UX — toma de asistencia (roster)

### 3.1 Flujo docente (prioridad)

1. Entrar a **Asistencia**.
2. Seleccionar **Curso (paralelo)** y **Fecha de sesión** (default: hoy).
3. Ver **una sola tabla** con todos los estudiantes matriculados activos del curso, ordenados por apellido/nombre.
4. Marcar estado por fila con control rápido (no modal por alumno):
   - Preferido: grupo de botones o select compacto / checkbox “presente” con cambio de estado.
   - Estados: `presente` | `ausente` | `tardanza` | `justificada`.
5. **Guardar sesión** (un clic) → persiste todos los cambios de esa fecha/curso.
6. Opcional: “Marcar todos presentes” / “Marcar todos ausentes” antes de ajustar excepciones.

### 3.2 Analogía con Notas

Usuario pide “seguir el formato del modelo de tomar notas, pero con inputs editables tipo check”:

| Notas | Asistencia (nuevo) |
| --- | --- |
| Filtro por curso | Selector curso obligatorio para modo roster |
| Filas = estudiantes del ámbito | Filas = matriculados del curso elegido |
| Celdas P1/P2 numéricas | Celdas de estado (check/toggle/select) |
| Guardado por fila o upsert | Guardado por **lote** de la sesión |

El listado histórico de asistencias puede permanecer como vista secundaria o pestaña “Historial”, pero el **modo principal** con `attendance.manage` es el **roster**.

### 3.3 Perfil estudiante

- Solo lectura: sus propios registros (como hoy).
- Sin controles de edición ni roster de compañeros.

### 3.4 Controles UI (mínimo)

Por fila:

- `#` (orden)
- Código estudiante
- Nombre
- Estado (editable si `attendance.manage`)
- Notas / observación (input texto corto opcional)
- Indicador si ya existía registro previo ese día

Cabecera:

- Curso, Fecha, contador `N / capacity` (ej. 28/40), botones Marcar todos / Guardar sesión.

---

## 4. Contrato API

### 4.1 Roster de sesión (lectura)

`GET /api/v1/attendance/roster?course_id=&session_date=YYYY-MM-DD`

Requiere: `attendance.view` (y scope de curso del docente).

Respuesta:

```json
{
  "course_id": 12,
  "course_name": "Desarrollo Web (2025-1) — Paralelo A",
  "parallel": "A",
  "capacity": 40,
  "enrolled_count": 28,
  "session_date": "2026-10-09",
  "students": [
    {
      "student_id": 5,
      "student_code": "EST0001",
      "full_name": "Pérez Ana",
      "attendance_id": 90,
      "status": "presente",
      "notes": null
    }
  ]
}
```

- Si no hay registro previo: `attendance_id: null`, `status` default sugerido `"presente"` (o vacío hasta marcar; la implementación elige uno y lo documenta en Skill).
- Orden: `full_name` ASC (o apellido si el modelo lo permite).

### 4.2 Guardado en lote (escritura)

`POST /api/v1/attendance/bulk`

Requiere: `attendance.manage` + docente dueño del curso (misma regla que hoy).

```json
{
  "course_id": 12,
  "session_date": "2026-10-09",
  "records": [
    { "student_id": 5, "status": "presente", "notes": null },
    { "student_id": 6, "status": "ausente", "notes": "Sin aviso" }
  ]
}
```

- Upsert por `(student_id, course_id, session_date)`.
- Validar que cada `student_id` tenga matrícula **activa** en ese curso.
- Máximo de ítems en `records`: ≤ 60 (alineado al cupo).
- Respuesta: lista de registros guardados + flags `critical_absence` por estudiante si aplica.

### 4.3 Compatibilidad

- Mantener `POST /attendance` individual (modal/historial) para no romper clientes; el flujo UI principal usa bulk.
- `GET /attendance` sigue sirviendo historial/filtros/export.

### 4.4 Cupo en matrícula / cursos

- `POST /enrollments`: validar cupo (sección 2).
- `POST|PUT /courses`: validar `capacity ≤ 60`.
- Opcional en `to_dict` de curso: `enrolled_count`, `seats_left`.

---

## 5. Seeder / datos demo

Actualizar `seed_coherent` / `seed_massive` (cuando se re-siembren):

1. `capacity = min(deseado, 60)` (ej. 40 o 60).
2. Estudiantes de la carrera repartidos en paralelos A, B, … de tamaño ≤ capacity.
3. Cada paralelo con su `Assignment` (puede ser el mismo u otro docente).
4. Asistencias y notas solo para alumnos del paralelo correspondiente.

---

## 6. Criterios de aceptación

1. Docente elige curso + fecha → ve **todos** los matriculados en **una tabla**, sin abrir un modal por alumno.
2. Puede marcar estados con controles tipo check/toggle/select en la tabla y guardar la sesión completa en una acción.
3. Intentar matricular el alumno 61 en un curso con `capacity=60` → **409**.
4. Crear curso con `capacity=80` → **400**.
5. Tras re-seed coherente: ningún paralelo activo tiene > 60 matrículas activas; si hay más alumnos, existen paralelos B/C.
6. Estudiante no ve roster de compañeros ni puede bulk-guardar.
7. Export/historial de asistencia siguen funcionando.

---

## 7. Fuera de alcance

- Lector biométrico / QR.
- Justificación con carga de archivos.
- Recálculo automático de paralelos al editar cupo (solo validación + mensaje).

---

## 8. Modelos de IA sugeridos

Composer, Claude Sonnet — leer SPEC-015 + SKILL-014 antes de editar código.
