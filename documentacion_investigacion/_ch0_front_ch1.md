# Portada / datos del estudio

**Título:** Diseño e implementación de un laboratorio experimental de gestión educativa con agente de inteligencia artificial y control de acceso orientado a Zero Trust mediante Tool Gateway: comparación de escenarios laboratorioIA y laboratorioIB

**Tipo de documento:** Informe técnico de investigación aplicada (desarrollo experimental de laboratorio)

**Ámbito del artefacto de software:** Repositorio local `D:\\PROYECTOS\\lab_ag_ia_g_edu`, con dos aplicaciones Flask paralelas (`laboratorioIA` y `laboratorioIB`) bajo `App/backend`

**Enfoque metodológico:** Diseño e implementación de software + experimentación controlada en laboratorio (escenarios A/B), sin inferencia estadística poblacional

**Estilo de citación:** APA 7.ª edición

**Idioma:** Español académico, tercera persona

**Fecha de documentación del código:** octubre 2026

**Nota de fidelidad empírica:** El presente documento describe únicamente funcionalidades, módulos, rutas, modelos, scripts de prueba y diferencias observables en el código fuente del repositorio indicado. No se reportan porcentajes de éxito de pruebas, significancia estadística, encuestas a usuarios, despliegue productivo ni componentes formales PDP/PAP inexistentes en el código. Cuando el README o el CHANGELOG afirman la existencia de carpetas `/Spec` o `/Skill`, se indica explícitamente que dichas carpetas no se encuentran presentes en el árbol del repositorio inspeccionado.

---

# Resumen

El estudio documenta el diseño e implementación de un laboratorio experimental de gestión académica institucional que integra un agente de inteligencia artificial (IA) con herramientas (tools) mediatizadas por un *Tool Gateway*, bajo un control de acceso basado en roles y permisos (RBAC) y controles orientados a principios de Zero Trust. El artefacto consta de dos escenarios de laboratorio, `laboratorioIA` y `laboratorioIB`, implementados como aplicaciones Flask 3 con SQLAlchemy, autenticación JWT, limitación de tasa (*rate limiting*), interfaz Jinja/Bootstrap 5 y proveedor de lenguaje DeepSeek. Ambos escenarios comparten el dominio académico (carreras, materias, periodos, cursos, matrículas, calificaciones y asistencia), el catálogo de tools del gateway y la bitácora del agente (LogIA / `AIAgentLog`), pero difieren en el mecanismo experimental de relajación o refuerzo de guards: `laboratorioIA` incorpora el modo `AI_INSECURE_MODE` (`insecure_mode.py`, referenciado como SPEC-031 en comentarios de código), mientras que `laboratorioIB` enfatiza el módulo dedicado `ai_intent_guard.py` (SPEC-030) para denegar intenciones en lenguaje natural fuera de permiso. El análisis del código confirma la ausencia de módulos formales PDP/PAP, la ausencia de directorios `/Spec` y `/Skill` pese a su mención en README, y el carácter parcial de `privileges_request_elevation` (función existente pero no registrada en el diccionario `HANDLERS`). La evaluación disponible se limita a scripts de humo y validación (`test_smoke.py`, `test_visibility.py`, `test_mysql.py`, `validate_ai_chat.py`, `validate_dsml_parse.py`, `validate_filters_export.py`), cuyos resultados dependen del entorno local de ejecución y no se generalizan estadísticamente en este informe.

**Palabras clave:** Zero Trust, Tool Gateway, agente de inteligencia artificial, RBAC, gestión educativa, laboratorio experimental, prompt injection, Flask, DeepSeek.

---

# Abstract

