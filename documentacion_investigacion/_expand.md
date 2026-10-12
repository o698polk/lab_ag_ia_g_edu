
## 2.11 Lectura analítica de NIST SP 800-207 aplicada al laboratorio

Rose et al. (2020) distinguen componentes lógicos de ZTA, entre ellos el Policy Engine / Policy Decision Point y mecanismos de aplicación (PEP). En el laboratorio, la decisión de permitir una tool se distribuye entre: (a) el filtrado previo de schemas (`tools_for_user`); (b) el chequeo de permiso en `execute_tool`; (c) chequeos adicionales dentro de handlers (`_perm_ok`, scoping, `user_can_report`); y (d) guards de mensaje en el orquestador. Esta distribución es típica de aplicaciones monolíticas: no hay un motor de políticas externo consultado por API. Syed et al. (2022) advierten que muchas organizaciones implementan Zero Trust de forma incremental; el laboratorio debe leerse exactamente así: un incremento sobre el canal del agente, no una plataforma ZTA. Buck et al. (2021) añaden que la percepción de complejidad es barrera de adopción; por ello un lab didáctico con flag `AI_INSECURE_MODE` puede ser más enseñable que un despliegue opaco.

La noción de “nunca confiar, siempre verificar” se concreta cuando un usuario ya autenticado como `TEACHER` intenta, vía NL, obtener `audit_logs_list` u operaciones `users_assign_roles`: el sistema no asume que el chat hereda confianza ilimitada. Kanaker et al. (2026) y Gulyamov et al. (2026) subrayan la auditabilidad; LogIA responde a esa exigencia al persistir `user_question`, `event_type` y `detail`. Geng et al. (2026) y Vasović et al. (2026) situarían estos registros como evidencia operacional mínima.

## 2.12 Agentes, least privilege y el problema del “deputy confuso”

Shostack (2014) describe escenarios en los que un componente con más privilegios es engañado para actuar en nombre de un actor menos privilegiado. El agente LLM es un candidato clásico a deputy confuso si se ejecuta con credenciales de servicio amplias. El diseño del laboratorio evita ese anti-patrón al ejecutar handlers con el `User` de la sesión JWT. Deng et al. (2025) recomiendan restringir herramientas; el allowlist `HANDLERS` y el filtrado de schemas operacionalizan esa recomendación. Kang et al. (2023) y Azad et al. (2024) muestran que el adversario intentará que el modelo ignore la política; de ahí la necesidad de enforcement en executor, no solo en el system prompt de `AIConfig`.

Jeong y Yang (2025) y Xu et al. (2025) discuten controles prácticos y privacidad: en el laboratorio, la no exposición de la API key al frontend y el enmascaramiento en `to_dict(mask_key=True)` son controles de confidencialidad del secreto del proveedor. Mawgoud et al. (2025) recuerdan robustez bajo carga; `Flask-Limiter` y la exención condicionada en modo inseguro muestran una tensión explícita entre usabilidad de laboratorio y protección.

## 2.13 Educación, datos sintéticos y ética de laboratorio

Adahman et al. (2022) y Awan et al. (2023) enfatizan costos y amenazas en entornos digitales educativos. El uso de seeds sintéticos permite practicar controles sobre calificaciones y directorios sin tratar datos reales de menores o de estudiantes identificados. El README publica credenciales demo: aceptable en lab cerrado, inaceptable si el mismo árbol se expone a Internet sin endurecimiento. Esta frontera ética debe formar parte de la enseñanza del artefacto.

## 2.14 Síntesis actualizada de la brecha de investigación

Tras el análisis conceptual, la brecha permanece: faltan laboratorios abiertos que documenten con rigor la mediación Tool Gateway en un SIS (Student Information System) simplificado, con escenarios A/B de guards y con honestidad sobre lo no implementado. El aporte de este trabajo es llenar esa brecha a escala de prototipo reproducible, citando el marco Zero Trust (Rose et al., 2020; Syed et al., 2022; Buck et al., 2021) y el de seguridad de agentes (Kang et al., 2023; Azad et al., 2024; Deng et al., 2025; Jeong & Yang, 2025; Xu et al., 2025) sin inventar madurez inexistente.

## 4.23 Análisis detallado de permisos por rol (seed)

