# Políticas y controles de seguridad del Agente IA

Documento de análisis del estado **actual** del Sistema de Gestión Académica respecto a la seguridad del asistente de inteligencia artificial: reglas, permisos, controles ante *prompt injection* / *jailbreak*, principios de **Zero Trust** y **mínimo privilegio**, y limitaciones conocidas.

| Campo | Valor |
| --- | --- |
| Versión del documento | 1.0 |
| Fecha | 2026-10-11 |
| Metodología | Spec as Skill (SPEC-002, SPEC-003, SPEC-009, SPEC-016, SPEC-021, SPEC-023, SPEC-026, SPEC-027) |
| Complementa | `permisos_role.md`, `PROMPTSMASTER — Sistema de Gestión Académica.md` |

---

## 1. Resumen ejecutivo

El agente IA **no ejecuta acciones solo porque el modelo lo pida**. Toda operación sensible pasa por capas de control en el servidor:

1. Autenticación JWT y permiso de entrada (`ai.use`).
2. Escaneo anti *prompt injection* / *jailbreak* **antes** de llamar al LLM.
3. Catálogo cerrado de herramientas (tools); no hay SQL arbitrario ni código remoto.
4. Permiso IAM por tool + re-chequeo en handlers.
5. Alcance de datos (visibilidad) por rol (estudiante/docente solo ven lo propio).
6. Confirmación humana obligatoria en mutaciones.
7. Registro en LogIA y auditoría de dominio.
8. Controles adicionales: rate limit, anti-SSRF en URL del proveedor, enlaces firmados de reportes, sanitización de salida.

Esto se alinea con **Zero Trust** (“nunca confiar solo en el modelo”) y **mínimo privilegio** (el agente actúa con la identidad y permisos del usuario autenticado).

---

## 2. Modelo de amenazas que el sistema intenta cubrir

| Amenaza | Descripción | Controles actuales |
| --- | --- | --- |
| **Prompt injection** | Mensaje que intenta anular el system prompt o forzar conducta | Escáner regex pre-LLM + bloqueo + LogIA |
| **Jailbreak** | “Actúa como DAN / admin / sin reglas” | Mismos patrones + tono institucional en system prompt |
| **Abuso de tools** | El LLM inventa acciones o el usuario pide lo que no puede | Catálogo cerrado + permiso por tool + scope |
| **Escalada de privilegios** | Pedir mutaciones o datos de otros roles | IAM + visibilidad + confirmación |
| **Exfiltración de secretos** | API keys, system prompt, dumps técnicos | Clave cifrada/enmascarada; sanitización DSML/JSON; APA7 |
| **SSRF** | Forzar llamadas HTTP a hosts internos vía proveedor | Allowlist de URL del LLM |
| **Descarga indebida de reportes** | Acceso a artifacts ajenos | HMAC firmado + JWT dueño/ADMIN + caducidad |
| **Flood / abuso de API** | Spam de chat | Rate limit 20/min en `/ai/chat` |

---

## 3. Arquitectura de defensa en profundidad

```
Usuario (JWT)
    │
    ▼
[API] permission_required("ai.use") + rate limit
    │
    ▼
[Orquestador] scan_prompt_injection ──bloquea──► LogIA (prompt_injection / policy_block)
    │ OK
    ▼
[LLM] system prompt endurecido + tools schema (catálogo cerrado)
    │
    ▼
[Executor] tool existe? → permiso IAM? → ¿mutante? → confirmación
    │
    ▼
[Handlers] has_permission + visibility/scope + auditoría
    │
    ▼
[Respuesta] strip DSML / compose / format APA7 → UI (sin markup técnico)
```

**Fuentes de código principales**

| Capa | Ruta |
| --- | --- |
| Orquestador | `App/backend/app/ai/gateway/orchestrator.py` |
| Executor | `App/backend/app/ai/gateway/executor.py` |
| Registro de tools | `App/backend/app/ai/gateway/registry.py` |
| Handlers | `App/backend/app/ai/gateway/handlers.py` |
| Proveedor LLM / SSRF / DSML | `App/backend/app/ai/provider.py` |
| Anti-injection + LogIA | `App/backend/app/services/ai_agent_log.py` |
| Visibilidad | `App/backend/app/services/visibility.py` |
| Artifacts firmados | `App/backend/app/services/artifact_links.py` |
| Decoradores IAM | `App/backend/app/permissions/decorators.py` |
| Seed de roles | `App/database/seeds/seed_data.py` |

