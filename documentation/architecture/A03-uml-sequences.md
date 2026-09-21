# A03 — UML de dominio y diagramas de secuencia

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F3 — Arquitectura |
| Skill | K-002 Architecture Designer |
| Spec | S04, S05, S07, S09 |
| Fecha | 2026-09-20 |

---

## 1. UML — Dominio IAM + autorización

```mermaid
classDiagram
  class User {
    +id: int
    +username: str
    +email: str
    +password_hash: str
    +status: str
    +is_active() bool
  }

  class Role {
    +id: int
    +code: str
    +name: str
  }

  class Permission {
    +id: int
    +code: str
    +module: str
  }

  class Policy {
    +policy_id: str
    +version: str
    +module: str
  }

  class AccessRequest {
    +subject: User
    +action: str
    +resource_type: str
    +resource_id: str
    +context: dict
  }

  class Decision {
    +decision: ALLOW|DENY
    +reason_code: str
    +policy_id: str
    +policy_version: str
  }

  class PDP {
    +evaluate(AccessRequest) Decision
  }

  class PAP {
    +load_active_policies()
    +activate(version)
  }

  User "1" --> "*" Role : user_roles
  Role "1" --> "*" Permission : role_permissions
  PDP --> PAP : reads
  PDP --> Decision : returns
  PDP --> AccessRequest : evaluates
  PAP --> Policy : manages
```

---

## 2. UML — Dominio académico (núcleo)

```mermaid
classDiagram
  class Student
  class Teacher
  class Career
  class Subject
  class AcademicTerm
  class Course
  class TeachingAssignment
  class Enrollment
  class Evaluation
  class Grade
  class AttendanceRecord
  class KardexEntry

  User <|-- Student : profile
  User <|-- Teacher : profile
  Career "1" --> "*" Student
  Subject "1" --> "*" Course
  AcademicTerm "1" --> "*" Course
  Teacher "1" --> "*" TeachingAssignment
  Course "1" --> "*" TeachingAssignment
  Student "1" --> "*" Enrollment
  Course "1" --> "*" Enrollment
  Course "1" --> "*" Evaluation
  Evaluation "1" --> "*" Grade
  Student "1" --> "*" Grade
  Student "1" --> "*" AttendanceRecord
  Student "1" --> "*" KardexEntry

  class TeachingAssignment {
    +teacher_id
    +course_id
    +term_id
    +is_active() bool
  }

  class Grade {
    +score: Decimal
    +graded_by_teacher_id
  }
```

---

## 3. SEQ-AUTH — Login + emisión JWT

```mermaid
sequenceDiagram
  actor U as Usuario
  participant FE as Frontend
  participant API as AuthRouter
  participant S as AuthService
  participant R as UserRepository
  participant A as AuditService
  participant DB as MySQL

  U->>FE: Credenciales
  FE->>API: POST /auth/login
  API->>S: login(username, password)
  S->>R: get_by_username()
  R->>DB: SELECT user
  DB-->>R: row
  alt usuario ACTIVE y password OK
    S->>S: emit access + refresh
    S->>DB: store session/refresh_hash
    S->>A: audit LOGIN SUCCESS
    S-->>API: tokens
    API-->>FE: 200 + tokens
  else fallo
    S->>A: audit LOGIN FAILURE
    API-->>FE: 401
  end
```

---

## 4. SEQ-GRD — update_grade (ALLOW docente asignado)

```mermaid
sequenceDiagram
  actor T as Docente
  participant FE as Frontend
  participant API as GradesRouter
  participant SVC as GradeService
  participant PDP as PDP
  participant REP as GradeRepository
  participant AUD as AuditService
  participant DB as MySQL

  T->>FE: Guardar nota
  FE->>API: PUT /grades/{id} + JWT
  API->>SVC: update_grade(cmd, identity)
  SVC->>SVC: revalidate user status + role + permission grades.update
  SVC->>PDP: evaluate(teacher, update_grade, grade, context)
  Note over PDP: context incluye teaching_assignment EXISTS
  PDP-->>SVC: ALLOW + policy_id
  SVC->>DB: BEGIN
  SVC->>REP: update score
  SVC->>AUD: UPDATE_GRADE SUCCESS
  SVC->>DB: COMMIT
  SVC-->>API: GradeDTO
  API-->>FE: 200
```