El archivo `seed_data.py` define una matriz que conviene interpretar en clave de mínimo privilegio. `TEACHER` recibe gestión de notas y asistencia, vista de cursos/estudiantes/horarios y `ai.use`, pero no administración de usuarios ni auditoría. `STUDENT` consulta lo propio (grades/attendance/schedules/enrollments/terms/subjects/courses) y puede usar IA, lo que obliga al scoping para que el agente no se convierta en oráculo institucional. `SECRETARY` concentra matrículas y kárdex. `AUDITOR` ve logs y reportes, no muta notas. `IT_SUPPORT` administra usuarios/roles y configuración IA, sin convertirse automáticamente en rector académico. `RECTOR` supervisa con amplio read/export. `COORDINATOR` gestiona catálogo académico. `REVIEWER` es mayormente lectura. `GUARDIAN` consulta información del estudiante a cargo (en la medida en que el resto del código lo enlace). `ADMIN` es omnisciente por bypass. Esta matriz es el corazón del RBAC que el gateway reutiliza.

## 4.24 Análisis de `system_stats` y reportes como superficie sensible

`system_stats` no usa un permiso único en la tupla HANDLERS (`perm=None`); implementa chequeo propio exigiendo `dashboard.view` o `reports.view` o `users.view` fuera de modo inseguro. El comentario SPEC-030 aclara que la visión institucional no está disponible para teacher/student típicos del seed. `reports_generate` similarly depends on `user_can_report`. Estas excepciones muestran que el diseño reconoce tools “meta” cuyo daño es de confidencialidad agregada (conteos, exportaciones), no solo de mutación.

## 4.25 Conversaciones, pending_action y confirmación

`AIConversation.pending_action` almacena JSON de una mutación en espera. El orquestador, ante `needs_confirm`, pide al usuario confirmar; si el siguiente mensaje es de confirmación (`is_confirm_message`), se reanuda `execute_tool(..., confirm=True)`. Este protocolo es un control UX-seguridad: reduce la probabilidad de que una interpretación errónea del LLM modifique notas o roles. En modo inseguro IA, el protocolo se omite a propósito.

## 4.26 Presentación APA del asistente (SPEC-027)

`ai_text_format.format_apa_plain` y `_finalize_reply` buscan respuestas sin markdown ornamental, alineadas a un tono formal. No debe confundirse con el estilo APA de este documento académico; es una regla de presentación del chatbot. SPEC-022/023 complementan evitando que el usuario vea dumps DSML o JSON de tools.

## 4.27 Cabeceras de seguridad y superficie web

`set_security_headers` aplica `X-Frame-Options: DENY`, `nosniff`, referrer policy estricta y CSP que permite CDN jsDelivr/Google Fonts y `'unsafe-inline'` en scripts/estilos. El `'unsafe-inline'` es un compromiso típico de apps con JS embebido; un hardening futuro podría nonces. HSTS solo fuera de debug. Estos controles responden a SPEC-002 / OWASP en el CHANGELOG, sin transformar la app en un benchmark OWASP completo.

## 4.28 Impersonación como poder excepcional

`login-as` permite a un administrador operar como otro usuario. En modelado de amenazas (Shostack, 2014), es un target de abuso interno. El laboratorio lo incluye para soporte y pruebas (`test_smoke.py`). La presencia de `impersonator_id` en claims permite, en principio, distinguir sesiones impersonadas; el uso correcto depende de disciplina operacional y auditoría.

## 4.29 DeepSeek como dependencia externa

`provider.py` / `deepseek.py` encapsulan la llamada HTTP. Sin API key, el orquestador cae a `_fallback_reply` explicando la falta de configuración. Esto implica que parte de la experiencia del agente no es local-first completa: el razonamiento NL depende del proveedor, mientras que el enforcement de tools es local. Esa separación es deseable: aun si el proveedor fallara o fuera comprometido a nivel de texto, el executor local sigue siendo la autoridad sobre mutaciones.

## 4.30 Coherencia API REST ↔ tools

Un principio de diseño verificable es que las tools reutilizan servicios (`apply_grade_rules`, `validate_course_capacity`, `apply_course_scope`) también usados por la API. Ello reduce drift de autorización entre UI/API y agente. No obstante, no todas las rutas REST tienen tool equivalente (p. ej., no hay tools para cada DELETE académico), lo cual limita la superficie del agente de forma deliberada.

## 4.31 Estado de migrations y riesgo de esquema

La dependencia `Flask-Migrate` sin revisiones pobladas implica que entornos distintos pueden divergir si se alteran modelos manualmente. `ensure_schema` en LogIA intenta parches defensivos para columnas nuevas (`user_question`). Es un patrón de laboratorio, no de ingeniería de release. El trabajo futuro con Alembic busca corregir esta deuda.