---

## 4. Permisos IAM del módulo IA

Formato de permiso: `{módulo}.{acción}`.

| Permiso | Quién lo tiene (seed típico) | Qué habilita |
| --- | --- | --- |
| `ai.use` | ADMIN, RECTOR, COORDINATOR, TEACHER, STUDENT, SECRETARY | Chat, conversaciones, tools del gateway, artifacts propios |
| `ai.configure` | ADMIN, IT_SUPPORT | Configurar proveedor, API key, modelo, system prompt |
| `ai.view_logs` | ADMIN, AUDITOR, IT_SUPPORT | Módulo **LogIA** (listar / exportar xlsx, pdf, json) |

### 4.1 Separación de privilegios (mínimo privilegio)

- Un **AUDITOR** puede ver LogIA (`ai.view_logs`) **sin** poder chatear (`ai.use` no está en su seed).
- Un **STUDENT** puede usar el chat, pero las tools de escritura fallan por falta de permisos y por scope.
- **IT_SUPPORT** configura IA y ve logs, pero no opera el dominio académico completo.
- El frontend oculta menús con `hasPerm()`; la **autoridad real** está en el backend.

### 4.2 Doble verificación de permisos

| Momento | Mecanismo |
| --- | --- |
| Entrada HTTP | Claims JWT + `@permission_required` |
| Ejecución de tool | `User.has_permission(perm)` contra BD (en vivo) |
| Handler | Muchas funciones vuelven a comprobar el permiso del dominio |

**Nota operativa:** si se cambian roles en BD, el JWT del API puede quedar desactualizado hasta re-login; el gateway del agente lee permisos desde BD, por lo que refleja cambios más rápido en tools.

---

## 5. Catálogo de tools y política de mutación

Solo existen las tools registradas en `HANDLERS` / `TOOL_SCHEMAS`. Una tool desconocida se rechaza (`Tool desconocida`).

### 5.1 Tools de lectura (sin confirmación; con permiso y scope)

Ejemplos: `careers_list`, `subjects_list`, `terms_list`, `courses_list`, `students_list`, `teachers_list`, `enrollments_list`, `grades_list`, `attendance_list`, `users_list`, `roles_list`, `audit_logs_list`, `reports_list_types`, `system_stats`.

### 5.2 Tools mutantes (confirmación obligatoria)

| Tool | Permiso típico | Efecto |
| --- | --- | --- |
| `careers_create` | `careers.create` | Alta de carrera |
| `careers_update` | `careers.edit` | Edición de carrera |
| `enrollments_create` | `enrollments.create` | Matrícula |
| `grades_upsert` | `grades.manage` | Notas |
| `attendance_upsert` | `attendance.manage` | Asistencia |
| `users_assign_roles` | `users.edit` | Asignación de roles |

**Política:** si `mutating=True` y no hay `confirm`, el executor responde `needs_confirm` y la conversación guarda `pending_action`. Solo tras palabras de confirmación (`confirma`, `sí`, `ok`, `acepto`, etc.) o flag `confirm=true` se ejecuta la escritura.

### 5.3 Reportes

`reports_generate` no pide confirmación de mutación (genera archivo), pero exige capacidad de reporte (`user_can_report`: ADMIN o `reports.export` / `.view` del dominio) y aplica los mismos filtros de visibilidad que los reportes REST.

### 5.4 Límites operativos

- Máximo **8** tool-calls por turno.
- Listados paginados con tope (p. ej. `per_page` ≤ 100).
- Rate limit chat: **20 solicitudes por minuto** (además del límite global de la API).

---

## 6. Controles anti prompt injection y jailbreak

### 6.1 Escáner de entrada (`scan_prompt_injection`)

Ubicación: `App/backend/app/services/ai_agent_log.py`.

Se ejecuta en el orquestador **antes** de invocar al LLM. Si hay coincidencia:

1. No se llama al proveedor ni se ejecutan tools.
2. Se responde con mensaje de política de seguridad (tono formal).
3. Se registran eventos LogIA: `prompt_injection` y `policy_block` (`severity=block`).
4. Se registra también en el log legado de chat.

**Patrones base detectados (lista heurística, EN/ES):**

