# K-023 — Reporting Engineer

| Campo | Valor |
|---|---|
| Código | K-023 |
| Nombre | Reporting Engineer |
| Fase primaria | F6 |
| Estado | Registered |
| Fecha registro | 2026-09-20 |
| Skill registradora | K-003 Skill Creator |

## Responsabilidad

Reportes HTML/CSV/JSON/(PDF), report_logs.

## Contrato

Entradas: RF-REP. Salidas: reporting services + UI export.

## Reglas

- Toda acción debe citar Spec + esta Skill + Fase PolkDev.
- No saltar gates.
- No modificar App fuera de la responsabilidad de esta Skill.
- Deny by Default / Zero Trust cuando aplique a seguridad.

## Entradas típicas

- Artefactos Spec/Architecture relacionados
- Ítems de backlog asignados en skills/01-BACKLOG-MATRIX.md

## Salidas típicas

- Entregables de su dominio con trazabilidad RF/HU/BL/TEST

## Prohibiciones

- Crear funcionalidad no especificada
- Guardar secretos en código
- Bypass de PDP/Gateway en rutas sensibles (si interactúa con AuthZ/IA)
