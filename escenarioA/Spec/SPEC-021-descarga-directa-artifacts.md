# SPEC-021 — Descarga directa de artifacts IA por URL

**Objetivo:** Que el reporte generado por el agente se pueda **descargar abriendo el link**  
`/api/v1/ai/artifacts/<id>/download` (ruta completa usable en navegador, copiar/pegar o clic), sin depender solo del botón con `fetch` + JWT.

**Skills relacionadas:** SKILL-020  
**Specs relacionadas:** SPEC-017, SPEC-018

---

## 1. Problema

| Hoy | Efecto |
| --- | --- |
| Endpoint exige `Authorization: Bearer` | Abrir `/api/v1/ai/artifacts/3/download` en pestaña → 401 |
| UI solo botón JS con token en header | No hay link copiable ni “abrir en nueva pestaña” |
| `download_url` relativo sin firma | No sirve como URL pública temporal |

---

## 2. Reglas

1. Autenticación del download: **JWT** (como ahora) **o** firma firmada en query (`expires` + `sig`).
2. Firma HMAC-SHA256 sobre `artifact_id:expires:user_id` con `SECRET_KEY` de la app.
3. Rechazar si `expires` venció, firma inválida, archivo ausente, o artifact inexistente.
4. Con JWT: dueño o ADMIN (igual que hoy).
5. `to_dict()` del artifact debe incluir:
   - `download_url`: path absoluto de API, ej. `/api/v1/ai/artifacts/3/download?expires=…&sig=…`
   - `download_path`: mismo path (alias claro)
6. Respuesta del agente / burbuja UI: mostrar **link completo** clicable + botón Descargar.
7. No exponer el archivo sin firma ni JWT.

---

## 3. Criterios de aceptación

1. `GET /api/v1/ai/artifacts/<id>/download?expires=…&sig=…` **sin** header Authorization → 200 + archivo.
2. Misma URL con `sig` alterado → 403.
3. URL expirada → 403/410.
4. Con JWT válido del dueño (sin query) → 200.
5. Chat muestra el path completo `/api/v1/ai/artifacts/<id>/download?...` y al hacer clic descarga.
6. Validación automatizada cubre firma + JWT.

---

## 4. Modelos sugeridos

Composer — leer SPEC-021 + SKILL-020 antes de editar.