- Ignorar instrucciones previas / anteriores.
- Revelar el system prompt.
- “You are now DAN / jailbreak / unrestricted”.
- Bypass de seguridad, permisos o roles.
- “Actúa como si fueras administrador”.
- Override de safety / policy / guardrails.
- Etiquetas `<system>`.
- “Developer mode enabled” / “Do anything now”.
- **SPEC-029 — escalada / spoofing de rol:** «cambia mi rol», «hazme admin», «soy un usuario administrador», «dame todos los permisos», bypass de mínimo privilegio / Zero Trust vía lenguaje natural (`kind=privilege_escalation`).

**Campo LogIA `user_question` (SPEC-029):** cada evento del turno guarda la pregunta/solicitud original del usuario (API, UI columna Pregunta, exports y búsqueda).

**SPEC-030 — mínimo privilegio por rol:**
- `tools_for_user`: el LLM solo ve tools permitidas.
- `scan_unauthorized_intent`: bloquea NL tipo «reporte de todos los usuarios del sistema» sin `users.view`/`reports.export`.
- Reportes de estudiantes acotados a cursos propios del docente.
- `system_stats` solo con visión institucional (`dashboard.view` / `reports.view` / `users.view`).

**No se bloquean** consultas legítimas del estilo «¿cuál es mi rol?» / «¿qué permisos tengo?».

**Excepción controlada:** mensajes de confirmación (`confirma`, `sí`, …) cuando ya existe una `pending_action` no se bloquean por el escáner, para no romper el flujo de confirmación de mutaciones.

### 6.2 Endurecimiento del system prompt

En `provider.py` (y contexto base en `deepseek.py`) se instruye al modelo a:

- Usar solo `tool_calls` de la API (no inventar markup DSML/XML para el usuario).
- No pegar JSON crudo ni bloques `[Tool …]`.
- Respetar confirmación en mutaciones.
- Presentar texto formal (guía APA 7 / SPEC-027): sin markdown ornamental ni emojis.

### 6.3 Sanitización de salida

| Control | Función |
| --- | --- |
| Parseo DSML como tools (SPEC-023) | Si el modelo emite markup interno, se trata como tool-call y pasa por el executor (misma IAM) |
| `strip_tool_markup` / `_is_raw_tool_dump` | Evita mostrar dumps técnicos al usuario |
| `format_apa_plain` | Elimina `*`, `**`, viñetas markdown y símbolos raros |
| Frontend `ai-chat.js` | Red de seguridad: oculta burbujas con DSML / dumps |

**Importante:** la sanitización de salida protege la UX y reduce fugas de markup; la **ejecución** de tools parseadas desde DSML sigue gobernada por IAM (no es un bypass de permisos).

---

## 7. Visibilidad y aislamiento de datos (scope)

Implementación: `App/backend/app/services/visibility.py` + filtros en handlers/reportes.

| Rol / perfil | Alcance típico vía agente |
| --- | --- |
| ADMIN / staff amplio | Lectura amplia según permisos IAM |
| TEACHER | Cursos asignados e intersección con periodos activos |
| STUDENT | Solo sus matrículas, notas y asistencia |
| GUARDIAN (si aplica en REST) | Alcance restringido; en seed habitualmente **sin** `ai.use` |

Las escrituras de notas/asistencia rechazan `course_id` fuera de `owned_course_ids`. Las conversaciones están atadas a `user_id` del dueño (ADMIN puede inspeccionar por id en ciertos endpoints de detalle).

---

## 8. Controles de infraestructura y secretos

### 8.1 Anti-SSRF del proveedor LLM

- `provider.py`: solo hosts allowlist (DeepSeek / OpenAI / localhost de desarrollo) y esquemas controlados.
- `deepseek.py` (ruta legada): más estricto (`https` + `api.deepseek.com`).
- La URL efectiva sale de configuración de aplicación, no de un parámetro libre del chat del usuario final.

### 8.2 API keys

- Almacenamiento cifrado en `AIConfig`.
- Respuestas de configuración enmascaran la clave.
- No se exponen al modelo ni al frontend en claro.

### 8.3 Artifacts / reportes (SPEC-021)

- Archivos en `instance/ai_artifacts/` con metadatos en BD.
- Caducidad por defecto (~72 h).
- Descarga con **URL firmada HMAC-SHA256** (`expires` + `sig`) o JWT del dueño / ADMIN.
- Artifact vencido → HTTP 410.

### 8.4 Cabeceras y límites HTTP

Aplicación Flask: cabeceras de seguridad (X-Frame-Options, nosniff, CSP, HSTS en no-debug), CORS configurado, limitadores de tasa.

---

