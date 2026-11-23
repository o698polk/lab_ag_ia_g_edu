# SPEC-009 — Visibilidad por perfil (Estudiante / Docente)

**Objetivo:** Garantizar que cada usuario solo vea datos académicos de su propio ámbito, con horarios alineados a sus cursos/materias, y que roles restringidos no accedan al módulo Kárdex.

**Skills relacionadas:** SKILL-008  
**Specs relacionadas:** SPEC-003, SPEC-004, SPEC-002 (A01 Broken Access Control)

---

## 1. Principio

| Rol | Ámbito de datos |
| --- | --- |
| STUDENT | Solo sus matrículas activas, cursos matriculados, notas, asistencia, horarios de esos cursos, periodos habilitados |
| TEACHER | Solo cursos asignados (`assignments`), notas/asistencia/horarios/estudiantes de esos cursos, periodos habilitados |
| Staff (ADMIN, RECTOR, COORDINATOR, SECRETARY, …) | Según permisos; sin filtro de “propiedad” de curso (sí pueden filtrar por periodo) |

Regla de oro: **nunca filtrar solo en el frontend**. El backend debe aplicar el scope en cada listado.

---

## 2. Módulo Kárdex — exclusión

| Rol | `kardex.view` | `kardex.export` | Menú UI Kárdex |
| --- | --- | --- | --- |
| STUDENT | **No** | **No** | Oculto |
| TEACHER | **No** | **No** | Oculto |
| SECRETARY / RECTOR / ADMIN | Sí (según matriz) | Según matriz | Visible |

- Quitar permisos de kárdex a STUDENT y TEACHER en seeds y sincronizar BD existente.
- El frontend no debe listar Kárdex si el rol es STUDENT o TEACHER (defensa en profundidad).
- Endpoints `/kardex/*` deben rechazar STUDENT/TEACHER con 403 aunque tengan un permiso residual.

---

## 3. Alcance por endpoint

### 3.1 Cursos `GET /courses`
- Usar `filter_courses_query`:
  - STUDENT → `Enrollment` status `activa`
  - TEACHER → `Assignment`
  - + periodos visibles (`Term.is_active`) para roles restringidos

### 3.2 Notas `GET /grades`
- STUDENT → `student_id` propio
- TEACHER → `course_id` ∈ cursos asignados
- Intersección con periodos visibles

### 3.3 Horarios `GET /schedules`
- **Obligatorio** restringir a cursos del perfil (misma lógica que cursos):
  - STUDENT → horarios de cursos donde está matriculado (activa)
  - TEACHER → horarios de cursos asignados
- Respuesta debe incluir: `course_name`, `subject_name`, `term_name`, `parallel`, día, hora, aula
- Así el horario coincide con las materias del usuario

### 3.4 Matrículas `GET /enrollments`
- STUDENT debe tener `enrollments.view` (solo lectura de las propias)
- TEACHER: solo matrículas de cursos asignados (si tiene el permiso); si no lo tiene, no ve el menú
- Staff: sin filtro de propiedad

### 3.5 Asistencia `GET /attendance`
- STUDENT → propia
- TEACHER → solo cursos asignados

### 3.6 Estudiantes `GET /students`
- TEACHER → solo estudiantes matriculados en sus cursos (periodos visibles)
- STUDENT → no tiene `students.view`

### 3.7 Materias / Periodos
- STUDENT/TEACHER: solo periodos `is_active` y materias relacionadas a sus cursos visibles

---

## 4. Frontend

| Módulo | STUDENT | TEACHER |
| --- | --- | --- |
| Cursos | Lista de sus cursos | Lista de cursos asignados |
| Notas | Sus notas (sin CRUD) | Notas de sus cursos (CRUD si `grades.manage`) |
| Horarios | Solo sus cursos; columnas Curso + Materia + Periodo | Idem asignados |
| Matrículas | Sus matrículas (solo lectura) | Oculto salvo permiso |
| Kárdex | **No mostrar** | **No mostrar** |
| Estudiantes | No | Solo cohortes de sus cursos |

- En páginas de consulta (estudiante): ocultar botones crear/editar/eliminar.
- Contadores y filtros deben operar sobre el dataset ya scoped.

---

## 5. Seeds y sincronización

1. Actualizar `ROLE_PERMS` en `seed_data.py`:
   - STUDENT: quitar `kardex.*`; agregar `enrollments.view`
   - TEACHER: quitar `kardex.view`
2. Función `sync_profile_visibility_perms()` ejecutable en arranque / seeder para BD ya existentes (añadir/quitar permisos sin recrear todo).
3. Horarios en seed: cada `Schedule.course_id` debe apuntar al curso real de la materia/periodo (ya correcto en seed masivo); el problema de “no coinciden” se resuelve con el filtro de scope + campos `subject_name` en API.

---

## 6. Criterios de aceptación

1. Login `est0001` / `Estudiante123!` → ve notas > 0 (si tiene matrícula en periodo activo), cursos propios, horarios solo de esos cursos; **no** ve Kárdex.
2. Login `docente01` / `Docente123!` → ve solo sus cursos/notas/horarios; **no** ve Kárdex; lista de estudiantes limitada a sus cursos.
3. Intento de `GET /api/v1/kardex/1` como estudiante/docente → 403.
4. `GET /schedules` como estudiante no incluye cursos ajenos.
5. Admin sigue viendo todos los módulos según permisos.

---

## 7. Modelos de IA sugeridos

Claude Sonnet, GPT-4o, Composer — con lectura obligatoria de esta SPEC y SKILL-008 antes de modificar código.
