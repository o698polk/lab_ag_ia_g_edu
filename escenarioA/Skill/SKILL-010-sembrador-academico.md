# SKILL-010 — Sembrador académico coherente (laboratorio avanzado)

**Spec:** SPEC-011  
**También aplica:** SPEC-004, SPEC-007, SPEC-009, SPEC-014

## Rol del agente

Regenerar en MySQL (`laboratorioA`) un dataset coherente: 3 carreras, 2 periodos, 20 docentes, 400 estudiantes, staff, matrículas, notas, asistencias y horarios.

## Procedimiento

1. Leer SPEC-011.
2. Confirmar `DATABASE_URL` → `laboratorioA` y MySQL XAMPP activo.
3. Asegurar `seed_all` (roles/admin) si hace falta.
4. Ejecutar `seed_coherent(app, reset=True)` desde `App/backend`.
5. Verificar conteos y logins demo.

```powershell
cd App\backend
$env:PYTHONPATH="..\database\seeds"
.\.venv\Scripts\python.exe -c "from run import app; from seed_coherent import seed_coherent; print(seed_coherent(app))"
```

## Restricciones

- No borrar usuario `admin` protegido.
- No matricular estudiante en carrera ajena.
- Capacidad de curso ≥ tamaño de cohorte por carrera.
- Batch commits; Attendance nunca en 0.

## Credenciales demo (post-seed)

| Usuario | Clave | Rol |
| --- | --- | --- |
| admin | Admin123! | ADMIN |
| rector | Rector123! | RECTOR |
| auditor | Auditor123! | AUDITOR |
| coord01..03 | Coord123! | COORDINATOR |
| secretaria | Secretaria123! | SECRETARY |
| tutor1 | Tutor123! | GUARDIAN |
| itsupport | Soporte123! | IT_SUPPORT |
| docente01..20 | Docente123! | TEACHER |
| est0001..0400 | Estudiante123! | STUDENT |