## 9. Registro, monitoreo y trazabilidad (LogIA + Auditoría)

Módulo **LogIA** (`AIAgentLog` / SPEC-026 / SPEC-028), visible con `ai.view_logs`.

| Tipo de evento | Uso |
| --- | --- |
| `chat` | Interacción general del agente |
| `tool_call` / `tool_error` | Uso o fallo de tools |
| `report` | Generación de reportes |
| `prompt_injection` / `policy_block` | Bloqueos anti injection / jailbreak (**fila roja**) |
| `privilege_block` | Bloqueos Zero Trust / mínimo privilegio (**fila roja**) |
| `confirm` | Confirmaciones de mutación |

**SPEC-028:** todo bloqueo de seguridad se registra en **doble canal**:

| Canal | Acciones / módulo |
| --- | --- |
| LogIA | `prompt_injection`, `policy_block`, `privilege_block` (`severity=block`) |
| Auditoría | `AI_PROMPT_INJECTION_BLOCK`, `AI_POLICY_BLOCK`, `AI_PRIVILEGE_BLOCK`, `AI_UNKNOWN_TOOL_BLOCK` en módulo `ai_security` |

En la UI, ambas tablas resaltan esas filas en **rojo** con etiqueta «BLOQUEADO».

Filtros y exportación: palabra clave, usuario, conversación, evento, severidad, rol, fechas → Excel, PDF, JSON.

Además, el dominio registra eventos `AI_TOOL_*`, `AI_REPORT`, `AI_CONFIG_UPDATE`, etc. en la auditoría clásica.

---

## 10. Principios Zero Trust aplicados

| Principio Zero Trust | Cómo se materializa en este sistema |
| --- | --- |
| **Nunca confiar, siempre verificar** | El LLM no es fuente de autoridad; cada tool se revalida en servidor |
| **Verificar explícitamente** | JWT + permiso de endpoint + permiso de tool + scope de filas |
| **Acceso con mínimo privilegio** | Matriz rol→permiso; tools acotadas; estudiante/docente con scope |
| **Asumir incumplimiento** | Logs de bloqueo, auditoría de tools, artifacts con caducidad y firma |
| **Segmentación** | Catálogo cerrado (no shell, no SQL libre); UI ≠ backend |
| **Identidad como perímetro** | El agente actúa como el usuario del token (incl. sesión impersonada, si aplica) |

### 10.1 Principio de mínimo privilegio (Least Privilege)

1. El agente **hereda** los permisos del usuario; no tiene un “superusuario IA”.
2. Mutaciones requieren permiso de dominio **y** confirmación explícita.
3. Lecturas sensibles (auditoría, usuarios) exigen permisos propios (`audit.view`, `users.view`, …).
4. Configuración del proveedor (`ai.configure`) está separada del uso del chat.
5. Observabilidad (LogIA) está separada del uso operativo (`ai.view_logs` ≠ `ai.use`).

---

## 11. Matriz de controles vs ataque (estado actual)

| Control | Prompt injection | Jailbreak | Abuso de tools | Exfiltración | SSRF | Descarga indebida |
| --- | --- | --- | --- | --- | --- | --- |
| Escáner pre-LLM | ● | ● | ○ | ○ | ○ | ○ |
| System prompt endurecido | ◐ | ● | ◐ | ◐ | ○ | ○ |
| Catálogo cerrado + executor | ○ | ◐ | ● | ◐ | ○ | ○ |
| IAM + scope | ○ | ◐ | ● | ● | ○ | ○ |
| Confirmación mutaciones | ○ | ○ | ● | ○ | ○ | ○ |
| Sanitización salida | ◐ | ◐ | ○ | ● | ○ | ○ |
| Allowlist URL LLM | ○ | ○ | ○ | ○ | ● | ○ |
| Artifact HMAC/JWT | ○ | ○ | ○ | ◐ | ○ | ● |
| LogIA / audit | ● | ● | ● | ● | ○ | ● |
| Rate limit | ○ | ○ | ◐ | ○ | ○ | ○ |

Leyenda: ● fuerte · ◐ parcial · ○ no aplica / nulo.

---

## 12. Flujos de política (resumen normativo interno)

### P-01 — Entrada al asistente

Solo usuarios autenticados con `ai.use` pueden invocar `/api/v1/ai/chat` y gestionar sus conversaciones.

### P-02 — Bloqueo por inyección

Mensajes que coincidan con patrones de inyección/jailbreak se rechazan sin LLM, con respuesta de política y registro en LogIA.

