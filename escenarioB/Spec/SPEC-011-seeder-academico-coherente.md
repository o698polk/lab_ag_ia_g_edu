# SPEC-011 — Seeder académico coherente

**Objetivo:** Generar (y poder regenerar) datos de demo con **coherencia académica** entre periodos, materias, matrículas, notas y asistencias de cada estudiante.

**Skills relacionadas:** SKILL-010  
**Specs relacionadas:** SPEC-004 (notas/asistencia), SPEC-007 (BD), SPEC-009 (visibilidad por periodos activos)

---

## 1. Hallazgos del sistema actual (baseline)

| Entidad | Estado observado |
| --- | --- |
| Periodos | 4 (`2024-1`…`2025-2`); a menudo solo uno `is_active` |
| Carreras / materias | 3 carreras × 6 materias |
| Cursos | 72 (todas las materias en todos los periodos) |
| Matrículas / notas | ~2520; sin asistencia |
| Coherencia | Misma materia repetida en todos los periodos; sin vínculo nota↔asistencia |

---

## 2. Reglas de coherencia

### 2.1 Periodos
- Existen **todos** los periodos del catálogo (mín. 4).
- Cerrados históricos: `grades_closed=True`, `is_active=False` (p. ej. 2024-*).
- Vigentes visibles: `is_active=True` (p. ej. 2025-1 y 2025-2).
- Fechas de periodo reales y no solapadas.

### 2.2 Malla progresiva por carrera
Por carrera, las 6 materias se distribuyen por periodo (no repetir el mismo par en todos):

| Periodo | Materias (índices 0..5) |
| --- | --- |
| 2024-1 | 0, 1, 2 |
| 2024-2 | 1, 2, 3 |
| 2025-1 | 2, 3, 4 |
| 2025-2 | 3, 4, 5 |

- Un curso por (carrera, materia, periodo, paralelo A).
- Docente asignado de la misma carrera.
- Un horario por curso (día/hora estables).

### 2.3 Matrículas
- Cada estudiante se matricula **solo** en cursos de **su carrera**.
- En **cada periodo** existente: matrícula activa en las 3 materias de ese periodo.
- Así hay trayectoria en los 4 periodos (12 matrículas/estudiante).

### 2.4 Perfil de desempeño (por estudiante)
Asignar perfil estable (`student.id % 5`):

| Perfil | Notas (base) | Asistencia |
| --- | --- | --- |
| 0 Excelente | P1/P2 ~ 8.5–10 | ~95% presente |
| 1 Bueno | ~7.5–9.0 | ~88% presente |
| 2 Regular | ~6.0–8.0 | ~78% presente |
| 3 Bajo | ~4.5–7.0 | ~65% presente |
| 4 Irregular | ~5.0–8.5 alta varianza | ~70% + más tardanzas |

- Si promedio &lt; 7 → generar supletorio (regla SPEC-004) y `compute()`.
- Periodos cerrados: notas definitivas; vigentes: pueden quedar `aprobado`/`reprobado`/`en_curso` según datos.

### 2.5 Asistencias
- Por cada matrícula activa: generar N sesiones (8–12) en fechas del **rango del periodo**.
- Las fechas deben caer en el `day_of_week` del `Schedule` del curso.
- Estados: `presente`, `ausente`, `tardanza`, `justificada` según pesos del perfil.
- Correlación suave: más ausencias → empujar notas del perfil un poco hacia abajo.
- Unique `(student_id, course_id, session_date)`.

### 2.6 Visibilidad
- Tras el seed, estudiantes/docentes ven solo periodos `is_active` (SPEC-009).
- Debe haber notas y asistencias visibles en periodos activos.

---

## 3. Entregable técnico

- Script: `App/database/seeds/seed_coherent.py`
- Modo: regenerar datos académicos (reset) manteniendo admin/roles.
- Ejecutable desde consola con el venv del backend.
- Idempotente al re-ejecutar con reset.

---

## 4. Criterios de aceptación

1. `Attendance.count() > 0` y cubre matrículas de **todos** los periodos.
2. Cada estudiante tiene matrículas en los 4 periodos de su carrera.
3. No hay la misma terna de materias idéntica en todos los periodos (progresión).
4. Notas cumplen regla de supletorio si promedio &lt; 7.
5. Login `est0001`: en periodos activos ve cursos, notas y asistencias &gt; 0.
6. Login `docente01`: ve asistencias/notas de sus cursos asignados.

---

## 5. Modelos de IA sugeridos

Composer, Claude Sonnet — leer SPEC-011 + SKILL-010 antes de modificar seeds.
