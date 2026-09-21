# K-006 — Test Engineer

| Campo | Valor |
|---|---|
| Código | K-006 |
| Nombre | Test Engineer |
| Fase primaria | F7 |
| Estado | Registered |
| Fecha registro | 2026-09-20 |
| Skill registradora | K-003 Skill Creator |

## Responsabilidad

Diseña y ejecuta unit/integration/e2e; cobertura líneas≥80% ramas≥70%.

## Contrato

Entradas: DoD, RF/HU. Salidas: tests/** + evidence.

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