### P-03 — Tools

Solo tools del catálogo. Sin permiso → denegación. Mutante → confirmación. Scope de datos siempre aplicado.

### P-04 — Secretos

API keys cifradas; system prompt y dumps técnicos no se muestran al usuario final.

### P-05 — Evidencia

Toda acción relevante del agente debe ser consultable en LogIA (y, cuando corresponda, en auditoría de dominio) por roles con `ai.view_logs` / `audit.view`.

### P-06 — Presentación

Las respuestas al usuario siguen presentación formal (SPEC-027 / guía APA 7 adaptada): sin markdown ornamental ni caracteres decorativos.

---

## 13. Limitaciones y riesgos residuales (honestidad operativa)

Estos puntos **no invalidan** los controles actuales, pero deben conocerse para endurecer futuras specs:

1. **Escáner heurístico:** lista regex fija; un atacante puede parafrasear. No hay clasificador semántico ni lista administrable en BD.
2. **`system_stats` (mitigado SPEC-030):** exige `dashboard.view` / `reports.view` / `users.view`; ya no se ofrece a TEACHER/STUDENT del seed.
3. **Elevación de privilegios:** schema/handler de solicitud existen de forma incompleta respecto a SPEC-016 (flujo no plenamente cableado en `HANDLERS`).
4. **Impersonación:** no hay guardia específica del agente; si un admin entra “como” otro usuario, el agente opera con la identidad impersonada.
5. **URLs firmadas de artifacts:** quien posee el enlace válido puede descargar hasta la expiración (diseño intencional; no hay token de un solo uso / binding por IP).
6. **Allowlist SSRF:** hay diferencias de rigor entre `provider.py` y la ruta legada `deepseek.py`.
7. **CORS amplio** en API (`*`) es un riesgo general de superficie, no exclusivo del agente.
8. **Confianza residual en el LLM:** mitigado con `tools_for_user` + intent guard + IAM; el modelo no debe recibir tools fuera de permiso.

---

## 14. Recomendaciones de endurecimiento (backlog sugerido)

Prioridad sugerida para próximas SPEC/SKILL:

1. Expandir y versionar la lista anti-injection / intent guard (configurable + pruebas adversariales).
2. Completar elevación de privilegios con flujo ADMIN + LogIA.
3. Marcar en LogIA cuando la sesión lleva `impersonator_id`.
4. Unificar política SSRF del proveedor LLM.
5. Tokens de descarga de un solo uso o TTL más corto para artifacts sensibles.
6. Evaluar detección semántica / segundo modelo de clasificación para jailbreaks sofisticados.

---

## 15. Referencias cruzadas

| Documento / spec | Tema |
| --- | --- |
| `permisos_role.md` | Matriz de roles y permisos del agente |
| SPEC-002 | Seguridad OWASP / SSRF / logging |
| SPEC-003 | Roles y permisos |
| SPEC-009 / SPEC-014 | Visibilidad y restricciones por perfil |
| SPEC-016 | Gateway del agente, tools, confirmación |
| SPEC-021 | Descarga firmada de artifacts |
| SPEC-023 | Sanitización DSML / tool markup |
| SPEC-026 | LogIA + anti prompt-injection |
| SPEC-027 | Presentación formal / typing UI |
| SPEC-029 / SKILL-028 | LogIA `user_question` + bloqueo escalada/spoofing de rol |
| SPEC-030 / SKILL-029 | Tools filtradas por rol + intent NL + scope reportes |
| SKILL-025 / SKILL-026 | Implementación LogIA y presentación |

---

## 16. Conclusión

El sistema aplica un **modelo de seguridad en capas** alrededor del agente IA: identidad JWT, mínimo privilegio por permiso y rol, catálogo cerrado de tools, confirmación humana en escrituras, aislamiento de datos por visibilidad, bloqueo heurístico de *prompt injection* / *jailbreak*, protección SSRF del proveedor, artifacts firmados y trazabilidad LogIA.

En términos de **Zero Trust**, el principio rector es: **el modelo es no confiable; el servidor decide**. En términos de **mínimo privilegio**, el agente **no amplía** poderes del usuario: solo automatiza lo que ese usuario ya podría hacer (con confirmación adicional en mutaciones).

Este archivo refleja el estado del código a la fecha indicada. Cualquier cambio de política debería ir acompañado de una nueva SPEC/SKILL y de la actualización de este documento y de `permisos_role.md`.
