# SPEC-010 — Tema institucional (claro / oscuro)

**Objetivo:** Que el campo **Tema por defecto** de Administración (`system_config.default_theme`) controle de verdad el tema visual del sistema, se aplique al guardar y se respete en login y arranque de la app.

**Skills relacionadas:** SKILL-009  
**Specs relacionadas:** SPEC-006 (UI), SPEC-009 (config de marca)

---

## 1. Conceptos

| Concepto | Origen | Uso |
| --- | --- | --- |
| Tema institucional | `system_config.default_theme` (`light` \| `dark`) | Tema por defecto del sistema |
| Preferencia personal | `users.theme` + `localStorage.theme_override=1` | Solo si el usuario pulsó el botón claro/oscuro |
| Tema visual activo | `document.documentElement[data-theme]` | Lo que el usuario ve |

---

## 2. Resolución del tema (orden obligatorio)

Al pintar la UI (login o `/app`):

1. Si existe preferencia personal activa (`localStorage.theme_override === "1"` y hay tema de usuario/localStorage) → usar esa preferencia.
2. Si no → usar `default_theme` de `/api/v1/config/brand` (o `/config`).
3. Fallback → `light`.

Regla: el valor por defecto de BD `users.theme = "light"` **no** debe bloquear el tema institucional si el usuario nunca eligió tema con el toggle.

---

## 3. Comportamiento al guardar en Administración

Al enviar el formulario de colores/tema (`PUT /config` con `default_theme`):

1. Persistir en `system_config` (ya existe).
2. **Aplicar de inmediato** `data-theme` en el documento actual (`applyTheme(default_theme)`).
3. Actualizar `localStorage.theme` al nuevo valor.
4. Quitar `theme_override` (el admin está definiendo el tema del sistema; la sesión actual debe reflejarlo).
5. Opcional recomendado: sincronizar `users.theme` del admin autenticado vía `PUT /auth/theme` para coherencia.
6. Mostrar feedback (“Tema oscuro/claro aplicado”).

Si solo se cambian colores y no el tema, no forzar cambio de tema.

---

## 4. Toggle manual (navbar)

Al pulsar el botón sol/luna:

1. Alternar `light` ↔ `dark`.
2. Marcar `localStorage.theme_override = "1"`.
3. Guardar preferencia en `PUT /auth/theme`.
4. Esta preferencia gana sobre `default_theme` hasta que el usuario limpie override o un admin redefina el tema institucional en esa misma sesión (ver §3.4).

---

## 5. Login y boot

| Pantalla | Acción |
| --- | --- |
| Login | Cargar `/config/brand` → aplicar resolución §2 (sin usuario aún: solo `default_theme` o override local) |
| App `bootApp` | Tras `/auth/me` y brand → aplicar resolución §2 |
| Tras `saveConfig` | Aplicar §3 sin esperar recarga |

---

## 6. CSS

- El tema visual depende únicamente de `html[data-theme="light|dark"]`.
- Las variables de marca (`--primary`, etc.) se mantienen independientes del tema (SPEC-009 / colores).
- `[data-theme="dark"]` redefine fondos/textos; no debe resetear `--primary` salvo diseño explícito.

---

## 7. Criterios de aceptación

1. Admin → Administración → Tema por defecto = Oscuro → Guardar → **la UI cambia a oscuro al instante** (sidebar, paneles, login al salir).
2. Recargar `/app` sin haber usado el toggle → sigue oscuro (institucional).
3. Usuario pulsa toggle a claro → queda claro (override); recarga mantiene claro.
4. Admin vuelve a guardar Tema por defecto = Oscuro → UI de esa sesión pasa a oscuro y limpia override.
5. Login muestra el tema institucional si no hay override local.

---

## 8. Modelos de IA sugeridos

Composer, Claude Sonnet, GPT-4o — leer SPEC-010 + SKILL-009 antes de tocar código.
