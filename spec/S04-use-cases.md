# S04 — Casos de uso

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fuente | `prompt_master.md` §§12–42 |
| Fecha | 2026-09-20 |

---

## 1. Actores

| Actor | Descripción |
|---|---|
| Administrador | Gestiona IAM, catálogos, periodos, auditoría (con permisos explícitos) |
| Docente | Opera cursos asignados: asistencia, evaluaciones, calificaciones |
| Estudiante | Consulta información propia; usa asistente IA autorizado |
| Sistema (PDP/Gateway) | Decide ALLOW/DENY y registra evidencia |
| Agente IA | Propone tools; no decide ni ejecuta sin Gateway |

---

## 2. Diagrama de contexto de casos de uso (textual)

```text
Admin ── CU-AUTH, CU-IAM, CU-CAT, CU-TERM, CU-ENR, CU-REP, CU-AUD, CU-POL
Teacher ── CU-AUTH, CU-ATT, CU-EVAL, CU-GRD, CU-SCH (propios), CU-AI*
Student ── CU-AUTH, CU-GRD-R, CU-ATT-R, CU-KAR, CU-SCH-R, CU-AI
* solo tools permitidos por política
```

---

## 3. Casos de uso prioritarios

### CU-AUTH-01 — Iniciar sesión
- **Actor:** Todos  
- **Pre:** Usuario activo  
- **Flujo:** Credenciales → validar → emitir access+refresh → auditar  
- **Post:** Sesión activa  
- **Excepciones:** Credenciales inválidas, cuenta bloqueada  

### CU-AUTH-02 — Refrescar token
- **Actor:** Usuario autenticado  
- **Flujo:** Refresh válido → nuevo access → rotación según política  

### CU-AUTH-03 — Cerrar sesión / invalidar refresh
- **Actor:** Usuario autenticado  

### CU-IAM-01 — Administrar usuarios
- CRUD lógico, activar/desactivar, reset password, asignar roles  

### CU-IAM-02 — Administrar roles y permisos
- Crear/editar roles; asignar/revocar permisos atómicos  

### CU-STU-01 — Gestionar estudiantes
- Alta/actualización de perfil académico y personal  

### CU-TCH-01 — Gestionar docentes
- Alta/actualización; consulta de carga  

### CU-CAT-01 — Gestionar carreras, malla, asignaturas
- Mantener catálogo curricular con prerrequisitos  

### CU-TERM-01 — Gestionar periodos académicos
- PLANNED → ACTIVE → CLOSED; bloquear edición de cerrados sin operación especial  

### CU-CRS-01 — Gestionar paralelos/cursos y cupos  

### CU-ASN-01 — Asignar docente a curso (teaching_assignment)
- Base de autorización contextual  

### CU-ENR-01 — Matricular / cancelar matrícula
- Estados ACTIVE / CANCELLED / COMPLETED  

### CU-SCH-01 — Gestionar horarios
- Detectar conflictos docente/aula/curso  

### CU-ATT-01 — Registrar asistencia
- Solo docente asignado; estados PRESENT/ABSENT/LATE/JUSTIFIED  

### CU-EVAL-01 — Definir evaluaciones del curso
- Porcentajes; `sum(porcentajes) <= 100`  

### CU-GRD-01 — Registrar/modificar calificación
- Docente asignado + permiso + política + transacción + auditoría  

### CU-GRD-02 — Consultar calificaciones propias (estudiante)
- Solo recursos del `CURRENT_USER`  

### CU-KAR-01 — Consultar Kardex
- Historial académico filtrable/exportable según permiso  

### CU-REP-01 — Generar reporte
- Registrar usuario, tipo, parámetros, resultado  

### CU-AI-01 — Consultar asistente académico
- NL → tool proposal → Gateway → PDP → ejecución o DENY  

### CU-AI-02 — Intento de operación sensible vía IA (ej. update_grade)
- Propuesta posible; **DENY** si política/contexto no autoriza; auditar  

### CU-AUD-01 — Consultar auditoría / security events
- Solo roles/permisos autorizados  

### CU-POL-01 — Administrar políticas (PAP)
- Versionar, activar/desactivar policies  

---

## 4. Matriz actor × caso de uso (resumen)

| CU | Admin | Teacher | Student |
|---|---|---|---|
| AUTH | X | X | X |
| IAM | X | — | — |
| CAT/TERM/CRS/ASN/ENR | X | limitado | — |
| ATT/EVAL/GRD write | — | propio curso | — |
| GRD/ATT/KAR/SCH read | X | propio | propio |
| AI assist | X* | X* | X* |
| AUD/POL | X | — | — |

\* según `ai.use` y tools permitidos.

---

## 5. Reglas transversales

1. Deny by Default.  
2. Revalidar identidad/estado/rol/permiso/contexto en servidor.  
3. Operaciones críticas en transacción + auditoría.  
4. IA nunca escribe BD directamente.  
5. Administrador también requiere permission + policy + audit.

---

## 6. Trazabilidad

| CU | Requisitos (S05) | Historias (S07) |
|---|---|---|
| CU-AUTH-* | RF-AUTH-* | HU-AUTH-* |
| CU-GRD-* | RF-GRD-* | HU-GRD-* |
| CU-AI-* | RF-AI-* | HU-AI-* |
| CU-AUD-* | RF-AUD-* | HU-AUD-* |