This study documents the design and implementation of an experimental laboratory for institutional academic management that integrates an artificial intelligence (AI) agent with tool calling mediated by a Tool Gateway, under role- and permission-based access control (RBAC) and controls aligned with Zero Trust principles. The software artifact comprises two laboratory scenarios, laboratorioIA and laboratorioIB, implemented as Flask 3 applications with SQLAlchemy, JWT authentication, rate limiting, Jinja/Bootstrap 5 UI, and a DeepSeek language provider. Both scenarios share the academic domain model, the gateway tool catalog, and the agent audit log (LogIA / AIAgentLog), but differ in the experimental relaxation or reinforcement of guards: laboratorioIA includes AI_INSECURE_MODE (insecure_mode.py; SPEC-031 in code comments), whereas laboratorioIB emphasizes the dedicated ai_intent_guard.py module (SPEC-030) to deny natural-language intents outside the caller's permissions. Code inspection confirms the absence of formal PDP/PAP modules, the absence of /Spec and /Skill directories despite README claims, and the partial status of privileges_request_elevation (implemented as a function but not registered in HANDLERS). Available evaluation is limited to smoke and validation scripts whose outcomes depend on the local execution environment and are not statistically generalized in this report.

**Keywords:** Zero Trust, Tool Gateway, AI agent, RBAC, educational management, experimental laboratory, prompt injection, Flask, DeepSeek.

---

# Índice

1. Capítulo I. El problema de investigación
2. Capítulo II. Marco teórico y conceptual
3. Capítulo III. Metodología
4. Capítulo IV. Análisis, diseño e implementación
5. Capítulo V. Pruebas, resultados y discusión
6. Capítulo VI. Conclusiones y trabajo futuro
7. Referencias
8. Anexos
   - Anexo A. Estructura de directorios
   - Anexo B. Catálogo de endpoints (resumen)
   - Anexo C. Catálogo de tools del gateway
   - Anexo D. Variables de entorno (nombres)
   - Anexo E. Diferencias laboratorioIA vs laboratorioIB

---


# Capítulo I. El problema de investigación

## 1.1 Antecedentes

La digitalización de la gestión académica ha consolidado sistemas institucionales capaces de administrar identidades, roles, matrículas, calificaciones y asistencia. En paralelo, la adopción de asistentes basados en modelos de lenguaje introduce un canal de interacción no determinista: el usuario expresa intenciones en lenguaje natural y el sistema debe traducirlas a operaciones sobre datos sensibles. Esta convergencia genera una tensión operativa entre usabilidad y control de acceso. Rose et al. (2020) formalizan Zero Trust Architecture (ZTA) como un enfoque en el que ninguna solicitud se considera intrínsecamente confiable por su ubicación o por una autenticación inicial, sino que cada acceso se evalúa con identidad, política y contexto. En el ámbito de la ciberseguridad educativa y de los sistemas de información, Syed et al. (2022) y Buck et al. (2021) sitúan Zero Trust como respuesta a modelos perimetrales insuficientes cuando los actores, dispositivos y APIs se multiplican.

Los agentes con herramientas (tool-using agents) amplifican el problema: el modelo no solo responde texto, sino que puede invocar funciones que leen o mutan el estado del sistema. Kang et al. (2023) y Azad et al. (2024) evidencian la relevancia de superficies de ataque asociadas a inyección de instrucciones y a la mala alineación entre intención del usuario y privilegios reales. Deng et al. (2025) sintetizan líneas de defensa para agentes, mientras que Jeong y Yang (2025) y Xu et al. (2025) discuten controles prácticos en entornos aplicados. En educación, Adahman et al. (2022) y Awan et al. (2023) subrayan la sensibilidad de datos académicos y la necesidad de gobernanza; Vasović et al. (2026), Mawgoud et al. (2025), Kanaker et al. (2026), Gulyamov et al. (2026) y Geng et al. (2026) aportan marcos contemporáneos sobre confianza, privacidad y arquitecturas de control en sistemas conectados. Shostack (2014) ofrece una base metodológica de modelado de amenazas que permite razonar sobre activos, actores y controles sin presuponer métricas de campo no medidas.

El repositorio lab_ag_ia_g_edu materializa esta problemática en un laboratorio reproducible: dos aplicaciones Flask (laboratorioIA y laboratorioIB) con dominio académico completo, RBAC granular, agente DeepSeek y un Tool Gateway que filtra tools según permisos, exige confirmación en mutaciones (salvo modo inseguro) y registra bloqueos en LogIA y auditoría. El presente capítulo formula el problema a partir de esa evidencia de software, no a partir de un despliegue productivo inexistente en el artefacto documentado.

