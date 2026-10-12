
# Capítulo V. Pruebas, resultados y discusión

## 5.1 Estrategia de evaluación disponible

La evaluación del laboratorio no se estructura como un experimento estadístico con hipótesis nula y tamaño muestral humano. Se estructura como verificación de laboratorio mediante scripts ejecutables que ejercitan la API y, en algunos casos, el gateway. Esta sección describe **qué comprueban** los scripts y discute el significado de los escenarios A/B. **No se reportan tasas de éxito porcentuales** porque no forman parte de un informe de ejecución versionado en el repositorio; cualquier número inventado contaminaría la validez científica del documento.

## 5.2 `test_smoke.py`

Ubicación: `App/backend/test_smoke.py` (presente en ambos laboratorios).

Flujo observado en código:

1. Login como `docente1` / `Docente123!` y obtención de `access_token`.
2. `POST /api/v1/grades` con `partial1=5`, `partial2=6` e impresión de `needs_supplementary` y `average`.
3. Nuevo `POST` incluyendo `supplementary=8` e impresión de `final_grade` y `status`.
4. Login admin y `POST /api/v1/users/2/login-as` para verificar impersonación.

Interpretación: el script valida la cadena autenticación → reglas de notas (promedio bajo ⇒ necesita supletorio; con supletorio ⇒ estado final) → capacidad de impersonación administrativa. Su resultado depende de que existan esos usuarios y el curso/estudiante referenciados en la base local.

## 5.3 `test_visibility.py`

Flujo:

1. Admin lista términos y dashboard.
2. Estudiante `est0001` lista términos, grades y courses.
3. Docente `docente01` lista términos y courses.
4. Aserciones: admin ve 4 términos; estudiante ve 2 con códigos `2025-1` y `2025-2`; estudiante tiene grades > 0; imprime `VISIBILITY_OK`.

Interpretación: verifica el scoping SPEC-009 tras un seed coherente. Si el seed difiere, las aserciones fallarán; ello no implica por sí solo un defecto teórico de Zero Trust, sino dependencia del dataset.

## 5.4 `test_mysql.py`

Comprueba que la URI contiene `mysql`, que la página de login responde 200, que admin autentica, que el dashboard reporta estudiantes, y que un conjunto de GETs `/api/v1/...` responden 200. Incluye comprobaciones adicionales de flujo docente/estudiante en el resto del archivo. Es una prueba integral de conectividad y permisos básicos contra XAMPP/MySQL, no una batería de seguridad adversaria.

## 5.5 `scripts/validate_ai_chat.py`

Valida persistencia de conversaciones (SPEC-018/020): mensaje de chat, incremento de `message_count`, generación de reporte/artifact (o forzando `reports_generate`), y propiedades de URL firmada (`/api/v1/ai/artifacts/...` con `sig` y `expires`). También ejercita tools vía `execute_tool`. Requiere admin sembrado y, para el camino feliz de chat con LLM, disponibilidad del proveedor; el script contempla forzados locales cuando no hay artifacts.

## 5.6 `scripts/validate_dsml_parse.py`

Toma un sample de markup `<|DSML|...|>` con `users_list` y verifica `has_tool_markup`, `parse_dsml_tool_calls`, `parse_tool_calls` y limpieza `strip_tool_markup`. Es una prueba unitaria-funcional del parser SPEC-023, independiente de la red DeepSeek.

## 5.7 `scripts/validate_filters_export.py`

Recorre el catálogo `REPORT_CATALOG`, construye reporte de users filtrado por rol ADMIN, y descarga `.xlsx`/`.pdf` de múltiples tipos vía API admin, asertoando HTTP 200. Verifica también query params de filtro en users. Es evidencia de que el subsistema de reportes está cableado extremo a extremo en presencia de datos y permisos adecuados.

## 5.8 Resultados reportables sin invención

Lo que este estudio puede afirmar con rigor es:

1. Existen scripts de verificación con aserciones explícitas.
2. Cubren autenticación, notas, impersonación, visibilidad, MySQL, chat/artifacts, parseo DSML y exportaciones.
3. El éxito de cada ejecución es **condicional al entorno local** (seed, BD, secretos, red al proveedor).
4. No se dispone, en el material inspeccionado, de un informe CI consolidado con métricas agregadas; por tanto no se publican porcentajes.

## 5.9 Discusión del diseño A vs B

`laboratorioIA` introduce un interruptor experimental `AI_INSECURE_MODE` que, activado, desactiva anti-injection, intent guard, enforcement de permisos en executor, confirmación de mutaciones y restringe el filtrado de tools. El valor científico del escenario A no es “ser inseguro en producción”, sino permitir observar, en laboratorio, el contraste entre un agente mediatizado y un agente deliberadamente permisivo. El `.env.example` advierte el riesgo.

