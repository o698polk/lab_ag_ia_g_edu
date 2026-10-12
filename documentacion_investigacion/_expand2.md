
## 1.13 Contexto institucional del problema (sin afirmar despliegue)

Las instituciones educativas digitalizan ventanillas académicas: inscripción, actas, asistencia, constancias. Cuando se añade un asistente conversacional, el personal tiende a formular pedidos ambiguos (“pásame el Excel de todos”). En un sistema sin Tool Gateway, ese pedido podría traducirse en consultas SQL amplias o en exportaciones sin chequeo. En el laboratorio, el mismo pedido se enfrenta a permisos, intent guard y, si procede, a denegación registrada. La relevancia no requiere afirmar que el software ya opera en una universidad real; basta con reconocer que el patrón de riesgo es verosímil en el sector (Adahman et al., 2022; Awan et al., 2023; Vasović et al., 2026).

## 1.14 Compatibilidad con lineamientos Zero Trust

Rose et al. (2020) enumeran principios: toda comunicación segura, sesión basada en identidad fuerte, políticas dinámicas, monitoreo. El laboratorio cubre de forma parcial identidad (JWT + roles), políticas (RBAC + guards) y monitoreo (AuditLog + LogIA). No cubre de forma demostrable inventario de dispositivos, posture checking, ni segmentación de red. Syed et al. (2022) clasificarían esto como adopción temprana/enfoque application-centric. Buck et al. (2021) explicarían por qué un proyecto académico elige ese recorte: costo y complejidad.

## 1.15 Riesgos específicos del dominio de calificaciones

Una mutación indebida de `grades_upsert` altera trayectorias académicas sintéticas en el lab y, en un sistema real, derechos estudiantiles. Por ello el diseño exige `grades.manage`, scoping de curso, respeto a `grades_closed` y confirmación. Kang et al. (2023) y Azad et al. (2024) advierten que un atacante podría intentar que el modelo “actúe como admin”; el bypass ADMIN existe en código, pero solo si el sujeto JWT es ADMIN, no porque el prompt lo declare. El orquestador, además, trata ciertos intentos de escalada narrativa como `privilege_escalation`.

## 4.32 Catálogo narrativo de tools de lectura

`careers_list` y `careers_get` exponen el catálogo de carreras con paginación y filtro `is_active`. `subjects_list` permite filtrar por `career_id`. `terms_list` aplica `visible_term_ids` fuera de modo inseguro, lo que conecta el gateway con SPEC-009. `courses_list` aplica `_course_scope` y añade `enrolled_count`. `students_list` restringe a estudiantes matriculados en cursos propios cuando hay ownership; `teachers_list` lista docentes si hay `teachers.view`. `enrollments_list` y `grades_list` / `attendance_list` combinan course scope con filtro adicional si el rol es STUDENT (solo su `student_id`). `users_list` soporta búsqueda por username/email/nombre. `roles_list` y `audit_logs_list` son superficies administrativas/de compliance. `reports_list_types` enumera tipos permitidos al usuario.

## 4.33 Catálogo narrativo de tools de mutación

`careers_create` / `careers_update` modifican el catálogo institucional. `enrollments_create` valida capacidad (`validate_course_capacity`) y unicidad de matrícula. `grades_upsert` es la tool de mayor sensibilidad académica cotidiana: upsert por par estudiante-curso, reglas de supletorio y ownership. `attendance_upsert` valida estados enumerados y ownership. `users_assign_roles` reemplaza el conjunto de roles del usuario objetivo, con protección a `is_protected` salvo ADMIN. Cada mutación genera `log_event` específico. El executor añade la barrera de confirmación en modo seguro.

## 4.34 Paginación y límites

`_paginate` acota `per_page` a un máximo de 100, mitigando enumeraciones masivas accidentales vía agent. No es un control antifraude completo, pero reduce respuestas enormes en demos.

## 4.35 Relación con reportes clásicos vs reportes AI