---

## 5. SEQ-GRD-DENY — estudiante intenta modificar nota

```mermaid
sequenceDiagram
  actor S as Estudiante
  participant API as GradesRouter
  participant SVC as GradeService
  participant PDP as PDP
  participant AUD as AuditService

  S->>API: PUT /grades/{id}
  API->>SVC: update_grade(...)
  SVC->>PDP: evaluate(...)
  PDP-->>SVC: DENY ROLE_NOT_ALLOWED
  SVC->>AUD: SECURITY DENY
  SVC-->>API: 403
  API-->>S: error + reason_code
```

---

## 6. SEQ-AI — Tool proposal → Gateway → PDP

```mermaid
sequenceDiagram
  actor U as Estudiante
  participant FE as Frontend
  participant AI as AIService
  participant LLM as LLM Provider
  participant GW as ToolGateway
  participant REG as ToolRegistry
  participant PDP as PDP
  participant H as ToolHandler
  participant AUD as AuditService
  participant DB as MySQL

  U->>FE: "¿Cuáles son mis calificaciones?"
  FE->>AI: POST /ai/chat + JWT
  AI->>LLM: prompt + tool schemas
  LLM-->>AI: proposal get_grades(student_id=CURRENT_USER)
  AI->>GW: invoke(proposal, identity)
  GW->>GW: schema validate
  GW->>REG: lookup get_grades
  GW->>GW: resolve CURRENT_USER → identity.student_id
  GW->>PDP: evaluate(get_grades, context)
  alt ALLOW
    PDP-->>GW: ALLOW
    GW->>H: execute
    H->>DB: read grades (scoped)
    H-->>GW: data
    GW->>AUD: TOOL SUCCESS
    GW-->>AI: result
    AI-->>FE: respuesta NL + datos
  else DENY
    PDP-->>GW: DENY
    GW->>AUD: TOOL DENY
    GW-->>AI: denied
    AI-->>FE: no autorizado
  end
```

---

## 7. SEQ-AI-ATTACK — “Cambia mi nota a 100”

```mermaid
sequenceDiagram
  actor S as Estudiante
  participant AI as AIService
  participant GW as ToolGateway
  participant PDP as PDP
  participant AUD as AuditService

  S->>AI: "Cambia mi nota a 100"
  AI-->>AI: proposal update_grade
  AI->>GW: invoke(update_grade, ...)
  GW->>PDP: evaluate
  PDP-->>GW: DENY ROLE_NOT_ALLOWED / POLICY
  GW->>AUD: security_event + tool_invocation DENY
  GW-->>AI: DENY
  Note over AI,S: No escritura en BD
```

---

## 8. SEQ-CLOSED-TERM — intento de editar periodo CLOSED

```mermaid
sequenceDiagram
  actor A as Admin
  participant SVC as AcademicService
  participant PDP as PDP
  participant AUD as Audit

  A->>SVC: modify grade on CLOSED term
  SVC->>SVC: term.status == CLOSED?
  alt operación especial autorizada
    SVC->>PDP: evaluate special_override
    PDP-->>SVC: ALLOW|DENY
  else flujo normal
    SVC-->>A: 409 / 403 TERM_CLOSED
    SVC->>AUD: DENY TERM_CLOSED
  end
```

---

## 9. Contratos de secuencia → requisitos

| Diagrama | RF / HU |
|---|---|
| SEQ-AUTH | RF-AUTH-001…004 · HU-AUTH-001/002 |
| SEQ-GRD | RF-GRD-001 · HU-GRD-001 |
| SEQ-GRD-DENY | RF-GRD-002 · HU-GRD-002 |
| SEQ-AI | RF-AI-001…005 · HU-AI-001 |
| SEQ-AI-ATTACK | RF-AI-002 · HU-AI-002 |
| SEQ-CLOSED-TERM | RF-TRM-002 |
