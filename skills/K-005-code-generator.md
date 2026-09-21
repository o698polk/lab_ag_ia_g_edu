# K-005 — Code Generator

| Campo | Valor |
|---|---|
| Código | K-005 |
| Nombre | Code Generator |
| Fase primaria | F6 |
| Estado | Registered |
| Fecha registro | 2026-09-20 |
| Skill registradora | K-003 Skill Creator |

## Responsabilidad

Implementa código App siguiendo capas SPEC→SKILL→APP y orden PolkDev F6.

## Contrato

Entradas: Spec+Arquitectura+Skill asignada. Salidas: app/**. Nunca sin Spec.

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
