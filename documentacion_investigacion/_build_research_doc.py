# -*- coding: utf-8 -*-
"""Genera el documento de investigacion a partir de evidencia del codigo."""
from pathlib import Path

OUT = Path(r"D:\PROYECTOS\lab_ag_ia_g_edu\documentacion_investigacion\proyecto_investigacion_lab_ag_ia_g_edu.md")
WC = Path(r"D:\PROYECTOS\lab_ag_ia_g_edu\documentacion_investigacion\_wordcount.txt")

parts = []

def add(s):
    parts.append(s if s.endswith("\n") else s + "\n")

add("""# Portada / datos del estudio

**Título:** Diseño e implementación de un laboratorio experimental de gestión educativa con agente de inteligencia artificial y control de acceso orientado a Zero Trust mediante Tool Gateway: comparación de escenarios laboratorioIA y laboratorioIB

**Tipo de documento:** Informe técnico de investigación aplicada (desarrollo experimental de laboratorio)

**Ámbito del artefacto de software:** Repositorio local `D:\\\\PROYECTOS\\\\lab_ag_ia_g_edu`, con dos aplicaciones Flask paralelas (`laboratorioIA` y `laboratorioIB`) bajo `App/backend`

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
""")
print("part0", len(parts[0].split()))
OUT.write_text(parts[0], encoding="utf-8")
print("wrote front", OUT.exists(), OUT.stat().st_size)
