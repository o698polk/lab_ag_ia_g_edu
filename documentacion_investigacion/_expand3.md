
## 2.15 Tabla conceptual de controles versus principios Zero Trust

| Principio (lectura de Rose et al., 2020) | Control en el laboratorio | Cobertura |
| --- | --- | --- |
| Autenticar y autorizar siempre | JWT + `has_permission` + decorator + executor | Parcial-alta en app |
| No confiar en red/localidad | App local sin asumir VPN como autorización | Parcial (lab single-host) |
| Políticas basadas en atributos/identidad | Roles, permisos, ownership de cursos | Parcial (sin motor ABAC externo) |
| Observabilidad | AuditLog + AIAgentLog | Media |
| Segmentación | No implementada a nivel red | Ausente |
| PDP central | No | Ausente |
| PEP | API decorators + Tool Gateway executor | Presente (app-level) |

Syed et al. (2022) y Buck et al. (2021) sostienen que la madurez es gradual; la tabla evita el todo-o-nada. Kang et al. (2023), Azad et al. (2024) y Deng et al. (2025) añaden la fila implícita “defensa del plano cognitivo del LLM”, cubierta por injection/intent guards. Jeong y Yang (2025) y Xu et al. (2025) enfatizan privacidad operacional (secretos, minimización), cubierta parcialmente por AES y scoping. Adahman et al. (2022), Awan et al. (2023), Vasović et al. (2026), Mawgoud et al. (2025), Kanaker et al. (2026), Gulyamov et al. (2026) y Geng et al. (2026) justifican por qué una fila vacía de segmentación no invalida el valor educativo del resto.

## 2.16 Amenazas STRIDE ligeras al canal del agente

Siguiendo el espíritu de Shostack (2014), sin pretender un modelo completo certificado:

- **Spoofing:** intentar hacerse pasar por otro rol vía prompt; mitigado por JWT real y detección de escalada narrativa.
- **Tampering:** mutaciones de notas; mitigado por permisos, confirmación, grades_closed, ownership.
- **Repudiation:** negación de acciones; mitigado por AuditLog/LogIA (no es no-repudio criptográfico forte).
- **Information disclosure:** listados institucionales; mitigado por intent guard, permisos, visibility.
- **Denial of service:** flood al chat; mitigado parcialmente por Flask-Limiter (relajable en inseguro).
- **Elevation of privilege:** `users_assign_roles` o elevación; mitigado por permisos; elevación formal parcial.

## 4.39 Ciclo de vida de un mensaje bloqueado por injection

1. Usuario autenticado envía mensaje con patrones de jailbreak/injection.
2. `scan_prompt_injection` retorna dict con `kind` y `matched`.
3. Orquestador construye reply formal de bloqueo.
4. Persiste mensaje assistant.
5. `log_security_block` escribe LogIA `prompt_injection` y `policy_block`, más auditoría.
6. Retorna respuesta con `blocked=True` sin llamar al LLM.

En IA con inseguro, el paso 2 retorna `None` y el flujo continúa hacia el LLM. Esta bifurcación es el corazón empírico del escenario A.

## 4.40 Ciclo de vida de un mensaje bloqueado por intent

1. Mensaje coincide con patrón de directorio institucional u otra regla.
2. Usuario carece de permisos requeridos.
3. No aplica excepción de ámbito propio (IB) o equivalentes.
4. Se registra `privilege_block` / `AI_PRIVILEGE_BLOCK`.
5. No hay tool calls.

Este ciclo muestra que el laboratorio no espera únicamente a que el executor deniegue una tool: deniega antes, ahorrando llamada al modelo y reduciendo fuga semántica.

## 4.41 Ciclo de vida de tool desconocida

Si el modelo inventa `delete_all_students`, el executor responde `unknown_tool: True` y registra bloqueo (modo seguro). Allowlist estricta.

## 4.42 Kárdex y restricciones de perfil

`system_api` documenta que ciertos perfiles no usan módulo kárdex (`_kardex_forbidden_for_profile`). Roles staff pueden generar kárdex PDF. Esto refuerza que no todo permiso de lectura académica implica acceso a todos los módulos de reporting institucional.

## 4.43 Notificaciones y elevación parcial

Aunque `privileges_request_elevation` no está en HANDLERS, su código crea `Notification(role_code="ADMIN", ...)`. Ello indica la intención de diseño de un workflow humano de aprobación. El trabajo futuro consiste en exponer la tool y construir UI de resolución (`status`, `resolved_by`, `resolution_note` ya modelados en `ElevationRequest`).

## 4.44 Consideraciones de concurrencia y consistencia

Las mutaciones hacen `db.session.commit()` por operación de tool. No se observa un saga complejo multi-tool atómico más allá de la transacción de cada handler. Mawgoud et al. (2025) invitan a pensar resiliencia; el lab prioriza claridad sobre sofisticación distribuida.

## 4.45 Internacionalización y validación de entradas

Mensajes de error de tools están en español. Validaciones de notas rechazan fuera de [1,10]. Estados de asistencia se validan por pertenencia a un conjunto cerrado. Fechas de asistencia se parsean `%Y-%m-%d`. Estas validaciones reducen entradas basura del modelo.

## 5.24 Rúbrica propuesta para evaluación docente del laboratorio (sin datos de aplicación)

| Criterio | Evidencia esperada | Nivel |
| --- | --- | --- |
| Explica RBAC | Cita roles/seed | Conceptual |
| Explica gateway | Cita executor/handlers | Técnico |
| Contrasta IA/IB | Cita insecure vs intent_guard | Analítico |
| Identifica parcialidades | Elevación, Spec ausente, no PDP | Crítico |
| Ejecuta smoke local | Salidas de scripts en su entorno | Práctico |

Esta rúbrica no reporta resultados de cohortes; solo orienta uso académico.

## 5.25 Qué no debe concluirse a partir de los scripts

No debe concluirse que el sistema es seguro ante atacantes adaptativos. No debe concluirse equivalencia a NIST SP 800-207 completo. No debe concluirse que IB es “mejor” estadísticamente que IA. Sí puede concluirse que existen mecanismos distintos y que el código permite contrastarlos.

## 6.14 Mensaje final de conformidad empírica

Todas las secciones técnicas de este informe pueden, en principio, ser auditadas abriendo los paths citados bajo `D:\PROYECTOS\lab_ag_ia_g_edu`. Si un elemento no aparece en disco, no aparece como implementado en el texto. Esa regla, más que cualquier adorno retórico, define la calidad científica de la entrega.
