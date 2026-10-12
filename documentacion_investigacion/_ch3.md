
# Capítulo III. Metodología

## 3.1 Enfoque general

El estudio adopta un enfoque de investigación aplicada basada en diseño e implementación de software, complementado con experimentación de laboratorio tipo A/B entre dos despliegues locales (`laboratorioIA` y `laboratorioIB`). No se trata de un ensayo clínico, ni de una encuesta, ni de un experimento aleatorizado con inferencia estadística. La unidad de análisis es el propio sistema de software y su comportamiento verificable mediante inspección de código y scripts de humo/validación.

## 3.2 Tipo de investigación

Se clasifica como investigación tecnológica / desarrollo experimental de laboratorio. El producto es un artefacto ejecutable y documentado. La comparación IA vs IB es cualitativa-estructural (presencia/ausencia de módulos y flags, diferencias de guards) y, cuando se ejecutan scripts, operacional (códigos HTTP, aserciones locales), sin reportar aquí tasas agregadas inventadas.

## 3.3 Población, muestra y datos

No hay población humana de estudio. Los datos son sintéticos generados por seeds (`seed_data.py`, `seed_coherent.py`, `seed_massive.py`) y dumps SQL (`laboratorioa.sql`, `laboratoriob.sql`). El README de `laboratorioIA` describe un dataset demo amplio (carreras, docentes, estudiantes, matrículas, asistencias) tras `seed_coherent`. El uso de datos sintéticos mitiga riesgos éticos de privacidad real (Adahman et al., 2022; Awan et al., 2023).

## 3.4 Procedimiento Spec-as-Skill: afirmación versus evidencia

Los README de ambas aplicaciones afirman: “Construido con metodología Spec as Skill (ver `/Spec` y `/Skill`)”. El CHANGELOG mapea acciones a identificadores `SPEC-001` … y skills asociados en las versiones 1.0.0 y 1.1.0. Además, comentarios en el código referencian SPEC-016 a SPEC-031 (gateway, conversaciones, reportes, LogIA, intent guard, modo inseguro, etc.).

**Hallazgo metodológico crítico:** al inspeccionar el repositorio, las carpetas `/Spec` y `/Skill` **no están presentes**. Por tanto, este estudio trata Spec-as-Skill como una metodología *reclamada* y parcialmente trazable vía CHANGELOG y comentarios, pero **no** como un cuerpo de especificaciones versionadas disponible en el árbol de directorios. Documentar lo contrario violaría la regla de fidelidad empírica.

## 3.5 Diseño de escenarios A/B

| Dimensión | laboratorioIA | laboratorioIB |
| --- | --- | --- |
| App Flask académica | Sí | Sí |
| Tool Gateway + HANDLERS | Sí | Sí |
| LogIA / injection heuristics | Sí | Sí |
| `insecure_mode.py` / `AI_INSECURE_MODE` | Sí (diferenciador) | No (archivo ausente) |
| `ai_intent_guard.py` dedicado | No (intent en `ai_agent_log.py`) | Sí (diferenciador) |
| Base demo / seeds | Sí | Sí (credenciales demo más reducidas en README IB) |

El diseño experimental consiste en mantener un núcleo funcional común y variar el régimen de guards del agente. En IA, el flag `AI_INSECURE_MODE` permite desactivar anti-injection, intent guard, chequeo de permisos en executor y confirmación de mutaciones. En IB, el énfasis documental y modular está en el guard de intención NL dedicado. Ambos permanecen laboratorios locales, no producción.

## 3.6 Técnicas de recolección de evidencia

1. **Inspección estática del código:** modelos, APIs, gateway, servicios, configuración, seeds.
2. **Inspección de estructura de directorios:** verificación de ausencia de Spec/Skill y emptiness de migrations.
3. **Revisión de scripts de prueba:** lectura de aserciones y flujos (qué comprueban).
4. **Revisión de documentación interna del repo:** README, CHANGELOG, `.env.example`.
5. **No se utilizaron:** encuestas, focus groups, métricas de producción, pruebas de penetración ofensivas documentadas como resultado cuantitativo.

## 3.7 Instrumentos de verificación existentes en el repositorio

- `test_smoke.py`: login docente, upsert de notas (promedio bajo y con supletorio), impersonación admin `login-as`.
- `test_visibility.py`: diferencias de periodos visibles admin vs estudiante vs docente; aserciones sobre conteos esperados tras seed.
- `test_mysql.py`: comprobaciones de URI MySQL, login, dashboard y GETs de módulos.
- `scripts/validate_ai_chat.py`: persistencia de conversación, chat, artifacts y URLs firmadas.
- `scripts/validate_dsml_parse.py`: parseo de markup DSML a tool calls.
- `scripts/validate_filters_export.py`: catálogo de reportes y exportación xlsx/pdf.

Los resultados de ejecución dependen de: base sembrada, coincidencia de usernames/passwords, disponibilidad de MySQL o SQLite, y, para chat real con LLM, API key DeepSeek. Este informe **no inventa** porcentajes de paso.

## 3.8 Análisis de datos

El análisis es descriptivo-analítico: se mapean componentes a objetivos, se contrastan escenarios, se clasifica el estado (implementado/parcial/ausente/futuro) y se discuten amenazas a la validez. No se aplican pruebas t, ANOVA, chi-cuadrado ni modelos de regresión. La ausencia de estadística inferencial es una decisión metodológica coherente con el tipo de evidencia disponible.

## 3.9 Consideraciones éticas

Se utilizan datos sintéticos. Las credenciales demo aparecen en README (práctica habitual en labs) y deben rotarse fuera del laboratorio. El modo `AI_INSECURE_MODE` está documentado como peligroso fuera de pruebas locales. No se procesan datos personales reales de estudiantes. La investigación no induce daño a terceros; su riesgo principal sería el mal uso del laboratorio como base de un despliegue inseguro, lo cual se mitiga explícitamente en la documentación de variables de entorno.

## 3.10 Validez y amenazas metodológicas (preview)

Amenazas a la validez interna: diferencias menores entre clones IA/IB más allá del diferenciador declarado; dependencia de seeds. Amenazas a la validez externa: no generalizable a instituciones reales sin rediseño. Amenazas a la validez de constructo: llamar “Zero Trust” a un subconjunto de controles puede sobreinterpretarse; por ello se usa la fórmula “orientado a Zero Trust”. Amenazas a la confiabilidad: scripts no empaquetados como suite CI en el material inspeccionado. Estas amenazas se retoman en el Capítulo V.

## 3.11 Criterios de inclusión de hallazgos

Solo se reportan elementos con evidencia en archivos del repositorio. Los identificadores SPEC se usan como etiquetas de trazabilidad encontradas en comentarios/CHANGELOG, no como prueba de que exista un documento Spec externo. Las propuestas de PDP/PAP, Alembic real y cableado de elevación se reservan a trabajo futuro.

## 3.12 Procedimiento de documentación

La documentación se elaboró en tercera persona, español formal, APA 7, citando únicamente las fuentes autorizadas. Cada afirmación arquitectónica se ancla a rutas de archivo (`App/backend/app/...`). Los diagramas Mermaid del Capítulo IV son reconstrucciones analíticas del flujo real, no copias de un especificado ausente.