## 5.16 Discusión extendida: qué significaría “pasar” las pruebas

En ingeniería de software, “pasar” `test_visibility.py` significa que, bajo el seed esperado, las cardinalidades y códigos de periodo coinciden con aserciones. No significa que el scoping sea inmune a IDOR sofisticados no cubiertos por el script. “Pasar” `validate_dsml_parse.py` significa que un sample representativo de markup se parsea; no cubre todos los dialectos posibles del modelo. “Pasar” `validate_ai_chat.py` en un entorno sin API key puede apoyarse en caminos de tool forzado; ello valida persistencia/artifacts más que la calidad generativa del LLM. Estas distinciones evitan la falacia de extrapolar humo a seguridad demostrada.

## 5.17 Discusión extendida: modo inseguro como control negativo

En metodología experimental, un control negativo muestra el fenómeno sin la intervención protectora. `AI_INSECURE_MODE=1` funciona como control negativo del agente: permite reproducir un asistente que confía excesivamente en el modelo. El investigador puede entonces contrastar logs y comportamientos con el modo seguro. Rose et al. (2020) no recomiendan inseguridad; el valor es pedagógico-experimental, análogo a desactivar un WAF en un lab aislado para enseñar su función. La documentación del `.env.example` cumple un rol ético al etiquetar el peligro.

## 5.18 Discusión extendida: intent guard y falsos positivos

Las reglas de `ai_intent_guard` / patrones de unauthorized intent pueden bloquear frases legítimas si se formulan como “lista todos los usuarios…”. El hint de ámbito propio mitiga falsos positivos docentes (“mis estudiantes”). Aun así, un clasificador basado en regex es frágil (Kang et al., 2023). Deng et al. (2025) sugerirían evaluaciones sistemáticas; el repo aún no las incluye como dataset. Por eso el Capítulo V se abstiene de métricas de precisión/recall.

## 5.19 Discusión sobre Zero Trust “suficiente”

¿Es “suficiente” Zero Trust este laboratorio? La pregunta es mal planteada si se espera un sí/no absoluto. Frente a NIST SP 800-207 (Rose et al., 2020), es un subconjunto. Frente a un chat sin mediación, es un salto cualitativo de control. Frente a un campus con IdP, MFA obligatorio, microsegmentación y PDP central, es preliminar. Syed et al. (2022) y Buck et al. (2021) invitan a evaluar madurez por capacidades, no por etiquetas de marketing. Este informe adopta esa cautela.

## 5.20 Implicaciones para la investigación en ciberseguridad educativa

El artefacto permite tesis y prácticas sobre: autorización en agentes, diseño de logs de seguridad, amenazas a SIS, y gobernanza de secretos de LLM. Awan et al. (2023) y Adahman et al. (2022) enmarcan el sector; Vasović et al. (2026), Mawgoud et al. (2025), Kanaker et al. (2026), Gulyamov et al. (2026) y Geng et al. (2026) actualizan el diálogo científico. El presente documento aporta la línea base descriptiva del sistema real.

## 6.9 Lecciones aprendidas de la documentación empírica

Documentar un sistema real obliga a reconciliar marketing interno del README con el disco. La lección metodológica es que los identificadores SPEC en comentarios son útiles, pero no reemplazan artefactos Spec. Otra lección: las funciones “huérfanas” (`privileges_request_elevation`) son hallazgos de investigación tan valiosos como las features completas, porque revelan deuda de integración. Una tercera lección: los escenarios A/B deben diferenciarse por pocos módulos para no confundir el factor experimental.

## 6.10 Recomendaciones para docentes que usen el laboratorio

1. Partir siempre de `AI_INSECURE_MODE` desactivado en demos públicas.
2. Ejecutar `test_visibility.py` tras seed para validar dataset.
3. Contrastar en clase un prompt de listado institucional con roles teacher vs admin, observando LogIA.
4. Mostrar el código de `executor.py` como PEP didáctico.
5. Discutir con estudiantes la ausencia de PDP/PAP y pedirles un diseño futuro.
6. No presentar el laboratorio como producto certificado Zero Trust.

## 6.11 Agenda mínima de evolución técnica

Prioridad alta: cablear elevación; tests CI; eliminar o cumplir promesa Spec folders. Prioridad media: Alembic; ampliar tools con paridad selectiva REST; mejorar CSP. Prioridad baja: UI de aprobación de `ElevationRequest`; métricas dashboard de bloqueos LogIA. Estas prioridades son propuestas de ingeniería derivadas de la evidencia, no features ya entregadas.
