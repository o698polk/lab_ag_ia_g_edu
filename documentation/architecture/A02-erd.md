# A02 — ERD (Entity Relationship Diagram)

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F3 — Arquitectura |
| Skill | K-002 Architecture Designer |
| Spec | S03 §7, PromptMaster §45–46 |
| Fecha | 2026-09-20 |

---

## 1. Convenciones

| Convención | Valor |
|---|---|
| PK | `id` BIGINT AUTO_INCREMENT salvo tablas puente |
| Timestamps | `created_at`, `updated_at` |
| Soft delete | `deleted_at` NULL en entidades académicas/IAM críticas |
| Status | ENUM / VARCHAR controlado por Spec |
| Nombres | snake_case plural |

---

## 2. ERD — IAM y sesiones

```mermaid
erDiagram
  USERS ||--o{ USER_ROLES : has
  ROLES ||--o{ USER_ROLES : grants
  ROLES ||--o{ ROLE_PERMISSIONS : has
  PERMISSIONS ||--o{ ROLE_PERMISSIONS : granted_by
  USERS ||--o{ SESSIONS : opens
  USERS ||--o{ REFRESH_TOKENS : owns

  USERS {
    bigint id PK
    string username UK
    string email UK
    string password_hash
    string status
    datetime last_login
    datetime deleted_at
    datetime created_at
    datetime updated_at
  }

  ROLES {
    bigint id PK
    string code UK
    string name
    bool is_active
    datetime created_at
  }

  PERMISSIONS {
    bigint id PK
    string code UK
    string description
    string module
  }

  USER_ROLES {
    bigint user_id FK
    bigint role_id FK
  }

  ROLE_PERMISSIONS {
    bigint role_id FK
    bigint permission_id FK
  }

  SESSIONS {
    bigint id PK
    bigint user_id FK
    string session_id UK
    datetime expires_at
    string ip
    string user_agent
  }

  REFRESH_TOKENS {
    bigint id PK
    bigint user_id FK
    string token_hash UK
    datetime expires_at
    bool revoked
  }
```

---

## 3. ERD — Personas académicas y catálogo

```mermaid
erDiagram
  USERS ||--o| STUDENTS : profile
  USERS ||--o| TEACHERS : profile
  CAREERS ||--o{ STUDENTS : enrolled_in
  CAREERS ||--o{ CURRICULUM : has
  CURRICULUM ||--o{ CURRICULUM_SUBJECTS : contains
  SUBJECTS ||--o{ CURRICULUM_SUBJECTS : listed
  SUBJECTS ||--o{ SUBJECT_PREREQUISITES : requires
  SUBJECTS ||--o{ SUBJECT_PREREQUISITES : required_by

  STUDENTS {
    bigint id PK
    bigint user_id FK_UK
    string student_code UK
    bigint career_id FK
    string level
    date admission_date
    string status
    datetime deleted_at
  }

  TEACHERS {
    bigint id PK
    bigint user_id FK_UK
    string teacher_code UK
    string specialty
    string status
    datetime deleted_at
  }

  CAREERS {
    bigint id PK
    string code UK
    string name
    string modality
    int duration_semesters
    string status
  }

  CURRICULUM {
    bigint id PK
    bigint career_id FK
    string version
    string status
  }

  CURRICULUM_SUBJECTS {
    bigint id PK
    bigint curriculum_id FK
    bigint subject_id FK
    int level
    int semester
    decimal credits
  }

  SUBJECTS {
    bigint id PK
    string code UK
    string name
    text description
    decimal credits
    int hours
    string type
    string status
  }

  SUBJECT_PREREQUISITES {
    bigint subject_id FK
    bigint prerequisite_subject_id FK
  }
```

---

## 4. ERD — Operación académica

```mermaid
erDiagram
  ACADEMIC_TERMS ||--o{ COURSES : offers
  SUBJECTS ||--o{ COURSES : instantiated_as
  COURSES ||--o{ TEACHING_ASSIGNMENTS : assigned
  TEACHERS ||--o{ TEACHING_ASSIGNMENTS : teaches
  COURSES ||--o{ ENROLLMENTS : has
  STUDENTS ||--o{ ENROLLMENTS : registers
  COURSES ||--o{ SCHEDULES : scheduled
  CLASSROOMS ||--o{ SCHEDULES : hosts

  ACADEMIC_TERMS {
    bigint id PK
    string code UK
    string name
    date start_date
    date end_date
    string status
    bool is_current
  }

  COURSES {
    bigint id PK
    bigint subject_id FK
    bigint term_id FK
    string parallel_code
    int capacity
    string status
  }

  TEACHING_ASSIGNMENTS {
    bigint id PK
    bigint teacher_id FK
    bigint course_id FK
    bigint term_id FK
    string status
  }

  ENROLLMENTS {
    bigint id PK
    bigint student_id FK
    bigint course_id FK
    bigint term_id FK
    datetime enrolled_at
    string status
  }

  CLASSROOMS {
    bigint id PK
    string code UK
    string name
    int capacity
  }

  SCHEDULES {
    bigint id PK
    bigint course_id FK
    bigint teacher_id FK
    bigint classroom_id FK
    bigint term_id FK
    string day_of_week
    time start_time
    time end_time
  }
```

**ABAC clave:** `TEACHING_ASSIGNMENTS(teacher_id, course_id, term_id)` debe existir para writes de asistencia/notas.

---

