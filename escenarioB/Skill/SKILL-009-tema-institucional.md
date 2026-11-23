# SKILL-009 — Aplicador de Tema Institucional

**Spec:** SPEC-010  
**También aplica:** SPEC-006

## Rol del agente

Hacer que `default_theme` de Administración controle el tema visual (`data-theme`), se aplique al guardar y se resuelva correctamente en login/boot frente a la preferencia personal del usuario.

## Antes de codificar

1. Leer `Spec/SPEC-010-tema-institucional.md`.
2. Revisar `applyTheme`, `toggleTheme`, `saveConfig`, `bootApp` en `App/frontend/static/js/app.js`.
3. Revisar login en `App/frontend/templates/login.html` y `/config/brand` en `system_api.py`.
4. No “arreglar” solo el `<select>`: el fallo es no aplicar `data-theme` tras guardar / no usar `default_theme` en el boot.

## Procedimiento

### Paso A — Helper de resolución
En `app.js` (y lógica equivalente en login):

```js
function resolveTheme({ userTheme, defaultTheme, respectOverride = true }) {
  const override = localStorage.getItem("theme_override") === "1";
  if (respectOverride && override) {
    return localStorage.getItem("theme") || userTheme || defaultTheme || "light";
  }
  return defaultTheme || userTheme || "light";
}
```

- `applyTheme(theme)` sigue seteando `data-theme` + `localStorage.theme`.
- `toggleTheme()` debe además `localStorage.setItem("theme_override", "1")` y persistir `/auth/theme`.

### Paso B — Guardar en Administración
En `saveConfig`:

1. Tras `PUT /config` exitoso, si viene `default_theme`:
   - `localStorage.removeItem("theme_override")`
   - `applyTheme(saved.default_theme)`
   - `API.put("/auth/theme", { theme: saved.default_theme })` (best-effort)
2. Actualizar hint/toast indicando que el tema se aplicó.

### Paso C — Boot app
En `bootApp` / `loadBrandColors`:

1. Obtener brand (`default_theme`).
2. Tras `/auth/me`, llamar `applyTheme(resolveTheme({ userTheme: user.theme, defaultTheme: brand.default_theme }))`.
3. No aplicar ciegamente `user.theme` antes del brand (eso dejaba siempre `light`).

### Paso D — Login
Tras `GET /config/brand`, aplicar `resolveTheme({ defaultTheme: cfg.default_theme })` al `<html>`.

### Paso E — Verificar
1. Login admin → Administración → Tema oscuro → Guardar → UI oscura al instante.
2. F5 → sigue oscuro.
3. Toggle a claro → override; F5 mantiene claro.
4. Volver a guardar tema oscuro en admin → vuelve a oscuro.

## Restricciones

- No eliminar el toggle personal.
- No hardcodear `data-theme="dark"` en HTML estático.
- Mantener colores de marca (`--primary`) independientes.
- Backend ya persiste `default_theme`; el foco es frontend + resolución.

## Entregables

- SPEC-010 + esta SKILL.
- Cambios en `app.js` y `login.html`.
- Entrada en PROMPTSMASTER (lista Spec/Skill).
