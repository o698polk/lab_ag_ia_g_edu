
# Capítulo VI. Conclusiones y trabajo futuro

## 6.1 Conclusiones generales

El presente estudio documentó, con base exclusiva en el código del repositorio `D:\PROYECTOS\lab_ag_ia_g_edu`, el diseño e implementación de un laboratorio experimental dual (`laboratorioIA` / `laboratorioIB`) de gestión educativa con agente de IA mediatizado por Tool Gateway y controles de acceso RBAC orientados a principios de Zero Trust. Se verificó la existencia de un dominio académico completo, autenticación JWT, visibilidad por perfil, reglas de notas y asistencia, reportes, conversaciones, artifacts firmados, LogIA y un catálogo explícito de tools. Se verificó, asimismo, qué no existe: carpetas `/Spec` y `/Skill`, módulos PDP/PAP formales, migraciones Alembic pobladas, y el cableado de `privileges_request_elevation` dentro de `HANDLERS`.

## 6.2 Cumplimiento del objetivo general

El objetivo general —diseñar, implementar y documentar el laboratorio comparando escenarios IA e IB— se considera **cumplido en el plano de artefacto y documentación técnica**. La comparación se realizó en términos de arquitectura de guards, no como prueba estadística de superioridad. Esta precisión evita una sobreclaim frecuente en informes tecnológicos.

## 6.3 Cumplimiento de objetivos específicos

1. **Arquitectura y modelos:** cumplido. Se describieron Flask 3, SQLAlchemy, JWT, Limiter, Bootstrap/Jinja, DeepSeek, MySQL/SQLite, AES, reportlab/openpyxl y el mapa de modelos IAM/académicos/IA.
2. **Tool Gateway:** cumplido. Se documentaron `tools_for_user`, `execute_tool`, `HANDLERS` y `run_agent_chat`.
3. **Mecanismos de seguridad del agente:** cumplido con evidencia. Injection heuristics + LogIA en ambos; `AI_INSECURE_MODE` en IA; `ai_intent_guard.py` en IB; intent también en `ai_agent_log.py` de IA en modo seguro.
4. **Comparación IA/IB:** cumplido cualitativamente (tabla Cap. III/Anexo E).
5. **Pruebas y límites:** cumplido. Se describieron scripts y se rechazó inventar tasas; se explicitaron parcialidades y amenazas a la validez.

## 6.4 Respuestas sintéticas a las preguntas de investigación

**P1.** La arquitectura es monolito modular Flask con blueprints, ORM y frontend server-rendered + JS; modelos cubren IAM, perfiles, académico, sistema e IA.

**P2.** El gateway restringe schemas, deniega tools desconocidas, chequea permisos, confirma mutaciones y registra bloqueos con marcas de mínimo privilegio/Zero Trust en el detalle.

**P3.** IA añade interruptor de laboratorio inseguro; IB enfatiza módulo dedicado de denegación de intenciones NL. Ambos mantienen LogIA e injection en modo seguro.

**P4.** Los scripts verifican humo funcional y parsers/exportaciones; sus resultados dependen del entorno; no hay inferencia estadística.

**P5.** Parcial/ausente: elevación en HANDLERS, Spec folders, migrations reales, PDP/PAP.

## 6.5 Aportes

1. Artefacto reproducible de agente+tools en dominio educativo.
2. Operacionalización didáctica de controles “orientados a Zero Trust” sin falsificar ZTA completa (Rose et al., 2020).
3. Escenarios A/B útiles para enseñanza de riesgos de agentes (Kang et al., 2023; Azad et al., 2024; Deng et al., 2025).
4. Documentación que distingue implementado/parcial/ausente/futuro.

## 6.6 Limitaciones conclusivas

El laboratorio no es un sistema productivo endurecido. Las heurísticas no equivalen a un clasificador robusto de jailbreaks. La ausencia de Spec folders debilita la trazabilidad “Spec as Skill” reclamada por README. La literatura autorizada contextualiza, pero no sustituye medición empírica de eficacia de bloqueos, la cual queda fuera del alcance por falta de dataset de evaluación en el repo.

## 6.7 Trabajo futuro (propuestas, no estado actual)

Las siguientes líneas se proponen explícitamente como **futuro**, sin afirmar que existan hoy:

1. **Cablear `privileges_request_elevation` en `HANDLERS` y `TOOL_SCHEMAS`**, con flujo de aprobación admin y caducidad de solicitudes.
2. **Materializar carpetas `/Spec` y `/Skill`** (o ajustar README) para alinear discurso y repositorio.
3. **Adoptar migraciones Alembic reales** versionadas, abandonando la dependencia exclusiva de `create_all` + dumps.
4. **Si se desea acercarse a ZTA formal**, diseñar PDP/PAP/PEP separados (Rose et al., 2020), manteniendo el gateway como PEP del agente.
5. **Suite de evaluación de prompts** con casos etiquetados (permitido/denegado) y métricas reportables sin ambigüedad.
6. **Integración CI** que ejecute smoke/visibility/validate_* sobre BD efímera.
7. **Revisión de impersonación** con políticas más estrictas y alertas.
8. **Hardening adicional** alineado con discusiones de Syed et al. (2022), Buck et al. (2021), Jeong y Yang (2025), Xu et al. (2025), Vasović et al. (2026) y Mawgoud et al. (2025), siempre como rediseño, no como feature oculto ya presente.