`services/reports.py` alimenta rutas `/api/v1/reports/*.xlsx|pdf` usadas por UI y por `validate_filters_export.py`. `services/ai_reports.py` alimenta artifacts del agente con tipos y formatos propios del catálogo AI. Ambos deben mantener coherencia de autorización; el modo inseguro relaja la visión del modelo sobre tipos disponibles, lo que nuevamente ilustra el rol del escenario A como control negativo.

## 4.36 Seed coherente y densidad de datos

`seed_coherent.py` en laboratorioIA define tipologías de staff (rector, auditor, coords, secretaria, tutor, itsupport) y volúmenes por carrera. El README IA cuantifica un dataset amplio (matrículas/notas/asistencias). Esa densidad permite pruebas de listados y reportes con resultados no triviales, y explica por qué `test_visibility.py` puede afirmar cardinalidades concretas. laboratorioIB documenta en README un conjunto demo más pequeño, aunque comparte estructura de seeders en su árbol.

## 4.37 Bootstrap de aplicación y CLI init-db

`create_app` registra blueprints y `init-db` crea tablas y ejecuta `seed_all`. `setup_mysql.py` asiste la recreación en XAMPP. El camino feliz de un investigador que clona el repo es: venv → requirements → `.env` → seed → `run.py` → http://127.0.0.1:5000. Esta reproducibilidad local es parte del aporte metodológico.

## 4.38 Frontend como cliente del gateway

`ai-chat.js` no ejecuta tools en el navegador; envía mensajes al backend. El browser nunca debería recibir la API key. Los artifacts se descargan por URL firmada. Este límite de confianza al cliente es coherente con Zero Trust application-centric (Rose et al., 2020) y con privacidad de secretos (Xu et al., 2025; Jeong & Yang, 2025).

## 5.21 Criterios de aceptación cualitativos derivados del código

Sin inventar métricas, sí es posible formular criterios de aceptación binarios locales: (C1) login admin retorna token; (C2) estudiante no ve todos los términos inactivos del seed coherente; (C3) markup DSML de users_list se parsea; (C4) tool desconocida produce `unknown_tool`; (C5) mutación sin confirmación produce `needs_confirm` en modo seguro; (C6) en IA con inseguro, los guards cortocircuitan a `None`/bypass. Estos criterios pueden usarse en rúbricas docentes.

## 5.22 Limitaciones al comparar IA vs IB en ejecución

Si un investigador activa inseguro en IA y compara contra IB seguro, observa diferencias de guards. Si ambos corren en configuración segura por defecto (`AI_INSECURE_MODE=0`), las diferencias se reducen a modularización del intent guard y a detalles de implementación de patrones. Por eso la comparación debe declarar el valor del flag. Omitirlo invalidaría la discusión A/B.

## 5.23 Amenazas a la validez re-evaluadas tras la inspección

La principal amenaza de constructo residual es etiquetar el sistema como “Zero Trust” a secas. Este documento usa deliberadamente “orientado a Zero Trust mediante Tool Gateway”. La principal amenaza interna es la deriva entre clones; se mitigó verificando presencia/ausencia de archivos clave. La principal amenaza externa es la extrapolación a producción; se mitiga en conclusiones y trabajo futuro. Shostack (2014) recomendaría mantener esta lista viva a medida que el código evolucione.

## 6.12 Contribución teórica modesta pero explícita

No se propone un nuevo formalismo de políticas. Se propone una evidencia de diseño: el Tool Gateway como PEP de agente en un SIS de laboratorio, con escenarios de relajación/refuerzo. Frente a Rose et al. (2020), es una instancia parcial. Frente a Deng et al. (2025), es un caso de estudio implementado. Frente a Adahman et al. (2022) y Awan et al. (2023), es un objeto tangible para educación en ciberseguridad.

## 6.13 Conclusión final ampliada

El software en `laboratorioIA` y `laboratorioIB` constituye una base seria para prácticas de autorización en sistemas con LLM. Su valor aumenta cuando se documenta sin mitomanía técnica: hay gateway, hay logs, hay RBAC, hay A/B; no hay Spec folders, no hay PDP/PAP, no hay estadísticas de eficacia, y la elevación está a medio cablear. Esa frontera nítida entre hechos y deseos es la condición de posibilidad de investigación reproducible en ciberseguridad aplicada.
