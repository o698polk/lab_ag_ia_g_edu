# K-002 — Architecture Designer

| Campo | Valor |
|---|---|
| Código | K-002 |
| Nombre | Architecture Designer |
| Fase primaria | F3 |
| Estado | Registered |
| Fecha registro | 2026-09-20 |
| Skill registradora | K-003 Skill Creator |

## Responsabilidad

Diseña C4, ERD, UML, secuencias, deployment y contratos Zero Trust.

## Contrato

Entradas: S03/S05/S09. Salidas: documentation/architecture/*. No escribe App.

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
