

## 2.8 Ampliación analítica: Zero Trust aplicado a agentes con herramientas

La literatura sobre Zero Trust ha madurado desde principios de verificación continua hacia marcos operativos que exigen autenticación, autorización y telemetría para cada solicitud de acceso a un recurso (Rose et al., 2020; Syed et al., 2022). No obstante, la mayor parte de las guías institucionales se concentra en identidades humanas, dispositivos y microsegmentación de red. Cuando el sujeto de la solicitud es un agente de lenguaje que decide invocar herramientas, el recurso deja de ser únicamente un endpoint HTTP expuesto al usuario y pasa a ser un conjunto de efectos colaterales —lectura de calificaciones, escritura de asistencia, generación de reportes— ejecutados en nombre del usuario autenticado. Buck et al. (2021) y Adahman et al. (2022) subrayan la escasez de evidencia empírica transferible; el laboratorio aquí documentado no pretende llenar ese vacío con inferencia poblacional, sino ofrecer un artefacto reproducible donde la mediación Tool Gateway hace observables denegaciones y confirmaciones.

Kang et al. (2023) y Azad et al. (2024) sitúan la inyección de instrucciones y el abuso de privilegios como amenazas estructurales de los sistemas basados en LLM. Deng et al. (2025) sistematizan superficies de ataque de agentes; Kanaker et al. (2026) destacan el mínimo privilegio de herramientas como control de alto impacto relativo. En ese marco, el diccionario `HANDLERS` del repositorio opera como catálogo explícito de capacidades: lo que no está registrado no se ejecuta, y lo que está registrado exige permiso JWT o lógica equivalente. Esta decisión es coherente con Zero Trust en el sentido de Rose et al. (2020) —no hay confianza implícita post-login—, pero no equivale a un PDP/PAP NIST completo. Declarar equivalencia sería una sobreafirmación.

Jeong y Yang (2025) proponen evaluaciones de confianza contextuales; Awan et al. (2023) exploran control de acceso basado en atributos. El laboratorio implementa fundamentalmente RBAC con atributos de visibilidad (cursos propios, periodos activos) en servicios de dominio, no un motor ABAC generalizado. Vasović et al. (2026) y Mawgoud et al. (2025) recuerdan la sensibilidad de datos educativos; por ello el laboratorio usa seeds sintéticos y cifrado AES de la API key, sin afirmar cumplimiento normativo integral. Xu et al. (2025), Gulyamov et al. (2026) y Geng et al. (2026) refuerzan la necesidad de defensas arquitectónicas frente a prompt injection: el código combina heurísticas de escaneo, intent guard (IB) y modo inseguro deliberado (IA) para contraste pedagógico.

## 2.9 Relación crítica entre Spec-as-Skill documentado y evidencia en disco

El README y el CHANGELOG presentan el desarrollo como *Spec as Skill*, con identificadores SPEC-001 a SPEC-031 mapeados a funcionalidades (IAM, OWASP headers, módulos académicos, DeepSeek, impersonación, LogIA, intent guard, insecure mode). Desde el punto de vista metodológico, esa narrativa es útil como trazabilidad de intención de diseño. Desde el punto de vista empírico, las carpetas `/Spec` y `/Skill` anunciadas no existen en el repositorio inspeccionado. Shostack (2014) insiste en que el modelo debe corresponder al sistema real; por tanto, este informe trata los códigos SPEC como metadatos en comentarios/CHANGELOG, no como artefactos de especificación versionados. La distinción evita confundir documentación aspiracional con evidencia verificable.

## 4.16 Detalle del ciclo de autorización del Tool Gateway

El flujo de autorización del agente, verificado en `executor.execute_tool`, puede describirse en capas:

1. **Resolución de tool.** Si el nombre no existe en `HANDLERS`, se retorna `unknown_tool` y se registra bloqueo con etiquetas `zero_trust` / `least_privilege` vía `_log_privilege_block` y `log_security_block`.
2. **Chequeo de permiso.** Si la tupla del handler declara un permiso (por ejemplo `grades.manage`) y `user.has_permission` es falso, se deniega con `needs_elevation` y se audita `AI_PRIVILEGE_BLOCK`.
3. **Confirmación de mutación.** Si `mutating` es verdadero y no hay `confirm`, se responde `needs_confirm` sin ejecutar efectos. En laboratorioIA, `AI_INSECURE_MODE` puede relajar este y otros guards; el default del módulo es modo seguro.
4. **Ejecución del handler.** Los handlers de dominio reutilizan servicios (`grades`, `attendance`, `visibility`, reportes) y escriben `log_event` en auditoría sistémica cuando corresponde.
5. **Telemetría LogIA.** Bloqueos de inyección, privilegio e intención no autorizada se persisten en `AIAgentLog` y se exponen en UI LogIA y endpoints `/ai/agent-logs`.

