# SPEC-027 — Indicador «pensando / escribiendo» y presentación formal APA 7

**Objetivo:** Mejorar la experiencia del chat IA con (1) un indicador visual de que el agente está pensando y escribiendo, y (2) respuestas en texto **simple, formal y legible**, sin markdown ornamental (`*`, `**`, guiones decorativos, viñetas raras ni caracteres especiales). La redacción se guía por las normas de presentación de la **APA 7.ª edición** adaptadas a un asistente académico (claridad, tono profesional, párrafos y listas numeradas).

**Skills relacionadas:** SKILL-026  
**Specs relacionadas:** SPEC-022, SPEC-023

---

## 1. Problema

1. Mientras el LLM procesa, el chat no da feedback → sensación de bloqueo.
2. El modelo suele responder con markdown (`**negrita**`, `*cursiva*`, listas con `-`/`*`, emojis, símbolos), lo que se ve poco profesional en un sistema académico.

---

## 2. Requisitos de UI (typing / thinking)

1. Al enviar un mensaje del usuario, mostrar de inmediato una burbuja de estado del asistente con:
   - Icono animado de «pensando» (p. ej. `bi-lightbulb` o cerebro con pulso/rotación suave).
   - Texto: «Pensando…» y luego «Escribiendo…» (o un único estado «El asistente está elaborando la respuesta…»).
   - Indicador de puntos animados (typing dots).
2. El indicador aparece en el panel de chat y en el chat flotante.
3. Al llegar la respuesta, retirar el indicador e insertar la burbuja del asistente con **efecto de escritura** (typewriter) suave, sin retrasar la usabilidad más de ~2–3 s para textos largos (acelerar o mostrar completo si el texto es muy largo).
4. No bloquear el scroll: mantener la vista al final de los mensajes.

---

## 3. Requisitos de presentación textual (APA 7 como guía)

Principios aplicables (no cita bibliográfica obligatoria; es **guía de estilo**):

| Principio APA 7 | Aplicación en el chat |
| --- | --- |
| Claridad y concisión | Oraciones completas; evitar jerga técnica innecesaria |
| Tono profesional | Segunda persona respetuosa; sin slang ni emojis |
| Evitar énfasis tipográfico excesivo | Sin `*`, `**`, `__`, `_` de markdown |
| Organización | Párrafos cortos; listas **numeradas** (1. 2. 3.) en lugar de viñetas con `-`/`•`/`*` |
| Lenguaje inclusivo y preciso | Español formal; datos concretos sin inventar |

Reglas de sanitización (backend, red de seguridad UI):

1. Eliminar `**…**`, `*…*`, `__…__`, `_…_` (dejar el texto interior).
2. Sustituir líneas que empiezan por `- `, `* `, `• `, `– `, `— ` por formato `1. `, `2. `, … o párrafo.
3. Eliminar emojis y caracteres de adorno (★, ✓ decorativos, flechas unicode raras). Conservar puntuación latina normal y enlaces URL.
4. Colapsar espacios múltiples y líneas vacías excesivas (máx. 1 línea en blanco entre párrafos).
5. Prompt de sistema: exigir este estilo; no usar markdown.

---

## 4. Criterios de aceptación

1. Al enviar un mensaje, se ve el icono animado + «Pensando…» / typing dots hasta recibir respuesta.
2. La respuesta nueva se revela con efecto de escritura (o aparece completa si supera umbral).
3. Una respuesta con `**Notas**` y `- item` llega al usuario como texto plano formal sin asteriscos ni viñetas markdown.
4. Compose post-tools (`_compose_user_reply`) también usa el mismo estilo formal.
5. SPEC/SKILL documentados; PROMPTSMASTER actualizado.

---

## 5. Modelos sugeridos

Composer / Claude — leer SPEC-027 + SKILL-026 antes de implementar.