## 1.2 Planteamiento del problema

En sistemas de gestión educativa con agente conversacional, el riesgo no se limita a la autenticación fallida. Un usuario autenticado con rol restringido (por ejemplo, TEACHER o STUDENT) puede formular en lenguaje natural solicitudes que exceden su ámbito: listados institucionales de usuarios, exportación masiva de estudiantes, consulta de auditoría o asignación de roles. Si el agente dispone de tools poderosas y el orquestador no intermedia la invocación con comprobaciones de permiso, confirmación y registro, se rompe el principio de mínimo privilegio. Rose et al. (2020) enfatizan la evaluación continua de acceso; Syed et al. (2022) y Buck et al. (2021) advierten que la confianza implícita post-login es un anti-patrón. Kang et al. (2023) y Azad et al. (2024) muestran que la inyección de prompts puede intentar redefinir políticas del asistente. Deng et al. (2025) y Jeong y Yang (2025) destacan que la defensa debe combinar filtrado de entrada, restricción de herramientas y telemetría.

El problema práctico del laboratorio es, por tanto, doble: (a) construir un sistema académico funcional con IAM, reglas de notas/asistencia, reportes y chat con tools; y (b) comparar escenarios de control del agente (IA vs IB) que permitan observar, en condiciones de laboratorio, cómo se endurecen o relajan los guards sin inventar una arquitectura Zero Trust completa con PDP/PAP formales. El código implementa controles orientados a Zero Trust (chequeo por tool, logging zero_trust/least_privilege en bloqueos, denegación de intentos NL), pero no implementa Policy Decision Point ni Policy Administration Point como módulos nombrados. Declarar lo contrario sería una distorsión empírica.

## 1.3 Formulación del problema

¿Cómo diseñar e implementar un laboratorio experimental de gestión educativa con agente de IA y Tool Gateway, de modo que el control de acceso RBAC y los guards del agente (incluyendo diferencias entre laboratorioIA y laboratorioIB) operen de forma verificable en código, alineados con principios de Zero Trust, sin afirmar componentes o resultados que no existan en el repositorio?

## 1.4 Preguntas de investigación

1. ¿Qué arquitectura de software y qué modelos de dominio académico e IAM existen efectivamente en laboratorioIA y laboratorioIB?
2. ¿Cómo el Tool Gateway (
egistry, executor, handlers, orchestrator) restringe tools, mutaciones y registro de bloqueos?
3. ¿En qué difieren los escenarios IA (modo AI_INSECURE_MODE) e IB (módulo i_intent_guard) respecto a guards del agente?
4. ¿Qué evidencia de verificación aportan los scripts de humo y validación existentes, y cuáles son sus límites?
5. ¿Qué elementos quedan parciales o ausentes (elevación de privilegios en HANDLERS, carpetas Spec/Skill, migraciones Alembic pobladas, PDP/PAP)?

## 1.5 Justificación

La justificación es técnica y académica. Técnicamente, el laboratorio ofrece un entorno controlado para estudiar el acoplamiento entre RBAC clásico (decoradores y permisos modulo.accion) y un canal de agente que puede saltarse la UI. Académicamente, permite contrastar literatura de Zero Trust y agentes (Rose et al., 2020; Syed et al., 2022; Buck et al., 2021; Kang et al., 2023; Azad et al., 2024; Deng et al., 2025; Jeong & Yang, 2025; Xu et al., 2025) con una implementación concreta y auditable. En el contexto educativo, la exposición de calificaciones, asistencia y directorios de usuarios exige controles explícitos (Adahman et al., 2022; Awan et al., 2023). El valor del estudio no reside en afirmar madurez productiva, sino en documentar con precisión qué está implementado, qué es parcial y qué queda como trabajo futuro, en la línea de transparencia metodológica que Shostack (2014) asocia al modelado de amenazas honesto.

## 1.6 Objetivo general

Diseñar, implementar y documentar un laboratorio experimental de gestión educativa con agente de IA y Tool Gateway, comparando los escenarios laboratorioIA y laboratorioIB en cuanto a controles de acceso y guards orientados a Zero Trust, con base exclusiva en evidencia del código fuente.

