# CHANGELOG — Sistema de Gestión Académica

## [1.1.0] — 2026-10-07

### Seeder masivo + visibilidad de periodos + chatbot flotante
| Acción | Spec | Skill |
| --- | --- | --- |
| Seeder 3 carreras, 30 docentes, 420 estudiantes, 4 periodos, 2520 notas | SPEC-004, SPEC-007 | SKILL-003, SKILL-004 |
| Periodos múltiples habilitados; filtro para STUDENT/TEACHER | SPEC-003, SPEC-004 | SKILL-007 |
| Chatbot flotante DeepSeek en UI | SPEC-005, SPEC-006 | SKILL-005, SKILL-006 |

## [1.0.0] — 2026-10-07

### Creación inicial del sistema (Spec as Skill)

| Acción | Spec | Skill |
| --- | --- | --- |
| Estructura Flask MVC + Blueprints + JWT | SPEC-001 | SKILL-001 |
| OWASP Top 10 2025: cabeceras, rate limit, bcrypt, auditoría | SPEC-002 | SKILL-002 |
| Modelos SQLAlchemy + seeds roles/permisos/admin | SPEC-007 | SKILL-003 |
| Roles granulares y decoradores de autorización | SPEC-003 | SKILL-007 |
| Módulos académicos, notas, asistencia, matrículas | SPEC-004 | SKILL-004 |
| Impersonación con banner y return-to-admin | SPEC-008 | SKILL-004 |
| Integración DeepSeek + config cifrada AES | SPEC-005 | SKILL-005 |
| UI Bootstrap/temas claro-oscuro/sidebar/dashboard | SPEC-006 | SKILL-006 |
| Kárdex PDF, reportes Excel, notificaciones, auditoría | SPEC-004 | SKILL-004 |
