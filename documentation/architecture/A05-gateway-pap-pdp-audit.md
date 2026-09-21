# A05 — Contratos Gateway · PAP · PDP · Audit

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F3 — Arquitectura |
| Skill | K-002 Architecture Designer |
| Spec | S05 RF-AZN/PAP/PDP/GW/AI/AUD · S09 ADR-004…007 |
| Fecha | 2026-09-20 |

---

## 1. PAP — Policy Administration Point

### Responsabilidades

```text
Crear / versionar / activar / desactivar / consultar políticas
```

### Store

```text
policies/v1/
  authentication.yaml
  students.yaml
  grades.yaml
  attendance.yaml
  reports.yaml
  ai.yaml
  enrollments.yaml
  terms.yaml
```

### Contrato de política (esquema lógico)

```yaml
policy_id: POL-GRADE-002
version: v1
module: grades
effect_default: DENY
rules:
  - id: R1
    effect: ALLOW
    actions: [grades.update]
    roles: [TEACHER]
    permissions: [grades.update]
    conditions:
      - teaching_assignment.exists
      - term.status == ACTIVE
```

### API interna PAP

| Operación | Descripción |
|---|---|
| `load_all()` | Carga YAML activos en memoria |
| `get(policy_id, version?)` | Obtiene política |
| `activate(policy_id, version)` | Marca versión activa + audit |
| `list()` | Inventario |

Las políticas **no** viven dispersas en controllers.

---

## 2. PDP — Policy Decision Point

### Entrada

```json
{
  "subject": {
    "user_id": 15,
    "roles": ["TEACHER"],
    "permissions": ["grades.update"],
    "status": "ACTIVE"
  },
  "action": "grades.update",
  "resource": {
    "type": "grade",
    "id": "100",
    "course_id": 5,
    "term_id": 3
  },
  "context": {
    "teacher_id": 10,
    "teaching_assignment_exists": true,
    "term_status": "ACTIVE",
    "request_id": "UUID"
  }
}
```

### Salida

```json
{
  "decision": "ALLOW",
  "reason_code": "POLICY_MATCH",
  "policy_id": "POL-GRADE-002",
  "policy_version": "v1"
}
```

o

```json
{
  "decision": "DENY",
  "reason_code": "ROLE_NOT_ALLOWED",
  "policy_id": "POL-GRADE-002",
  "policy_version": "v1"
}
```

### Regla absoluta

```text
DENY BY DEFAULT
Si ninguna regla ALLOW aplica → DENY
```

### reason_code iniciales

| Código | Uso |
|---|---|
| `POLICY_MATCH` | ALLOW |
| `ROLE_NOT_ALLOWED` | Rol no habilitado |
| `PERMISSION_MISSING` | Falta permiso atómico |
| `CONTEXT_MISMATCH` | Sin assignment / ownership |
| `TERM_CLOSED` | Periodo cerrado |
| `USER_INACTIVE` | Usuario no ACTIVE |
| `RESOURCE_NOT_OWNED` | IDOR / recurso ajeno |
| `TOOL_NOT_ALLOWED` | Tool sensible denegado |
| `DEFAULT_DENY` | Sin match |

---

## 3. Tool Gateway (PEP)

### Pipeline

```text
Tool Proposal
 → Schema Validation
 → Tool Registry lookup
 → Identity Resolution (CURRENT_USER)
 → Context Resolution
 → PDP.evaluate
 → ALLOW: execute handler + audit
 → DENY: audit/security + return
```

### Tools iniciales (Registry)

| tool_name | risk | roles típicos | permission |
|---|---|---|---|
| `get_student_profile` | LOW | STUDENT/ADMIN | `students.view` |
| `get_grades` | LOW | STUDENT/TEACHER/ADMIN | `grades.view` |
| `get_attendance` | LOW | STUDENT/TEACHER/ADMIN | `attendance.view` |
| `get_kardex` | LOW | STUDENT/ADMIN | `kardex.view` |
| `get_schedule` | LOW | ALL auth | `schedules.view` |
| `generate_report` | MED | ADMIN/TEACHER | `reports.generate` |
| `update_grade` | HIGH | TEACHER | `grades.update` |
| `update_attendance` | HIGH | TEACHER | `attendance.update` |
| `create_enrollment` | HIGH | ADMIN | `enrollments.create` |
| `cancel_enrollment` | HIGH | ADMIN | `enrollments.cancel` |

### Metadata obligatoria por tool

```text
tool_name, description, method, endpoint, parameters,
required_permissions, allowed_roles, resource_type, risk_level
```

---

## 4. Audit / Security

### audit_events (operación de negocio)

Campos mínimos PromptMaster §33:

```text
id, request_id, user_id, role, action, module, resource,
resource_id, old_value, new_value, ip, user_agent,
timestamp, status, reason
```

### security_events (señales de seguridad)

```text
LOGIN_FAILURE, ACCESS_DENY, TOOL_DENY, IDOR_ATTEMPT,
PRIVILEGE_ESCALATION_ATTEMPT, TERM_CLOSED_WRITE_ATTEMPT
```

### Separación

| Concepto | Pregunta que responde |
|---|---|
| Historial | ¿Qué hizo el usuario en la app? |
| Auditoría | ¿Qué evidencia técnica de seguridad existe? |

---

## 5. Integración con capas de aplicación

```text
Router
  → Service
      → (opcional) Permission pre-check
      → PDP.evaluate  (obligatorio en ops sensibles)
      → Repository (solo si ALLOW)
      → AuditService
```

Para tools IA:

```text
AIService → Gateway → PDP → Handler → Audit
```

Nunca:

```text
AI → Repository/MySQL
Router → Repository (saltando service/PDP en ops sensibles)
```

---

## 6. Matriz de decisión de ejemplo

| Subject | Action | Context | Decision |
|---|---|---|---|
| TEACHER + grades.update + assignment | update_grade | term ACTIVE | ALLOW |
| TEACHER + grades.update + sin assignment | update_grade | — | DENY CONTEXT_MISMATCH |
| STUDENT | update_grade | — | DENY ROLE_NOT_ALLOWED |
| STUDENT | get_grades propio | CURRENT_USER | ALLOW |
| STUDENT | get_grades otro id | spoof | DENY RESOURCE_NOT_OWNED |
| ADMIN sin permission audit.view | audit.export | — | DENY PERMISSION_MISSING |

---

## 7. Criterios de aceptación arquitectura (Gate F3)

- [ ] C4 L1–L3 documentados (A01)
- [ ] ERD cubre entidades mínimas PromptMaster (A02)
- [ ] Secuencias AUTH, GRD, AI, ATTACK (A03)
- [ ] Deployment localhost (A04)
- [ ] Contratos PAP/PDP/Gateway/Audit (A05)
- [ ] S03 actualizado con referencias F3