Esta cadena no sustituye una arquitectura Zero Trust empresarial; materializa un punto de aplicación de política (PEP-like) centrado en tools del agente, coherente con la idea de verificación por solicitud (Rose et al., 2020; Syed et al., 2022).

## 4.17 Dominio académico: reglas de negocio verificables

**Calificaciones.** El modelo `Grade` y el servicio asociado combinan `partial1`, `partial2` y, cuando aplica, `supplementary`. La función de cómputo determina promedio y estado (`en_curso`, `aprobado`, `reprobado`) con umbral de aprobación `final_grade >= 7.0`. El script `test_smoke.py` ejercita el caso de necesidad de suplementario y el registro con suplementario. No se reportan aquí tasas de aprobación institucionales: los datos son de laboratorio.

**Asistencia.** Los estados incluyen `presente`, `ausente`, `tardanza` y `justificada`. La función de criticidad marca ausencia crítica cuando la proporción de `ausente` supera 0.25 sobre los registros del curso. Esta regla es de negocio local del laboratorio, no una norma ministerial.

**Visibilidad.** `visibility.py` restringe cursos y periodos visibles para roles de perfil (estudiante/docente). `test_visibility.py` contrasta admin frente a perfiles acotados. El diseño evita que el agente o la API filtren “todo el instituto” para roles que no tienen permiso institucional.

**Reportes y kárdex.** Existen exportaciones PDF/XLSX y kárdex por estudiante. El agente puede listar tipos y generar reportes según chequeos `user_can_report` / permisos, con artifacts descargables. El catálogo de reportes de UI puede ser más amplio que el subconjunto expuesto al agente; esa asimetría es una limitación de alcance del canal conversacional, no un defecto ocultado.

## 4.18 Seguridad de aplicación (no Zero Trust completo)

Además del gateway, `create_app` aplica cabeceras de endurecimiento, Flask-Limiter en login y chat, bloqueo por intentos fallidos, hash de contraseñas, JWT access/refresh, impersonación controlada y cifrado AES de la clave DeepSeek. Estos controles responden a una postura OWASP-oriented documentada en CHANGELOG (SPEC-002). No se afirma pentest formal, certificación ISO ni despliegue endurecido en producción: no hay evidencia de ello en el repositorio.

## 4.19 Implicaciones para la formación en ciberseguridad

El valor formativo del artefacto reside en la reproducibilidad de dos escenarios contrastables. En laboratorioIA, el instructor puede activar `AI_INSECURE_MODE` para observar qué ocurre cuando se debilitan guards del agente. En laboratorioIB, `ai_intent_guard` ilustra denegación temprana de intenciones NL no autorizadas. Ambos comparten LogIA, lo que permite discutir trazabilidad. Esta utilidad pedagógica no debe confundirse con evidencia de efectividad institucional generalizable (Buck et al., 2021; Adahman et al., 2022).

## 5.7 Discusión ampliada frente a la literatura

Los hallazgos de implementación confirman la tesis de Kanaker et al. (2026) y Deng et al. (2025) en un sentido acotado: restringir el catálogo de herramientas y auditar denegaciones es una defensa arquitectónica tangible. Al mismo tiempo, la ausencia de PDP/PAP y de evaluaciones cuantitativas alineadas con Adahman et al. (2022) impide afirmar madurez Zero Trust de nivel organizacional. La comparación A/B del laboratorio se acerca más a un diseño experimental de controls on/off que a un ensayo clínico de seguridad. Xu et al. (2025) y Geng et al. (2026) advierten que la IA generativa puede erosionar supuestos de control; el modo inseguro de laboratorioIA existe precisamente para hacer visible ese riesgo en un entorno controlado, no para normalizarlo en producción.

La integración educativa del agente —consulta de notas, asistencia y reportes— conecta con preocupaciones de Vasović et al. (2026) y Mawgoud et al. (2025) sobre datos académicos. El laboratorio responde con RBAC, visibilidad y seeds sintéticos. No responde con anonimización diferencial, federación de identidad ni SGSI completo; esas ausencias se listan como trabajo futuro, no como logros.

## 5.8 Criterios de aceptación documental (auditoría de fidelidad)

Para cada afirmación fuerte del informe se aplicó el criterio: ¿existe archivo, clase, ruta o script que la sustente? Si la respuesta es negativa, la afirmación se reformuló o se clasificó como pendiente. Ejemplos:

| Afirmación tentativa | Veredicto |
| --- | --- |
| Existe Tool Gateway con orchestrator/registry/executor/handlers | Implementado |
| Existe PDP/PAP formal | No implementado |
| Existen carpetas /Spec y /Skill | No verificado en disco |
| Elevación de privilegios vía tool | Parcial (fuera de HANDLERS) |
| Pruebas de humo y validadores | Implementados como scripts |
| 95% de efectividad del agente | Sin evidencia — no se afirma |
| Despliegue productivo ISTAE | Sin evidencia — no se afirma |
