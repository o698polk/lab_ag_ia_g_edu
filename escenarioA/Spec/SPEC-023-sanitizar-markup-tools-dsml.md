# SPEC-023 — Sanitizar markup DSML / tool-calls en respuestas

**Objetivo:** El usuario **nunca** debe ver marcas internas de invocación de tools (DSML, `invoke name=…`, XML de function-call, etc.). Esas llamadas deben **ejecutarse** y responderse en lenguaje natural.

**Skills relacionadas:** SKILL-022  
**Specs relacionadas:** SPEC-016, SPEC-022

---

## 1. Problema

Algunos modelos (p. ej. DeepSeek) emiten tool-calls como texto:

```text
<|DSML|calls>
<|DSML|invoke name="users_list">
<|DSML|parameter name="search">Gabriela López</|DSML|parameter>
</|DSML|invoke>
</|DSML|calls>
```

Si `message.tool_calls` viene vacío, el orquestador trata ese texto como la **respuesta al usuario** → error de UX.

---

## 2. Reglas

1. `parse_tool_calls` debe aceptar:
   - `tool_calls` estructurados (OpenAI),
   - **y** markup DSML / XML / `invoke name=` en `content`.
2. Si hay markup de tools en `content` → parsear, ejecutar tools, **no** devolver el markup.
3. Sanitizar cualquier reply que contenga: `DSML`, `invoke name=`, `<|`, `</|`, `<tool_call`, `function_call`.
4. Prompt de sistema: prohibir explícitamente emitir DSML / XML de tools al usuario; usar solo la API de tools.
5. UI: filtrar burbujas con markup DSML (red de seguridad).

---

## 3. Criterios de aceptación

1. Pedir “busca al usuario Gabriela López” → respuesta natural con resultados; **sin** texto DSML.
2. Validación: reply no contiene `DSML` ni `invoke name=`.
3. Si el modelo solo emite DSML sin `tool_calls` JSON → igual se ejecuta `users_list`.

---

## 4. Modelos sugeridos

Composer — leer SPEC-023 + SKILL-022 antes de editar.
