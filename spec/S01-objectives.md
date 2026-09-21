# S01 — Objetivos

| Campo | Valor |
|---|---|
| Proyecto | SIGA — Sistema Integral de Gestión Académica (`siga-polkdev`) |
| Fase | F1 — Planificación |
| Skill | K-012 Planner |
| Estado | ⏳ Pendiente de Gate F1 |
| Fuente | `prompt_master.md` §§2–3, §87 |
| Fecha | 2026-09-20 |

---

## 1. Objetivo general

Construir una plataforma web modular para gestionar integralmente la información académica de una institución de educación superior, aplicando arquitectura segura, control granular de acceso (RBAC + permisos + ABAC), trazabilidad, auditoría, automatización e inteligencia artificial bajo principios Zero Trust y metodología PolkDev (`SPEC → SKILL → APP`).

---

## 2. Objetivos específicos

| ID | Objetivo | Criterio de éxito |
|---|---|---|
| OG-01 | Centralizar la información académica | Un solo sistema de registro para estudiantes, docentes, carreras, cursos, matrículas, notas y asistencia |
| OG-02 | Administrar usuarios | CRUD de usuarios con estados, historial y sin contraseñas en texto plano |
| OG-03 | Administrar roles | Roles base ADMINISTRATOR, TEACHER, STUDENT; extensibles por especificación |
| OG-04 | Administrar permisos granulares | Permisos atómicos (`recurso.acción`); Deny by Default |
| OG-05 | Gestionar estudiantes | Alta, consulta, actualización y relación con matrículas/kardex |
| OG-06 | Gestionar docentes | Alta, consulta, actualización y asignaciones a cursos |
| OG-07 | Gestionar carreras | Catálogo de carreras vinculadas a malla curricular |
| OG-08 | Gestionar asignaturas | Catálogo de asignaturas vinculadas a malla y periodos |
| OG-09 | Gestionar periodos académicos | Apertura, operación y cierre controlado de periodos |
| OG-10 | Gestionar matrículas | Inscripción, actualización y cancelación con autorización |
| OG-11 | Gestionar paralelos / cursos | Paralelos por asignatura-periodo con docente asignado |
| OG-12 | Gestionar horarios | Consulta y gestión de horarios por rol |
| OG-13 | Registrar asistencia | Registro y consulta con control contextual |
| OG-14 | Registrar calificaciones | Creación/actualización solo por docente asignado + política |
| OG-15 | Gestionar evaluaciones | Definición y aplicación de evaluaciones por curso |
| OG-16 | Construir Kardex / historial académico | Vista consolidada del recorrido académico del estudiante |
| OG-17 | Generar reportes | Reportes académicos y administrativos con permisos de exportación |
| OG-18 | Registrar auditoría | Eventos técnicos de seguridad con request_id, actor, recurso y resultado |
| OG-19 | Integrar IA educativa | Asistente vía Tool Registry + Tool Gateway; sin acceso directo a MySQL |
| OG-20 | Aplicar autorización contextual | PDP evalúa rol + permiso + atributos + contexto antes de ALLOW |
| OG-21 | Proteger operaciones sensibles | Gateway obligatorio; revalidación servidor; auditoría |
| OG-22 | Mantener trazabilidad completa | Spec ↔ Skill ↔ Implementation ↔ Test ↔ Audit |
| OG-23 | Permitir crecimiento modular | Arquitectura por capas y módulos independientes |

---

## 3. Objetivos no funcionales

| ID | Objetivo | Meta |
|---|---|---|
| ONF-01 | Seguridad | JWT + revalidación servidor; OWASP Top 10; Zero Trust |
| ONF-02 | Autorización | RBAC + permisos granulares + ABAC; Deny by Default |
| ONF-03 | Calidad de código | PEP8, type hints, SOLID, separación de capas |
| ONF-04 | Pruebas | Unit, Integration, Security, E2E; cobertura líneas ≥ 80%, ramas ≥ 70% |
| ONF-05 | Secretos | Ningún secreto en código; `.env` + `.env.example` |
| ONF-06 | Despliegue inicial | Solo localhost / 127.0.0.1 sin autorización explícita de publicación |
| ONF-07 | Mantenibilidad | Cambios incrementales anclados a Spec + Skill + Fase |
| ONF-08 | Usabilidad | UI administrativa responsive (HTML/CSS/JS + Bootstrap 5+) |

---

## 4. Resultado esperado (visión)

SIGA operativo en entorno local con:

- autenticación JWT (access + refresh);
- autorización RBAC/ABAC vía PAP/PDP;
- módulos académicos mínimos definidos en PromptMaster;
- Tool Gateway + Tool Registry + IA sin bypass de políticas;
- auditoría e historial diferenciados;
- evidencia de pruebas y documentación alineada a PolkDev.

---

## 5. Trazabilidad

| Artefacto | Relación |
|---|---|
| PromptMaster §3 | Fuente de objetivos |
| S02 | Delimita qué objetivos entran en alcance por fase |
| S08 | Secuencia temporal para alcanzar los objetivos |
| F2 (S03–S12) | Detalle de requisitos, backlog e historias |
| Gate F1 | Validación humana de este plan |

---

## 6. Regla PolkDev

```text
NINGÚN CÓDIGO SIN SPEC.
NINGUNA IMPLEMENTACIÓN SIN SKILL.
NINGUNA FASE SIN GATE.
```
