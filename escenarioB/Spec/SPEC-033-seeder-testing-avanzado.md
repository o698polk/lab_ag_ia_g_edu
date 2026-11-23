# SPEC-033 — Seeder coherente para testing avanzado

**Objetivo:** Regenerar `laboratorioB` con un dataset académico **cerrado y coherente** para pruebas de uso y testing avanzado (UI, APIs, agente IA, reportes, Excel, roles).

**Skills relacionadas:** SKILL-032  
**Specs relacionadas:** SPEC-011 (coherencia), SPEC-004 (notas/asistencia), SPEC-009 (visibilidad), SPEC-015 (cupo ≤ 60)

---

## 1. Volúmenes objetivo

| Entidad | Cantidad / regla |
| --- | --- |
| Carreras | **3**: DSW (Desarrollo de Software), MAG (Mecanización Agrícola), MAU (Mecánica Automotriz) |
| Materias | **6 por carrera** (catálogo fijo en `CAREERS_DEF`) |
| Periodos | **2**: `2025-1` (cerrado), `2025-2` (abierto); ambos `is_active=True` |
| Docentes | **20** (7 DSW + 7 MAU + 6 MAG) |
| Estudiantes | **400** (134 DSW + 133 MAU + 133 MAG) |
| Roles institucionales | 1 RECTOR, 1 AUDITOR, 3 COORDINATOR, 1 SECRETARY, 1 GUARDIAN, 1 IT_SUPPORT |
| Admin | 1 protegido (seed base) |

---

## 2. Reglas de coherencia

### 2.1 Malla por periodo (2 periodos × 3 materias)

| Periodo | Índices de materia (0..5) | Estado |
| --- | --- | --- |
| 2025-1 | 0, 1, 2 | `grades_closed=True`, `is_active=True` |
| 2025-2 | 3, 4, 5 | `grades_closed=False`, `is_active=True` |

### 2.2 Cursos y cupo
- Por (carrera, materia del periodo): repartir estudiantes en **paralelos** de tamaño ≤ 50 (`capacity` ≤ 60).
- Códigos: `{subject.code}-{term.code}-{parallel}` (A, B, C…).
- Docente de la **misma carrera**; rotación estable por índice.
- Un `Schedule` por curso (día/hora/aula coherentes con el índice de materia).

### 2.3 Matrículas
- Cada estudiante solo en cursos de **su carrera**.
- En cada periodo: matrícula en las 3 materias del mapa, en **exactamente un** paralelo.
- Status `activa`.

### 2.4 Notas y asistencias
- Perfil estable por `student.id % 5` (excelente → irregular).
- 10 sesiones por matrícula en fechas del periodo alineadas al `day_of_week` del horario.
- Correlación: más ausencias → leve penalización de notas.
- Si promedio &lt; 7 → supletorio + `compute()`.

### 2.5 Tutor
- Un usuario `GUARDIAN` vinculado a un estudiante de DSW (`guardian_user_id` + nombre/teléfono).

### 2.6 Credenciales de prueba (password fija por rol)

| Usuario | Password | Rol |
| --- | --- | --- |
| admin (config) | (ADMIN_PASSWORD) | ADMIN |
| rector | Rector123! | RECTOR |
| auditor | Auditor123! | AUDITOR |
| coord01..coord03 | Coord123! | COORDINATOR |
| secretaria | Secretaria123! | SECRETARY |
| tutor1 | Tutor123! | GUARDIAN |
| soporte | Soporte123! | IT_SUPPORT |
| docente01..docente20 | Docente123! | TEACHER |
| est0001..est0400 | Estudiante123! | STUDENT |

---

## 3. Entregable técnico

- Script principal: `App/database/seeds/seed_coherent.py`
- Orquestación: `App/backend/setup_mysql.py` → `seed_all` + `seed_coherent(reset=True)`
- Reutiliza `CAREERS_DEF` / `clear_academic_data` de `seed_massive.py`
- `seed_massive` queda como legado (no se invoca en setup)

---

## 4. Criterios de aceptación

1. Tras `python setup_mysql.py`: 3 carreras DSW/MAG/MAU, 2 periodos, 20 docentes, 400 estudiantes.
2. Existen usuarios de los 6 roles institucionales + admin.
3. Toda matrícula tiene nota y ≥ 4 asistencias; horarios y asignaciones presentes.
4. Ningún curso supera `capacity` 60 ni matrículas inconsistentes de carrera.
5. Login con las credenciales de la tabla 2.6 funciona para pruebas de rol.
