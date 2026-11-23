# SPEC-012 — Docente asignado en módulo Materias (perfil estudiante)

**Objetivo:** En el módulo **Materias**, los usuarios con rol STUDENT (y de forma coherente TEACHER/staff) deben ver el **nombre del docente** asignado a cada materia visible.

**Skills relacionadas:** SKILL-011  
**Specs relacionadas:** SPEC-004 (cursos/asignaciones), SPEC-009 (visibilidad por perfil)

---

## 1. Problema

Hoy `GET /subjects` y la tabla UI solo muestran código, nombre, créditos y carrera. La asignación docente vive en `assignments` → `courses` → `subjects`, pero no se expone al listar materias.

---

## 2. Reglas

1. El docente se obtiene de `Assignment` de los **cursos** de esa materia que el usuario puede ver:
   - STUDENT → cursos con matrícula activa (periodos visibles).
   - TEACHER → cursos asignados.
   - Staff → cursos de periodos visibles o todos, según permisos.
2. Una materia puede tener **varios** docentes (varios paralelos/periodos): mostrar todos, separados por coma, sin duplicados.
3. Si no hay asignación: mostrar texto `Sin docente asignado`.
4. Solo lectura en perfil estudiante (sin botones CRUD si no tiene permiso).

---

## 3. Contrato API

`GET /api/v1/subjects` — cada ítem incluye:

```json
{
  "id": 1,
  "code": "DSW103",
  "name": "Desarrollo Web",
  "credits": 3,
  "career_name": "Desarrollo de Software",
  "teachers": ["Ana García", "Luis Pérez"],
  "teachers_label": "Ana García, Luis Pérez"
}
```

---

## 4. UI módulo Materias

| Columna | Visible |
| --- | --- |
| Código | Sí |
| Nombre | Sí |
| Créditos | Sí |
| Carrera | Sí (si aplica) |
| **Docente(s)** | **Sí (nuevo)** |
| Acciones | Solo si `subjects.edit` / create |

Nota opcional para STUDENT: “Docentes de sus cursos en periodos habilitados.”

---

## 5. Criterios de aceptación

1. Login `est0001` → Materias muestra al menos un nombre de docente por materia con curso asignado.
2. El docente coincide con el `Assignment` del curso matriculado.
3. Staff sigue viendo materias; columna Docente(s) también informativa.
4. No se rompe el CRUD de materias para admin/coordinador.

---

## 6. Modelos de IA sugeridos

Composer, Claude Sonnet — leer SPEC-012 + SKILL-011 antes de editar.