## 5. ERD — Asistencia, evaluaciones, notas, kardex

```mermaid
erDiagram
  COURSES ||--o{ ATTENDANCE_SESSIONS : holds
  ATTENDANCE_SESSIONS ||--o{ ATTENDANCE_RECORDS : includes
  STUDENTS ||--o{ ATTENDANCE_RECORDS : marked
  COURSES ||--o{ EVALUATIONS : defines
  EVALUATION_TYPES ||--o{ EVALUATIONS : typed
  EVALUATIONS ||--o{ GRADES : scored
  STUDENTS ||--o{ GRADES : receives
  STUDENTS ||--o{ KARDEX_ENTRIES : history
  SUBJECTS ||--o{ KARDEX_ENTRIES : subject

  ATTENDANCE_SESSIONS {
    bigint id PK
    bigint course_id FK
    date session_date
    string topic
  }

  ATTENDANCE_RECORDS {
    bigint id PK
    bigint session_id FK
    bigint student_id FK
    string status
    string notes
  }

  EVALUATION_TYPES {
    bigint id PK
    string code UK
    string name
  }

  EVALUATIONS {
    bigint id PK
    bigint course_id FK
    bigint evaluation_type_id FK
    string name
    decimal weight_percent
    date due_date
    string status
  }

  GRADES {
    bigint id PK
    bigint evaluation_id FK
    bigint student_id FK
    decimal score
    string comment
    bigint graded_by_teacher_id FK
    datetime graded_at
  }

  KARDEX_ENTRIES {
    bigint id PK
    bigint student_id FK
    bigint term_id FK
    bigint subject_id FK
    bigint course_id FK
    decimal final_grade
    string academic_status
    decimal credits
  }
```

**Regla evaluaciones:** `SUM(weight_percent) WHERE course_id = X AND status active <= 100`.

**Estados kardex:** APPROVED | FAILED | IN_PROGRESS | WITHDRAWN.

---

## 6. ERD — Plataforma, IA, políticas, auditoría

```mermaid
erDiagram
  USERS ||--o{ NOTIFICATIONS : receives
  USERS ||--o{ REPORT_LOGS : generates
  USERS ||--o{ AUDIT_EVENTS : actor
  USERS ||--o{ SECURITY_EVENTS : actor
  USERS ||--o{ AI_CONVERSATIONS : starts
  AI_CONVERSATIONS ||--o{ AI_MESSAGES : contains
  AI_MESSAGES ||--o{ TOOL_INVOCATIONS : may_trigger
  TOOL_REGISTRY ||--o{ TOOL_INVOCATIONS : defines
  POLICIES ||--o{ POLICY_VERSIONS : versions
  POLICY_VERSIONS ||--o{ POLICY_DECISIONS : applied

  NOTIFICATIONS {
    bigint id PK
    bigint user_id FK
    string type
    string title
    text body
    bool read_flag
  }

  REPORT_LOGS {
    bigint id PK
    bigint user_id FK
    string report_type
    json parameters
    string result_status
    datetime created_at
  }

  AUDIT_EVENTS {
    bigint id PK
    string request_id
    bigint user_id FK
    string role
    string action
    string module
    string resource
    string resource_id
    json old_value
    json new_value
    string ip
    string user_agent
    string status
    string reason
    datetime timestamp
  }

  SECURITY_EVENTS {
    bigint id PK
    string request_id
    bigint user_id FK
    string event_type
    string severity
    json details
    datetime timestamp
  }

  AI_CONVERSATIONS {
    bigint id PK
    bigint user_id FK
    datetime started_at
  }

  AI_MESSAGES {
    bigint id PK
    bigint conversation_id FK
    string role
    text content
    datetime created_at
  }

  TOOL_REGISTRY {
    bigint id PK
    string tool_name UK
    string description
    string method
    string endpoint
    json parameters_schema
    string required_permissions
    string allowed_roles
    string resource_type
    string risk_level
    bool is_active
  }

  TOOL_INVOCATIONS {
    bigint id PK
    bigint tool_id FK
    bigint user_id FK
    bigint message_id FK
    json parameters
    string decision
    string reason_code
    string status
    datetime created_at
  }

  POLICIES {
    bigint id PK
    string policy_id UK
    string name
    string module
  }

  POLICY_VERSIONS {
    bigint id PK
    bigint policy_id FK
    string version
    string file_path
    bool is_active
    datetime activated_at
  }

  POLICY_DECISIONS {
    bigint id PK
    bigint policy_version_id FK
    string request_id
    string decision
    string reason_code
    json context
    datetime created_at
  }
```

---

## 7. Integridad y restricciones

| Regla | Aplicación |
|---|---|
| FK ON DELETE RESTRICT | Datos académicos críticos |
| UNIQUE (course_id, parallel) por term | Evitar duplicados |
| UNIQUE (student_id, course_id, term_id) enrollment ACTIVE | Una matrícula activa |
| UNIQUE (teacher_id, course_id, term_id) assignment | Asignación única |
| CHECK weight_percent > 0 | Evaluaciones |
| Indexes | user_id, course_id, term_id, request_id, tool_name |

---

## 8. Notas de implementación (F5/F6)

- Migraciones Alembic por oleada (O1 IAM → O2 catálogo → …).
- Seed: roles, permisos base, policies v1, tools iniciales.
- Soft delete: repositorios filtran `deleted_at IS NULL` por defecto.
