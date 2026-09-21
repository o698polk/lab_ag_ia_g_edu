# PromptMaster FASE 10 — Optimización UX / a11y / responsive

| Campo | Valor |
|---|---|
| Fecha | 2026-09-21 |
| Alcance | Frontend `/ui/` post F2–F9 |
| Skill | K-022 / modernización UX |

## Checklist

### Accesibilidad

| Ítem | Estado | Notas |
|---|---|---|
| `lang="es"` en HTML | ✅ | Todas las páginas generadas |
| Skip link al contenido | ✅ | Home/login estático; app shell vía `SigaNav.ensureSkipLink` |
| `:focus-visible` | ✅ | `responsive.css` |
| Toast `role` / `aria-live` | ✅ | `alert` en error, `status` en ok |
| Sidebar Escape / backdrop | ✅ | `navigation.js` |
| Labels en formularios | ✅ | `for`/`id` en módulos F4–F9 |
| Tablas con `<thead>` en HTML | ✅ | Regla F2+ |

### Responsive

| Ítem | Estado | Notas |
|---|---|---|
| Breakpoint ≤900px sidebar drawer | ✅ | + backdrop |
| Breakpoint ≤560px shortcuts 1 col | ✅ | |
| Tablas con scroll horizontal | ✅ | `min-width` en `.data-table` |
| Touch target menú ≥44px | ✅ | `.btn-sidebar` |
| `prefers-reduced-motion` | ✅ | |
| `prefers-contrast: more` | ✅ | |

### UX / eficiencia (métricas cualitativas lab)

| Flujo | Pantallas | Clics típicos | Feedback |
|---|---|---|---|
| Login → Dashboard | 2 | 1 submit | toast / redirect |
| Notas (carrera→periodo→paralelo) | 1 | 3 selects + 1 acción | toast |
| Asistencia sesión + marca | 1–2 | 4–5 | toast + tablas log |
| Reporte generar | 1 | 2–3 | preview + historial |
| Alta usuario (admin) | 1 | form submit | toast + refresh |

### Seguridad UX (sin autorizar en cliente)

| Ítem | Estado |
|---|---|
| Guard `requireAuth` en páginas protegidas | ✅ |
| Roles UI solo ocultan, servidor revalida | ✅ |
| DENY visible en toast (`formatError`) | ✅ |

## Pruebas automatizadas

```text
pytest tests/unit/test_ui_session_navigation.py
```

Incluye `test_ui_f10_a11y_responsive`.

## Cómo verificar manualmente

1. Ctrl+F5 en http://127.0.0.1:8000/ui/pages/home.html — Tab muestra skip link.
2. Login → Dashboard — Tab muestra skip al contenido.
3. Reducir ventana &lt;900px — Menú abre drawer + backdrop; Escape cierra.
4. Generar error de login — toast con `role=alert`.