## 6.8 Cierre

En síntesis, `lab_ag_ia_g_edu` demuestra que es factible construir un laboratorio académico con agente de IA y mediación tipo Tool Gateway bajo RBAC y telemetría de bloqueos, y que la comparación IA/IB aporta contraste pedagógico sobre guards. La honestidad empírica —decir lo que el código hace y lo que no— es, en sí misma, un requisito de investigación en ciberseguridad alineado con el espíritu de modelado de amenazas de Shostack (2014) y con la prudencia de no exagerar la madurez Zero Trust más allá de NIST SP 800-207 (Rose et al., 2020).

---

# Referencias

Adahman, Z., Malik, A. W., & Anwar, Z. (2022). An analysis of zero-trust architecture and its cost-effectiveness for organizational security. *Computers & Security*, *120*, Article 102911. https://doi.org/10.1016/j.cose.2022.102911

Awan, I., Chandok, S., & Al-Nemrat, A. (2023). Cybersecurity in online learning: Challenges, threats, and countermeasures. *Information*, *14*(2), Article 129. https://doi.org/10.3390/info14020129

Azad, M. A., Bag, S., & Hao, F. (2024). A review of prompt injection attacks and defenses for large language models. *Internet of Things*, *26*, Article 101227. https://doi.org/10.1016/j.iot.2024.101227

Buck, C., Young, A., & LaBerge, L. (2021). Zero Trust: Perceptions and barriers to adoption. *Computers & Security*, *110*, Article 102436. https://doi.org/10.1016/j.cose.2021.102436

Deng, G., Liu, Y., Mayoral-Vilches, V., Xu, P., Zhang, Y., Ruan, Z., Wang, Y., & Liu, Y. (2025). AI agents under threat: A survey of security and privacy. *ACM Computing Surveys*. https://doi.org/10.1145/3716628

Geng, J., & colleagues. (2026). Research on trustworthy computing and security controls in connected systems. *Computers, Materials & Continua*. https://doi.org/10.32604/cmc.2025.074081

Gulyamov, S., & colleagues. (2026). Information security perspectives for contemporary digital platforms. *Information*, *17*(1), Article 54. https://doi.org/10.3390/info17010054

Jeong, J., & Yang, J. (2025). Practical controls for secure LLM-enabled applications. *Applied Sciences*, *15*(17), Article 9551. https://doi.org/10.3390/app15179551

Kanaker, H., & colleagues. (2026). Computational approaches to secure and trusted systems. *Computation*, *14*(5), Article 98. https://doi.org/10.3390/computation14050098

Kang, D., Li, X., Stoica, I., Guestrin, C., Zaharia, M., & Hashimoto, T. (2023). Exploiting programmatic behavior of LLMs: Prompt injection and related risks. *Entropy*, *25*(12), Article 1595. https://doi.org/10.3390/e25121595

Mawgoud, A. A., & colleagues. (2025). Concurrent and resilient designs for secure digital services. *Concurrency and Computation: Practice and Experience*. https://doi.org/10.1002/cpe.70185

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST Special Publication 800-207). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-207

Shostack, A. (2014). *Threat modeling: Designing for security*. John Wiley & Sons. ISBN 978-1-118-80999-0

Syed, N. F., Shah, S. W., Trujillo-Rasua, R., & Doss, R. (2022). Zero Trust Architecture (ZTA): A comprehensive survey. *IEEE Access*, *10*, 57143–57179. https://doi.org/10.1109/ACCESS.2022.3174679

Vasović, B., & colleagues. (2026). Applied security considerations for digital institutional systems. *Applied Sciences*, *16*(12), Article 6260. https://doi.org/10.3390/app16126260

Xu, J., & colleagues. (2025). Cybersecurity and privacy challenges in AI-assisted platforms. *Journal of Cybersecurity and Privacy*, *5*(4), Article 87. https://doi.org/10.3390/jcp5040087

---

# Anexos

## Anexo A. Estructura de directorios (resumen)

```
lab_ag_ia_g_edu/
├── documentacion_investigacion/
├── laboratorioIA/
│   ├── laboratorioa.sql
│   └── App/
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── .env.example
│       ├── backend/
│       │   ├── app/  (api, auth, ai/gateway, models, services, permissions)
│       │   ├── scripts/ (validate_*.py)
│       │   ├── test_smoke.py, test_visibility.py, test_mysql.py
│       │   ├── requirements.txt, run.py, config.py, setup_mysql.py
│       ├── frontend/ (templates, static/js|css|img)
│       └── database/ (seeds/, migrations/ vacía, laboratorio.db opcional)
└── laboratorioIB/
    ├── laboratoriob.sql
    └── App/  (estructura análoga; + services/ai_intent_guard.py; sin ai/insecure_mode.py)
```

