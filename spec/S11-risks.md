# S11 — Riesgos

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F2 — SPEC |
| Skill | K-001 Spec Builder |
| Fecha | 2026-09-20 |

Escala: Impacto / Probabilidad = **A** Alta · **M** Media · **B** Baja  
Prioridad: Impacto × Probabilidad (cualitativa)

---

## 1. Registro de riesgos

| ID | Riesgo | Imp. | Prob. | Mitigación | Contingencia | Owner |
|---|---|---|---|---|---|---|
| RK-01 | Código prematuro sin Spec/Gate | A | M | PromptMaster + bloqueos PolkDev | Rollback de cambios no anclados | K-012 / PO |
| RK-02 | Privilege escalation / IDOR en notas | A | M | ABAC + tests seguridad O4/O6 | Parche + audit forensics | K-016/K-007 |
| RK-03 | IA bypasea autorización | A | M | Gateway obligatorio + DENY default | Deshabilitar tools sensibles | K-019/K-018 |
| RK-04 | ADMIN omnipotente implícito | A | M | ADR-004; permisos explícitos | Revisar matriz y policies | K-020 |
| RK-05 | Secretos en Git | A | B | `.gitignore` + `.env.example` | Rotar secretos | K-004 |
| RK-06 | Periodos CLOSED editables | A | M | RF-TRM-002 + tests | Revert + auditoría | K-017 |
| RK-07 | Subestimar PAP/PDP | A | A | Diseño en F3; BL-O6 temprano en arquitectura | Spike técnico en F5 | K-002/K-020 |
| RK-08 | Alcance académico excesivo | M | A | Prioridad P0/P1/P2 en S05/S06 | Diferir P2 | K-012 |
| RK-09 | Entorno MySQL/XAMPP inestable | M | M | Checklist F5 + scripts | Docker MySQL solo con ADR | K-004/K-014 |
| RK-10 | Cobertura &lt; umbral | M | M | Tests desde O1 | Ampliar F7 | K-006 |
| RK-11 | Proveedor LLM no disponible | M | M | ADR-011 + mock | Modo degradado solo consulta mock | K-018 |
| RK-12 | Drift Spec vs código | M | M | Trazabilidad RF→HU→BL→TEST | Gate F10 | K-009 |
| RK-13 | Conflictos de horario no detectados | M | M | RF-SCH-001 | Corrección + alerta | K-017 |
| RK-14 | Soft delete mal filtrado (datos “fantasma”) | M | M | Estándar repositorio | Fix queries | K-014 |
| RK-15 | Publicación accidental a red | A | B | Bind 127.0.0.1; ADR-009 | Apagar servicio + revisión | K-010 |

---

## 2. Riesgos aceptados conscientemente (baseline)

| ID | Nota |
|---|---|
| RK-08 | Se acepta backlog amplio documentado; ejecución por oleadas |
| RK-11 | Mock aceptable en laboratorio hasta ADR-011 cerrado |

---

## 3. Disparadores de replanificación

- Gate rechazado  
- Hallazgo de seguridad crítico abierto &gt; 1 ciclo  
- Cambio de stack (requiere nuevo ADR)  
- Solicitud de roles extendidos sin Spec  

---

## 4. Relación con S08 / S12

- Riesgos de calendario → S08 §6  
- Riesgos de calidad/seguridad → métricas S12 y Gate F8  
