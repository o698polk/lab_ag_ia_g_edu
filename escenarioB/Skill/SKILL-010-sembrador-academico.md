# SKILL-010 — Sembrador académico coherente

**Spec:** SPEC-011  
**También aplica:** SPEC-004, SPEC-007, SPEC-009

## Rol del agente

Analizar la BD académica, implementar/ejecutar un seeder que genere materias, cursos, matrículas, notas y asistencias **coherentes en todos los periodos**, y verificar con logins de estudiante/docente.

## Antes de codificar

1. Leer `Spec/SPEC-011-seeder-academico-coherente.md`.
2. Contar entidades actuales (Term, Course, Enrollment, Grade, Attendance).
3. Revisar `seed_massive.py` / `seed_data.py` y modelos `Grade`/`Attendance`/`Schedule`.
4. No inventar periodos fuera del catálogo; usar los existentes o recrearlos con el mismo código.

## Procedimiento

### Paso A — Spec/Skill
Asegurar SPEC-011 y esta SKILL; registrar en PROMPTSMASTER.

### Paso B — Script `seed_coherent.py`
1. `seed_all` si no hay roles.
2. `clear_academic_data` (reutilizar lógica de massive) + recrear carreras/materias/periodos.
3. Malla progresiva por periodo (tabla SPEC-011 §2.2).
4. Perfiles de estudiante → notas + pesos de asistencia.
5. Sesiones de asistencia en días del horario dentro de `[term.start_date, term.end_date]`.
6. `grade.compute()` / reglas de supletorio.
7. Activar periodos vigentes (`2025-1`, `2025-2`).
8. `sync_profile_visibility_perms`.

### Paso C — Ejecutar
Desde `App/backend` con venv:

```powershell
$env:PYTHONPATH="D:\PROYECTOS\laboratorioIA\App\database\seeds"
.\.venv\Scripts\python.exe -c "from run import app; from seed_coherent import seed_coherent; print(seed_coherent(app))"
```

### Paso D — Verificar
```text
Counts: Attendance>0, Grades==Enrollments, Terms active >= 1
API est0001: /courses /grades /attendance counts > 0
API docente01: /grades /attendance scoped > 0
```

## Restricciones

- No borrar usuario `admin` protegido.
- No dejar `Attendance = 0`.
- No matricular estudiante en carrera ajena.
- Batch commits para no saturar memoria.
- Credenciales demo documentadas al final del script.

## Entregables

- SPEC-011 + SKILL-010
- `seed_coherent.py` ejecutado con éxito
- Resumen de conteos post-seed
