# S10 — Glosario

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fecha | 2026-09-20 |

| Término | Definición |
|---|---|
| SIGA | Sistema Integral de Gestión Académica |
| PolkDev | Metodología SPEC → SKILL → APP con fases y gates |
| Spec | Artefacto de especificación (S01–S12) |
| Skill | Capacidad registrada (K-xxx) responsable de una tarea |
| Gate | Punto de control humano entre fases |
| JWT | JSON Web Token; identifica sesión, no autoriza solo |
| Access Token | Token de corta duración para API |
| Refresh Token | Token para renovar access; revocable |
| RBAC | Control de acceso basado en roles |
| Permiso atómico | Acción granular `recurso.acción` (ej. `grades.update`) |
| ABAC | Control por atributos/contexto (asignación, ownership, periodo) |
| Deny by Default | Sin política ALLOW explícita → DENY |
| PAP | Policy Administration Point (gestión/versionado de políticas) |
| PDP | Policy Decision Point (decide ALLOW/DENY) |
| PEP | Policy Enforcement Point (Tool Gateway aplica la decisión) |
| Tool Registry | Catálogo de tools invocables por IA/sistema |
| Tool Gateway | Intermediario que valida, autoriza y ejecuta tools |
| Zero Trust | Never Trust, Always Verify en cada operación crítica |
| Teaching assignment | Relación docente–curso–periodo para ABAC |
| Paralelo / Course | Instancia de asignatura en un periodo |
| Periodo académico | Intervalo con estados PLANNED/ACTIVE/CLOSED/CANCELLED |
| Matrícula / Enrollment | Vínculo estudiante–curso–periodo |
| Kardex | Historial académico consolidado del estudiante |
| Auditoría | Evidencia técnica de seguridad de operaciones |
| Historial | Registro de acciones desde perspectiva de usuario (≠ auditoría) |
| Soft delete | Baja lógica conservando registro |
| IDOR | Insecure Direct Object Reference; acceso indebido por ID |
| CURRENT_USER | Marcador resuelto a identidad autenticada (nunca client-spoof) |
| XAMPP | Stack local que provee MySQL (no runtime PHP de la App) |
| Oleada | Bloque de entrega del backlog (O1…O6) |
| MVP | Conjunto P0 mínimo operable y seguro |
