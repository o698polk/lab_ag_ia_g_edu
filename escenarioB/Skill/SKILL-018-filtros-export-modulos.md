# SKILL-018 — Filtros y export Excel/PDF universales

**Spec:** SPEC-019  
**También aplica:** SPEC-004, SPEC-006, SPEC-009

## Rol del agente

Añadir filtros contextuales (incl. roles y fechas en Usuarios) y exportación Excel/PDF a todos los módulos de listado.

## Procedimiento

1. Leer SPEC-019.
2. `reports.py`: `filter_*` + `*_rows` para users, teachers, careers, subjects, terms, courses, schedules, notifications, audit; soportar `role` en `_args`.
3. `system_api.py`: rutas `/reports/{type}.xlsx|pdf` para cada tipo nuevo (o registry genérico).
4. `crud.js`:
   - Filtro `role` + `data-role` en `dataAttrs` / `applyAdvancedFilters` / `buildReportQuery`.
   - Ampliar `exportReport` map y `canExport`.
5. `app.js`: en cada `pages.*` pasar `filters`, `statusOptions`/`roleOptions`, `exportType` y `dataAttrs` correctos; cargar `roles` en meta para usuarios.
6. Verificar: usuarios por rol + fechas; un módulo nuevo (teachers/careers) descarga xlsx/pdf 200.

## Restricciones

- No saltar permisos ni scope de visibilidad.
- No romper exports existentes de grades/attendance/enrollments/students.