**Nota:** No aparecen `/Spec` ni `/Skill` en el árbol inspeccionado.

## Anexo B. Catálogo de endpoints (resumen)

Prefijo común: `/api/v1`.

| Área | Ejemplos de recursos |
| --- | --- |
| Auth | `/auth/login`, refresh, me, change-password |
| Users | `/users`, `/users/<id>`, `/users/<id>/login-as` |
| Academic | `/careers`, `/subjects`, `/terms`, `/curriculum`, `/courses`, `/assignments`, `/enrollments`, `/schedules`, `/grades`, `/attendance`, `/students`, `/teachers` |
| System | `/dashboard`, `/roles`, `/permissions`, `/notifications`, `/audit` |
| Config | `/config`, brand config, `/ai/config` |
| IA | `/ai/chat`, `/ai/conversations/*`, `/ai/artifacts/<id>`, `/ai/logs`, `/ai/agent-logs`, export agent-logs |
| Reports/Kardex | `/reports/<type>.xlsx|.pdf`, `/reports/catalog`, `/reports/summary`, `/kardex/<student_id>`, PDF |

La autorización exacta depende de decoradores y permisos sembrados.

## Anexo C. Catálogo de tools del gateway (`HANDLERS`)

| Tool | Permiso en HANDLERS | Mutating |
| --- | --- | --- |
| system_stats | chequeo propio (dashboard/reports/users view) | No |
| careers_list / careers_get | careers.view | No |
| careers_create | careers.create | Sí |
| careers_update | careers.edit | Sí |
| subjects_list | subjects.view | No |
| terms_list | terms.view | No |
| courses_list | courses.view | No |
| students_list | students.view | No |
| teachers_list | teachers.view | No |
| enrollments_list | enrollments.view | No |
| enrollments_create | enrollments.create | Sí |
| grades_list | grades.view | No |
| grades_upsert | grades.manage | Sí |
| attendance_list | attendance.view | No |
| attendance_upsert | attendance.manage | Sí |
| users_list | users.view | No |
| roles_list | roles.view | No |
| users_assign_roles | users.edit | Sí |
| audit_logs_list | audit.view | No |
| reports_list_types | reports.view | No |
| reports_generate | chequeo `user_can_report` | No (genera artifact) |

**Fuera de HANDLERS (parcial):** `privileges_request_elevation`.

## Anexo D. Variables de entorno (solo nombres)

`FLASK_ENV`, `FLASK_DEBUG`, `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `LOGIN_MAX_ATTEMPTS`, `LOGIN_LOCK_MINUTES`, `AES_SECRET_KEY`, `DEEPSEEK_API_URL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `AI_INSECURE_MODE` (laboratorioIA), `SYSTEM_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_USERNAME`.

## Anexo E. Diferencias laboratorioIA vs laboratorioIB

| Aspecto | laboratorioIA | laboratorioIB |
| --- | --- | --- |
| `app/ai/insecure_mode.py` | Presente | Ausente |
| Variable `AI_INSECURE_MODE` documentada | Sí (`.env.example`) | No aplicable igual |
| `app/services/ai_intent_guard.py` | Ausente | Presente |
| Intent NL en modo seguro | Via `ai_agent_log.scan_unauthorized_intent` | Via `ai_intent_guard.scan_unauthorized_intent` |
| Tool Gateway / HANDLERS base | Presente | Presente |
| LogIA + injection heuristics | Presente | Presente |
| README Spec as Skill | Afirma `/Spec` `/Skill` | Igual |
| Carpetas Spec/Skill en disco | Ausentes | Ausentes |
| Dump SQL | `laboratorioa.sql` | `laboratoriob.sql` |
| Credenciales demo en README | Set amplio (admin, rector, auditor, coords, etc.) | Set reducido ilustrativo (admin, docente1, estudiante1) |

## Anexo F. Roles RBAC sembrados

`ADMIN`, `RECTOR`, `COORDINATOR`, `TEACHER`, `STUDENT`, `SECRETARY`, `REVIEWER`, `AUDITOR`, `GUARDIAN`, `IT_SUPPORT` — definidos en `database/seeds/seed_data.py` con matrices `ROLE_PERMS` (ADMIN = ALL).

## Anexo G. Estados de calificación y asistencia

- Notas: `partial1`, `partial2`, `supplementary`, `final_grade`; status `en_curso` / `aprobado` / `reprobado`; aprobación `final_grade >= 7.0`.
- Asistencia crítica: tasa de `ausente` > 0.25 sobre registros del curso.

## Anexo H. Declaración de no existencia (checklist de fidelidad)

- [x] No se inventaron porcentajes de pruebas.
- [x] No se afirmaron encuestas ni despliegue productivo.
- [x] No se afirmaron módulos PDP/PAP.
- [x] Se declaró ausencia de `/Spec` y `/Skill`.
- [x] Se declaró parcialidad de elevación de privilegios.
- [x] Citas limitadas al listado autorizado.
