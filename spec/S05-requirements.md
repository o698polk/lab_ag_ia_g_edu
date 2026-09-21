# S05 — Requisitos

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fuente | `prompt_master.md` + S01/S02 |
| Fecha | 2026-09-20 |

---

## 1. Convención de IDs

```text
RF-<ÁREA>-NNN   Requisito funcional
RNF-<ÁREA>-NNN  Requisito no funcional
```

Prioridad: **P0** (MVP crítico) · **P1** (necesario) · **P2** (diferible controlado)

---

## 2. Requisitos funcionales

### 2.1 Autenticación (AUTH)

| ID | Requisito | P |
|---|---|---|
| RF-AUTH-001 | Login con username/email + password | P0 |
| RF-AUTH-002 | Emisión de access token JWT y refresh token | P0 |
| RF-AUTH-003 | Refresh de access token con refresh válido | P0 |
| RF-AUTH-004 | Logout e invalidación de sesión/refresh | P0 |
| RF-AUTH-005 | Cambio de contraseña autenticado | P1 |
| RF-AUTH-006 | Recuperación de contraseña | P1 |
| RF-AUTH-007 | Bloqueo/desbloqueo de cuenta | P1 |
| RF-AUTH-008 | Expiración de sesión configurable | P0 |
| RF-AUTH-009 | Nunca almacenar password en texto plano | P0 |

### 2.2 IAM

| ID | Requisito | P |
|---|---|---|
| RF-IAM-001 | CRUD lógico de usuarios | P0 |
| RF-IAM-002 | Activar/desactivar usuarios | P0 |
| RF-IAM-003 | Asignar/revocar roles a usuarios | P0 |
| RF-IAM-004 | CRUD de roles | P0 |
| RF-IAM-005 | Catálogo de permisos atómicos | P0 |
| RF-IAM-006 | Asignar/revocar permisos a roles | P0 |
| RF-IAM-007 | Roles iniciales: ADMINISTRATOR, TEACHER, STUDENT | P0 |
| RF-IAM-008 | Deny by Default si falta permiso explícito | P0 |

### 2.3 Académico

| ID | Requisito | P |
|---|---|---|
| RF-STU-001 | Gestionar estudiantes (datos personales/académicos) | P0 |
| RF-TCH-001 | Gestionar docentes y perfil profesional | P0 |
| RF-CAR-001 | Gestionar carreras | P0 |
| RF-CUR-001 | Gestionar malla curricular por carrera/nivel | P0 |
| RF-SUB-001 | Gestionar asignaturas y prerrequisitos | P0 |
| RF-TRM-001 | Gestionar periodos (PLANNED/ACTIVE/CLOSED/CANCELLED) | P0 |
| RF-TRM-002 | Bloquear modificación académica de periodos CLOSED salvo operación autorizada+auditada | P0 |
| RF-CRS-001 | Gestionar paralelos/cursos (cupo, estado) | P0 |
| RF-ASN-001 | Crear teaching_assignments (docente-curso-periodo) | P0 |
| RF-ENR-001 | Matricular estudiante en curso | P0 |
| RF-ENR-002 | Cancelar/completar matrícula | P1 |
| RF-SCH-001 | Gestionar horarios y detectar conflictos | P1 |
| RF-ATT-001 | Registrar/editar asistencia solo si docente asignado | P0 |
| RF-ATT-002 | Consultar asistencia y calcular porcentaje | P1 |
| RF-EVL-001 | Definir evaluaciones con porcentajes; suma ≤ 100 | P0 |
| RF-GRD-001 | Registrar/modificar calificaciones con autorización contextual | P0 |
| RF-GRD-002 | Estudiante solo consulta sus calificaciones | P0 |
| RF-KAR-001 | Generar/consultar Kardex con estados académicos | P1 |
| RF-REP-001 | Generar reportes mínimos (HTML/CSV/JSON; PDF P2) | P1 |
| RF-REP-002 | Registrar log de cada reporte generado | P1 |
| RF-NTF-001 | Emisión de notificaciones tipificadas | P2 |
| RF-DSH-001 | Dashboard por rol | P1 |

### 2.4 Autorización / Zero Trust / IA

| ID | Requisito | P |
|---|---|---|
| RF-AZN-001 | Autorización = RBAC + permiso + ABAC contextual | P0 |
| RF-AZN-002 | Revalidar identidad/estado/rol/permiso/recurso/contexto en servidor | P0 |
| RF-AZN-003 | ADMIN no es omnipotente; requiere permission+policy+audit | P0 |
| RF-PAP-001 | Políticas versionadas en `policies/v1/` | P0 |
| RF-PDP-001 | PDP responde solo ALLOW/DENY + reason_code + policy_id | P0 |
| RF-GW-001 | Tool Gateway como PEP para tools de IA y ops sensibles | P0 |
| RF-AI-001 | IA solo interpreta NL y propone tools | P0 |
| RF-AI-002 | IA no ejecuta SQL ni accede a MySQL/credenciales | P0 |
| RF-AI-003 | Tool Registry con metadata de riesgo y permisos | P0 |
| RF-AI-004 | Tools iniciales de consulta + tools sensibles sujetos a DENY | P0 |
| RF-AI-005 | Sustituir CURRENT_USER por identidad autenticada | P0 |

### 2.5 Auditoría e historial

| ID | Requisito | P |
|---|---|---|
| RF-AUD-001 | Registrar audit_events en operaciones relevantes | P0 |
| RF-AUD-002 | Separar historial de usuario de auditoría técnica | P0 |
| RF-AUD-003 | Incluir request_id, actor, acción, recurso, status, ip | P0 |

---

## 3. Requisitos no funcionales

| ID | Requisito | P |
|---|---|---|
| RNF-SEC-001 | Cumplir controles OWASP Top 10 aplicables | P0 |
| RNF-SEC-002 | Secretos solo en entorno; `.env.example` sin secretos reales | P0 |
| RNF-SEC-003 | Principio Zero Trust: Never Trust, Always Verify | P0 |
| RNF-PERF-001 | Operaciones API locales p95 &lt; 500 ms en consultas simples (meta local) | P2 |
| RNF-REL-001 | Transacciones en update_grade y ops críticas | P0 |
| RNF-QUA-001 | Cobertura líneas ≥ 80%, ramas ≥ 70% | P0 |
| RNF-QUA-002 | PEP8, type hints, docstrings, SOLID/KISS/DRY | P0 |
| RNF-ARC-001 | Separación de capas; sin lógica de negocio en routes/HTML/JS/models | P0 |
| RNF-UX-001 | UI responsive Bootstrap 5+ | P1 |
| RNF-DEP-001 | Deploy inicial solo localhost/127.0.0.1 | P0 |
| RNF-TRA-001 | Trazabilidad Requirement → Story → Skill → Impl → Test → Audit | P0 |
| RNF-DB-001 | MySQL 8+ con FK, índices, soft delete académico | P0 |

---

## 4. Criterios de aceptación globales

1. Toda operación P0 tiene al menos un test asociado.  
2. Toda operación sensible deja evidencia de auditoría.  
3. Intentos no autorizados (incluye vía IA) terminan en DENY documentado.  
4. Ningún secreto en repositorio.  
5. Ningún endpoint crítico sin chequeo PDP/permiso.

---

## 5. Trazabilidad

| Spec | Uso |
|---|---|
| S04 | Casos de uso cubiertos por RF |
| S06 | Backlog priorizado desde RF |
| S07 | Historias derivadas |
| S12 | Métricas de cumplimiento |
