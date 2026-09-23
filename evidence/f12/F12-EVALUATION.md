# F12 — Informe de evaluación (K-011)

| Campo | Valor |
|---|---|
| Fase | F12 — Evaluation |
| Skill | K-011 Evaluator |
| Spec | S12 |
| Fecha | 2026-09-20 |
| Entrada | Gate F11 **GO** · deploy `127.0.0.1:8000` |

Dimensiones PromptMaster F12: performance, security, usability, coverage, errors, technical debt.

---

## 1. Performance (local)

| ID | Meta | Medición | Cumple |
|---|---|---|---|
| MQ-R01 p95 login | &lt; 500 ms | **431.87 ms** (n=8, HTTP 200) | ✅ |
| MQ-R02 p95 get grades | &lt; 500 ms | **33.61 ms** (n=30, `GET /students/1/grades` admin, HTTP 200) | ✅ |
| MQ-R03 disponibilidad | demo sin crash | health 200 · login 200 · grades 200 · sin 5xx en la muestra | ✅ |

Fuente: `evidence/f12/perf.json`. Muestra de login acotada a 8 para no disparar el rate limit (10/60 s).

---

## 2. Security

| ID | Meta | Resultado | Cumple |
|---|---|---|---|
| MQ-S01 críticos | 0 | SEC-01 / F8: ninguno abierto | ✅ |
| MQ-S02 IDOR | 100% DENY en casos de prueba | tests security + evaluation | ✅ |
| MQ-S03 IA tool sensible | 100% DENY | BL-O6-007 | ✅ |
| MQ-S04 secretos en repo | 0 | `.env` fuera de git | ✅ |
| MQ-S05 audit ops sensibles | P0 cubierto en tests | audit ≠ history | ✅ |
| MQ-S06 ADMIN sin permiso | DENY | tests IAM | ✅ |

Rate limit de login observado en ráfaga (429 `RATE_LIMITED`): comportamiento esperado en `APP_ENV=local`.

---

## 3. Coverage y pruebas

| ID | Meta | Resultado | Cumple |
|---|---|---|---|
| MQ-Q01 líneas | ≥ 80% | **85.65%** (F10, 2309/2696) | ✅ |
| MQ-Q02 ramas | ≥ 70% | global diferido | ⚠ ADR-013 |
| MQ-Q03 suites | 4 | unit, integration, security, e2e | ✅ |
| MQ-Q04 authz | ≥ 12 | security + PDP + zero trust + IDOR | ✅ |
| MQ-Q05 flaky | 0 | última suite completa 74 passed; re-run F12 en `pytest-f12.txt` | ✅ |

---

## 4. Producto y proceso

| ID | Resultado | Cumple |
|---|---|---|
| MQ-P01 RF P0 | baseline salvo CRUD create de rol | ⚠ |
| MQ-P02 HU P0 | CA con tests | ✅ |
| MQ-P03 módulos baseline | IAM, académico, operación, evaluación, plataforma, ZT | ✅ |
| MQ-D01 cambios sin Spec | 0 críticos | ✅ |
| MQ-D02 tareas sin Skill | 0 | ✅ |
| MQ-D03 gates saltados | 0 (F1→F12) | ✅ |
| MQ-D04 spec drift crítico | 0 al F10 | ✅ |

---

## 5. Usabilidad

| ID | Meta | Resultado | Cumple |
|---|---|---|---|
| MQ-U01 | Login + nota + asistencia en desktop | Login y dashboard en `/ui/`. Nota y asistencia solo por API, no en la UI | ⚠ P1 |
| MQ-U02 | Viewport móvil sin bloqueo total | `viewport` + Bootstrap 5; no hay flujo móvil de notas | ⚠ |

---

## 6. Errores

En la sesión de medición F12 no hubo respuestas 5xx en health, login (muestra acotada) ni grades. El 429 de login es control de abuso, no fallo de aplicación.

---

## 7. Deuda técnica (aceptada en Gate F10)

1. Recuperación de contraseña (P1) no implementada.
2. UI de notas y asistencia (P1) no implementada; `/ui/` es dashboard mínimo.
3. Export PDF de reportes (P2) responde 501.
4. API de alta/baja de roles incompleta (seed y asignación sí).
5. Cobertura de ramas global &lt; 70% — ADR-013; ruta crítica Zero Trust cubierta.
6. Alcance de publicación: solo `127.0.0.1` (ADR-009).

---

## 8. Recomendación del Evaluator (no vinculante)

```text
ACEPTAR CIERRE CONDICIONADO del laboratorio PolkDev F1–F12
Condiciones ya aceptadas en F10: gaps P1/P2, ADR-013, sin Internet
```

La aceptación del cierre es **exclusivamente humana**.

---

## 9. Addendum post-PromptMaster UX (2026-09-22)

No cambia la decisión humana del Gate F12. Actualiza el estado de deuda **después** de F2–F10 frontend:

| Ítem F12 | Estado actual |
|---|---|
| UI notas (carrera→periodo→paralelo) | Cerrada — `/ui/pages/notas/` |
| UI asistencia | Cerrada — `/ui/pages/asistencia/` |
| UI catálogos por entidad | Cerrada — `/ui/pages/catalogos/` |
| UI reportes / usuarios / avisos / asistente | Cerrada |
| a11y + responsive + shims legacy | Cerrada — `evidence/verify/UX-F10-CHECKLIST.md` |
| Recuperación de contraseña | Sigue abierta (sin endpoint) |
| Export PDF | Sigue 501 (P2) |