`laboratorioIB` modulariza el guard de intención NL en `ai_intent_guard.py`, con reglas para directorios y exportaciones institucionales y excepciones de “mi curso/mis estudiantes”. El valor del escenario B es mostrar una defensa pre-LLM alineada con mínimo privilegio semántico (no solo IAM de tool call), coherente con preocupaciones de Deng et al. (2025), Jeong y Yang (2025) y Xu et al. (2025).

Ambos escenarios comparten RBAC, visibility, gateway HANDLERS y LogIA. Por ello la comparación es de **régimen de guards del agente**, no de dos productos académicos distintos. Rose et al. (2020) y Syed et al. (2022) ayudarían a interpretar B como más cercano a verificación continua de intención/acceso, y A (modo inseguro) como condición de control negativo. Buck et al. (2021) recordarían que la adopción real exige gobernanza más allá del flag.

## 5.10 Relación con objetivos específicos

- OE1 (arquitectura/modelos): satisfecho por inspección (Cap. IV).
- OE2 (gateway): satisfecho por inspección de registry/executor/handlers/orchestrator.
- OE3 (mecanismos de seguridad del agente): satisfecho con matices A/B.
- OE4 (comparación IA/IB): satisfecho cualitativamente.
- OE5 (pruebas y límites): satisfecho al describir scripts sin inventar métricas, y al señalar parcialidades.

## 5.11 Limitaciones de la evaluación

1. **No adversariales sistemáticas:** no hay suite documentada de red team de prompts con dataset etiquetado.
2. **Heurísticas:** falsos positivos/negativos posibles en regex (Kang et al., 2023; Azad et al., 2024).
3. **Dependencia del LLM:** el comportamiento de tool calling varía con el modelo/prompt.
4. **Seeds acoplados:** aserciones de visibility asumen cardinalidades del seeder.
5. **Sin estadística inferencial:** no se estima efectividad poblacional de bloqueos.
6. **Sin usuarios reales:** no hay usabilidad ni aceptación medibles (y no se inventan).

## 5.12 Amenazas a la validez

**Validez interna:** cambios menores no documentados entre clones IA/IB podrían confundirse con el efecto del diferenciador; se mitigó listando archivos presentes/ausentes (`insecure_mode.py`, `ai_intent_guard.py`).

**Validez externa:** un instituto real con IdP, SIEM y PDP centralizado no es equivalente a este lab; Rose et al. (2020) describen un alcance mayor.

**Validez de constructo:** “Zero Trust” aquí operacionaliza un subconjunto (JWT + RBAC + gateway + logs). No incluye microsegmentación de red ni attestación de dispositivo.

**Confiabilidad:** la repetición de scripts depende de estado de BD; no se observó harness de aislamiento total por test.

**Validez ecológica:** el chat de laboratorio con datos sintéticos subestima presión operacional y abuso interno sofisticado (Shostack, 2014).

## 5.13 Discusión frente al estado del arte

El laboratorio ilustra, en software ejecutable, tensiones que Syed et al. (2022) y Buck et al. (2021) describen a nivel organizacional: es más fácil construir un asistente útil que gobernarlo. Kang et al. (2023) y Azad et al. (2024) predicen intentos de jailbreak; el código responde con bloqueos pre-LLM y registro. Deng et al. (2025) abogarían por capas; el gateway + intent + injection + RBAC es un apilamiento pragmático. Adahman et al. (2022) y Awan et al. (2023) justificarían el scoping académico. Vasović et al. (2026), Mawgoud et al. (2025), Kanaker et al. (2026), Gulyamov et al. (2026) y Geng et al. (2026) refuerzan que la contribución útil es un artefacto auditable, no una promesa de seguridad absoluta.

## 5.14 Hallazgos principales (cualitativos)

1. El Tool Gateway está implementado y es el PEP práctico del agente.
2. El modo inseguro de IA es un diferenciador experimental explícito.
3. El intent guard dedicado de IB es un diferenciador de modularización/defensa NL.
4. `privileges_request_elevation` permanece parcial al no estar en `HANDLERS`.
5. Spec folders están ausentes pese al README.
6. La batería de scripts cubre humo funcional, no eficacia estadística de seguridad.

## 5.15 Implicaciones prácticas para laboratorios académicos

Para programas de ciberseguridad, el artefacto permite prácticas de: (a) lectura de controles RBAC; (b) análisis de logs LogIA; (c) contraste seguro vs inseguro; (d) amenaza de confused deputy en agentes; (e) discusión de brecha Spec documentada vs código. No debe usarse como plantilla de producción sin cerrar las parcialidades del Capítulo VI.