## 1.7 Objetivos específicos

1. Describir la arquitectura Flask, el stack tecnológico y los modelos de datos académicos e IAM presentes en ambas aplicaciones.
2. Caracterizar el Tool Gateway: registro de schemas, filtrado por permisos, ejecución con confirmación, handlers y orquestación del chat.
3. Analizar los mecanismos de seguridad del agente (heurísticas de inyección, LogIA, intent guard, modo inseguro) y su mapeo a comentarios SPEC-016…SPEC-031 en el código.
4. Comparar sistemáticamente diferencias observables entre laboratorioIA y laboratorioIB.
5. Documentar la batería de scripts de prueba/validación sin inventar tasas de éxito, e identificar limitaciones y trabajo futuro (incluyendo el cableado de privileges_request_elevation al diccionario HANDLERS).

## 1.8 Alcance

El alcance incluye: (a) inspección y documentación de laboratorioIA/App y laboratorioIB/App; (b) API REST bajo /api/v1; (c) dominio académico y reglas de negocio de notas y asistencia; (d) Tool Gateway y servicios de IA; (e) seeds y dumps SQL (laboratorioa.sql, laboratoriob.sql); (f) scripts de prueba en ackend/. El alcance excluye: despliegue en producción, evaluación con usuarios reales, análisis estadístico inferencial, implementación de PDP/PAP formales no presentes, y reconstrucción de especificaciones Spec-as-Skill ausentes como carpetas en el repositorio.

## 1.9 Limitaciones

Las limitaciones principales son: (1) los README afirman metodología Spec as Skill con rutas /Spec y /Skill, pero esas carpetas no existen en el árbol inspeccionado; (2) database/migrations está vacío y el esquema se crea vía db.create_all() y dumps SQL; (3) no hay PDP/PAP como componentes formales; (4) privileges_request_elevation existe como función y modelo ElevationRequest, pero no está en HANDLERS, por lo que el LLM no puede invocarla como tool registrada; (5) la evaluación es de laboratorio y dependiente del entorno (BD sembrada, API key DeepSeek, variables .env); (6) no se reportan métricas de efectividad de bloqueos ni significancia estadística porque no forman parte de los artefactos de prueba del repositorio.

## 1.10 Hipótesis de trabajo (no estadística)

Se formula como hipótesis de diseño, no como hipótesis estadística a contrastar con p-valores: un Tool Gateway que filtre tools por permiso, confirme mutaciones, registre bloqueos en LogIA/auditoría y aplique guards de inyección e intención reduce la superficie de acciones no autorizadas del agente respecto de un modo deliberadamente inseguro, en el marco de un laboratorio controlado. La verificación se realiza por inspección de código y scripts deterministas locales, no por inferencia poblacional.

## 1.11 Relevancia para la ciberseguridad educativa

Los datos académicos concentran información personal y de rendimiento. Un agente que pueda llamar users_assign_roles, grades_upsert o 
eports_generate sin mediación adecuada concentra riesgo de abuso interno y de manipulación por prompt. Vasović et al. (2026) y Mawgoud et al. (2025) insisten en controles aplicados; Kanaker et al. (2026) y Gulyamov et al. (2026) refuerzan la necesidad de arquitecturas explicables y auditables; Geng et al. (2026) aportan perspectivas de control en sistemas conectados. El laboratorio permite ensayar estas preocupaciones en un sistema completo pero no productivo, con datos sintéticos de seeds (seed_coherent, seed_massive, seed_data).

## 1.12 Delimitación operativa de Zero Trust en este estudio

En este documento, “orientado a Zero Trust” significa: autenticación JWT previa al uso del agente; autorización por permiso en cada tool; denegación por defecto de tools desconocidas; registro de bloqueos con marcas zero_trust y least_privilege en el detalle del executor; ausencia de confianza ciega en el texto del modelo. No significa equivalencia con una implementación completa de NIST SP 800-207 con PDP, PEP y PAP separados. Rose et al. (2020) proporcionan el marco conceptual; el software aporta un subconjunto práctico mediatizado por el gateway.
