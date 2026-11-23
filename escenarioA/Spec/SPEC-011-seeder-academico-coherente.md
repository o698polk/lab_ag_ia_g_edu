# SPEC-011 — Seeder académico coherente (laboratorio avanzado)

**Objetivo:** Generar (y regenerar) un dataset de demo **coherente** para pruebas de uso y testing avanzado: 3 carreras, malla, 2 periodos, 20 docentes, 400 estudiantes, staff institucional, matrículas, notas, asistencias y horarios alineados.

**Skills relacionadas:** SKILL-010  
**Specs relacionadas:** SPEC-004, SPEC-007, SPEC-009, SPEC-014  
**BD objetivo:** `laboratorioA` (XAMPP, `DATABASE_URL` en `App/.env`)

---

## 1. Volumen objetivo

| Entidad | Cantidad |
| --- | --- |
| Carreras | 3 — Desarrollo de Software, Mecánica Automotriz, Mecanización Agrícola |
| Materias | 6 por carrera (malla progresiva) |
| Periodos | **2** (`2025-1`, `2025-2`), ambos `is_active=True` |
| Docentes | **20** (reparto 7 / 7 / 6 por carrera) |
| Estudiantes | **400** (reparto 134 / 133 / 133) |
| Staff | 1 Rector, 1 Auditor, 3 Coordinadores, 1 Secretaría, 1 Tutor (GUARDIAN), 1 Soporte TI (+ ADMIN existente) |

---

## 2. Reglas de coherencia

### 2.1 Periodos
| Código | Rol | grades_closed |
| --- | --- | --- |
| 2025-1 | Vigente (primer bloque de malla) | False |
| 2025-2 | Vigente (segundo bloque) | False |

Fechas reales no solapadas; sesiones de asistencia dentro del rango del periodo.

### 2.2 Malla progresiva
| Periodo | Índices de materias (0..5) |
| --- | --- |
| 2025-1 | 0, 1, 2 |
| 2025-2 | 3, 4, 5 |

- Un curso por (carrera, materia, periodo, paralelo A).
- Docente de la **misma carrera**.
- Un horario por curso (día/hora estables).
- Capacidad de curso ≥ estudiantes de la carrera.

### 2.3 Matrículas
- Cada estudiante solo en cursos de **su carrera**.
- En cada periodo: matrícula activa en las 3 materias del mapa.
- → 6 matrículas / estudiante (2 periodos × 3 materias).

### 2.4 Perfil de desempeño (`student.id % 5`)
Excelente / Bueno / Regular / Bajo / Irregular → notas + pesos de asistencia.  
Si promedio &lt; 7 → supletorio + `Grade.compute()`.

### 2.5 Asistencias
- 8–12 sesiones por matrícula en el `day_of_week` del `Schedule`.
- Estados: presente, ausente, tardanza, justificada.
- Unique `(student_id, course_id, session_date)`.

### 2.6 Staff y tutor
- Usuarios con roles institucionales (credenciales fijas).
- Tutor (`GUARDIAN`) vinculado a un estudiante demo vía `Student.guardian_user_id`.

### 2.7 Visibilidad
- Periodos activos visibles para STUDENT/TEACHER (SPEC-009).
- Docente solo ve cursos asignados.

---

## 3. Entregable técnico

- Script: `App/database/seeds/seed_coherent.py`
- Reset académico manteniendo `admin` protegido y roles/permisos.
- Ejecutable con venv del backend contra `laboratorioA`.

---

## 4. Criterios de aceptación

1. Carreras = 3 con nombres exactos del catálogo.
2. Teachers = 20, Students = 400.
3. Terms = 2 activos; Attendance &gt; 0; Grades ≈ Enrollments.
4. Login `est0001`: cursos/notas/asistencias &gt; 0 en periodos activos.
5. Login `docente01`: notas/asistencias de sus cursos &gt; 0.
6. Login `rector`, `auditor`, `coord01`, `secretaria`, `tutor1`, `itsupport` OK.

---

## 5. Modelos sugeridos

Composer — leer SPEC-011 + SKILL-010 antes de modificar seeds.
