# S07 — Historias de usuario

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fecha | 2026-09-20 |

Formato:

```text
Como <rol>, quiero <acción>, para <beneficio>.
Criterios de aceptación (CA)
Refs: RF / CU / BL
```

---

## HU-AUTH-001 — Login

Como usuario registrado, quiero iniciar sesión con mis credenciales, para acceder a SIGA según mi rol.

**CA**
1. Credenciales válidas + usuario ACTIVE → access + refresh.  
2. Credenciales inválidas → 401 sin filtrar si el user existe.  
3. Usuario bloqueado → denegado + auditoría.  

**Refs:** RF-AUTH-001/002 · CU-AUTH-01 · BL-O1-002

---

## HU-AUTH-002 — Refresh / Logout

Como usuario autenticado, quiero renovar mi sesión o cerrarla, para mantener seguridad de acceso.

**CA**
1. Refresh válido emite nuevo access.  
2. Logout invalida refresh/sesión.  
3. Refresh inválido → 401.  

**Refs:** RF-AUTH-003/004 · CU-AUTH-02/03 · BL-O1-002

---

## HU-IAM-001 — Gestionar usuarios

Como administrador, quiero crear y desactivar usuarios y asignarles roles, para controlar el acceso al sistema.

**CA**
1. Requiere permisos `users.*` / `roles.*`.  
2. Password nunca se almacena en claro.  
3. Soft delete / desactivación; no borrado físico arbitrario.  

**Refs:** RF-IAM-001…003 · CU-IAM-01 · BL-O1-004

---

## HU-IAM-002 — Permisos granulares

Como administrador, quiero asignar permisos atómicos a roles, para aplicar Deny by Default.

**CA**
1. Sin permiso explícito → DENY.  
2. Matriz rol→permiso consultable.  
3. Cambios auditados.  

**Refs:** RF-IAM-005…008 · CU-IAM-02 · BL-O1-005/006

---

## HU-TRM-001 — Periodo académico

Como administrador, quiero abrir y cerrar periodos, para controlar el ciclo académico.

**CA**
1. Estados PLANNED/ACTIVE/CLOSED/CANCELLED.  
2. Periodo CLOSED no admite cambios académicos normales.  
3. Excepción solo con operación autorizada + auditoría.  

**Refs:** RF-TRM-001/002 · CU-TERM-01 · BL-O2-003

---

## HU-ASN-001 — Asignación docente

Como administrador, quiero asignar un docente a un curso en un periodo, para habilitar su operación académica.

**CA**
1. Existe teaching_assignment (teacher_id, course_id, term_id).  
2. Sin asignación, docente no puede escribir asistencia/notas.  

**Refs:** RF-ASN-001 · CU-ASN-01 · BL-O3-002

---

## HU-ENR-001 — Matrícula

Como administrador, quiero matricular estudiantes en cursos, para registrar su participación académica.

**CA**
1. Matrícula ACTIVE vincula student-course-term.  
2. Respeta cupo si está configurado.  
3. Cancelación cambia estado y audita.  

**Refs:** RF-ENR-001/002 · CU-ENR-01 · BL-O3-003

---

## HU-ATT-001 — Registrar asistencia

Como docente, quiero registrar asistencia de mis estudiantes, para llevar control del curso.

**CA**
1. Solo si teaching_assignment existe.  
2. Estados PRESENT/ABSENT/LATE/JUSTIFIED.  
3. Intento en curso ajeno → DENY + audit.  

**Refs:** RF-ATT-001 · CU-ATT-01 · BL-O4-001/004

---

## HU-EVL-001 — Definir evaluaciones

Como docente, quiero definir evaluaciones con porcentaje, para estructurar la calificación del curso.

**CA**
1. Suma de porcentajes ≤ 100.  
2. Evaluación asociada a su curso asignado.  

**Refs:** RF-EVL-001 · CU-EVAL-01 · BL-O4-002

---

## HU-GRD-001 — Registrar calificación

Como docente, quiero registrar y modificar calificaciones de mi curso, para evaluar el desempeño.

**CA**
1. ALLOW solo con permiso + asignación + política.  
2. Operación en transacción: validar → autorizar → actualizar → auditar → commit.  
3. Curso ajeno → DENY.  

**Refs:** RF-GRD-001 · CU-GRD-01 · BL-O4-003/004

---

## HU-GRD-002 — Ver mis notas

Como estudiante, quiero ver mis calificaciones, para conocer mi rendimiento.

**CA**
1. Solo recursos del estudiante autenticado.  
2. Intento de ver notas de otro → DENY (anti-IDOR).  

**Refs:** RF-GRD-002 · CU-GRD-02 · BL-O4-005

---

## HU-KAR-001 — Kardex

Como estudiante, quiero consultar mi Kardex, para ver mi historial académico.

**CA**
1. Muestra periodo, asignatura, nota, estado, créditos.  
2. Exportación solo con permiso.  

**Refs:** RF-KAR-001 · CU-KAR-01 · BL-O4-006

---

## HU-AI-001 — Asistente académico

Como estudiante, quiero preguntar en lenguaje natural por mis notas o asistencia, para obtener información autorizada.

**CA**
1. IA propone tool (ej. get_grades).  
2. Gateway resuelve CURRENT_USER.  
3. PDP ALLOW → respuesta; sin permiso → DENY.  
4. IA no ejecuta SQL.  

**Refs:** RF-AI-001…005 · CU-AI-01 · BL-O6-003…005

---

## HU-AI-002 — Bloqueo de manipulación vía IA

Como sistema de seguridad, quiero denegar pedidos de cambiar notas vía IA cuando no haya autorización, para proteger integridad académica.

**CA**
1. Propuesta `update_grade` posible.  
2. PDP DENY para STUDENT (y teacher no asignado).  
3. Se registra security/audit event con reason_code.  

**Refs:** RF-AI-002 · CU-AI-02 · BL-O6-007

---

## HU-AUD-001 — Consultar auditoría

Como administrador, quiero consultar eventos de auditoría, para investigar acciones sensibles.

**CA**
1. Requiere `audit.view`.  
2. Campos mínimos: request_id, user, action, resource, status, timestamp.  

**Refs:** RF-AUD-001/003 · CU-AUD-01 · BL-O6-006

---

## HU-REP-001 — Reportes

Como administrador o docente autorizado, quiero generar reportes académicos, para análisis y seguimiento.

**CA**
1. Formatos HTML/CSV/JSON (PDF P2).  
2. Cada generación deja report_log.  

**Refs:** RF-REP-001/002 · CU-REP-01 · BL-O5-002

---

## Mapa rápido HU → Backlog

| HU | BL |
|---|---|
| HU-AUTH-* | BL-O1-002 |
| HU-IAM-* | BL-O1-004…006 |
| HU-TRM-001 | BL-O2-003 |
| HU-ASN/ENR | BL-O3-* |
| HU-ATT/EVL/GRD/KAR | BL-O4-* |
| HU-AI/AUD | BL-O6-* |
| HU-REP | BL-O5-002 |
