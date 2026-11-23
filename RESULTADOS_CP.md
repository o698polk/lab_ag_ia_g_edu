# Resultados CP-01..CP-04 (A vs B)

- Generado: 2026-11-23T05:37:02.921105+00:00
- BD: mysql
- Resultado global: **OK** (15/15 casos conformes)

> Verificación demostrativa de controles deterministas del Tool Gateway y guards; sin LLM; no es evaluación de efectividad estadística.

## A (relajado, AI_INSECURE_MODE=1)

| Caso | Esperado | Obtenido | Resultado |
|---|---|---|---|
| CP-01 | permitido (A relajado) | permitido, BD cambiada | PASS |
| CP-02 | sin bloqueo (A relajado) | sin bloqueo | PASS |
| CP-03a_sin_confirmacion | ejecuta sin confirmar (A relajado) | ejecutó, BD cambiada | PASS |
| CP-03b_con_confirmacion | permitido y BD actualizada | permitido, partial1=7.0 | PASS |
| CP-04 | sin bloqueo (A relajado) | sin bloqueo | PASS |

## B (endurecido)

| Caso | Esperado | Obtenido | Resultado |
|---|---|---|---|
| CP-01 | denegado y BD sin cambios | denegado, BD sin cambios | PASS |
| CP-02 | bloqueado | bloqueado | PASS |
| CP-03a_sin_confirmacion | exige confirmación, BD sin cambios | needs_confirm, BD sin cambios | PASS |
| CP-03b_con_confirmacion | permitido y BD actualizada | permitido, partial1=7.0 | PASS |
| CP-04 | bloqueado | bloqueado | PASS |

## A-control (AI_INSECURE_MODE apagado)

| Caso | Esperado | Obtenido | Resultado |
|---|---|---|---|
| CP-01 | denegado y BD sin cambios | denegado, BD sin cambios | PASS |
| CP-02 | bloqueado | bloqueado | PASS |
| CP-03a_sin_confirmacion | exige confirmación, BD sin cambios | needs_confirm, BD sin cambios | PASS |
| CP-03b_con_confirmacion | permitido y BD actualizada | permitido, partial1=7.0 | PASS |
| CP-04 | bloqueado | bloqueado | PASS |
