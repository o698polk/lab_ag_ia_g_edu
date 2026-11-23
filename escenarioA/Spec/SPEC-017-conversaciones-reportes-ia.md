# SPEC-017 — Conversaciones unificadas + reportes desde el agente IA

**Objetivo:** Persistir el historial del asistente IA y **replicarlo** entre el **chat flotante** y el **chat fijo** (módulo Asistente IA), de modo que sea la misma conversación. Además, permitir que el agente **genere reportes** en **PDF, Excel, JSON y Markdown** ante consultas del usuario, reutilizando filtros/scope existentes.

**Skills relacionadas:** SKILL-016  
**Specs relacionadas:** SPEC-005, SPEC-006, SPEC-013, SPEC-016 (gateway/tools)

---

## 1. Problema actual

| Pieza | Hoy |
| --- | --- |
| Chat fijo (`Pages.ai` / `#aiMessages`) | Mensajes solo en DOM; se pierden al navegar |
| Chat flotante (`#floatChatMessages`) | Historial independiente en otro DOM |
| Backend | `AILog` guarda pares message/response sueltos, sin hilo ni canal |
| Reportes | Endpoints `/reports/*.xlsx|pdf` desde UI de módulos; el agente no los invoca ni ofrece JSON/MD |

El usuario ve dos chats “distintos” aunque sea el mismo asistente.

---

## 2. Modelo de datos

### 2.1 `ai_conversations`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | UUID / string PK | Identificador de conversación |
| `user_id` | FK users | Dueño |
| `title` | string(200) nullable | Auto: primeros ~60 chars del primer mensaje |
| `created_at` | datetime | |
| `updated_at` | datetime | Último mensaje |
| `is_archived` | bool | default false |

### 2.2 `ai_messages`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | int PK | |
| `conversation_id` | FK | |
| `role` | enum/string | `user` \| `assistant` \| `system` \| `tool` |
| `content` | text | Texto visible |
| `channel` | string(20) | `panel` \| `float` \| `api` (origen del turno) |
| `tool_name` | string nullable | Si role=tool |
| `tool_payload` | JSON nullable | Args/resultado sanitizado |
| `artifact_id` | FK nullable | Si el turno generó un reporte |
| `created_at` | datetime | |
| `tokens_used` | int nullable | |

### 2.3 `ai_artifacts` (reportes generados)

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | int / UUID PK | |
| `conversation_id` | FK | |
| `user_id` | FK | |
| `format` | string | `pdf` \| `xlsx` \| `json` \| `md` |
| `report_type` | string | `grades` \| `attendance` \| `enrollments` \| `students` \| `summary` \| `custom` |
| `filename` | string | ej. `notas_2026-10-09.xlsx` |
| `storage_path` o `content_blob` | path/bytes | Preferir archivo temporal + descarga por id |
| `filters` | JSON | Filtros usados (term_id, course_id, …) |
| `created_at` | datetime | |
| `expires_at` | datetime nullable | Limpieza opcional (24–72 h) |

Compatibilidad: seguir escribiendo un resumen en `AILog` por turno (o migrar lectura de logs a conversaciones).

---

## 3. Unificación chat flotante ↔ chat fijo

### 3.1 Regla de producto

- Cada usuario tiene una **conversación activa** (la más reciente no archivada) compartida por ambos canales.
- Enviar desde el flotante o desde el panel **append** al mismo `conversation_id`.
- Al abrir el panel o el flotante: `GET /ai/conversations/active` (o `?id=`) carga el mismo historial y lo renderiza en `#aiMessages` y `#floatChatMessages`.
- Tras cada respuesta exitosa: ambos contenedores visibles se actualizan (si el otro está montado en DOM); si no, al abrirse recargan desde API.

### 3.2 Endpoints

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| GET | `/ai/conversations` | `ai.use` | Lista conversaciones del usuario |
| GET | `/ai/conversations/active` | `ai.use` | Activa + últimos N mensajes (ej. 100) |
| GET | `/ai/conversations/<id>` | `ai.use` | Detalle + mensajes (solo dueño; ADMIN puede auditar con `ai.view_logs`) |
| POST | `/ai/conversations` | `ai.use` | Nueva conversación (opcional “Nueva chat”) |
| POST | `/ai/chat` | `ai.use` | Ampliar: acepta `conversation_id` + `channel`; crea activa si falta |
| DELETE | `/ai/conversations/<id>` | `ai.use` | Archivar/borrar propia |

### 3.3 Contrato `POST /ai/chat` (ampliación)

Request (además de SPEC-016):

```json
{
  "message": "Resumen de asistencias de hoy",
  "conversation_id": null,
  "channel": "float"
}
```

Response:

```json
{
  "reply": "…",
  "conversation_id": "…",
  "messages": [
    { "role": "user", "content": "…", "channel": "float", "created_at": "…" },
    { "role": "assistant", "content": "…", "channel": "float", "created_at": "…" }
  ],
  "artifacts": []
}
```

### 3.4 UI

1. **Panel fijo:** cargar historial al entrar a `Pages.ai`; botón “Nueva conversación”.
2. **Flotante:** al abrir panel, sync desde `active`; mismo `send` que persiste.
3. Indicador opcional “Sincronizado” / título de conversación en ambos.
4. Sin `ai.use`: ocultar ambos (como hoy el flotante).

---

## 4. Reportes generados por el agente

### 4.1 Capacidades

El usuario puede pedir en lenguaje natural, por ejemplo:

- “Exporta las notas del periodo 2025-1 en Excel”
- “Dame un PDF de asistencia del curso 12”
- “Genera un JSON con estudiantes de Desarrollo de Software”
- “Resume matrículas en Markdown”

Formatos soportados: **`pdf` | `xlsx` | `json` | `md`**.

### 4.2 Tools del gateway (SPEC-016)

| Tool | Descripción |
| --- | --- |
| `reports.generate` | Parámetros: `report_type`, `format`, `filters{}` |
| `reports.list_types` | Catálogo de reportes disponibles según permisos del usuario |

Permisos: reutilizar los de export existentes (`reports.export`, `grades.view`, etc.). Si falta permiso → mensaje + opcional elevación (SPEC-016 §5).

### 4.3 Generación

1. Resolver `report_type` + filtros desde el NL (term, career, course, fechas, status).
2. Aplicar **mismo scope** que `app/services/reports.py` (docente/estudiante/periodos).
3. Generar archivo:
   - `xlsx` / `pdf`: reutilizar generadores actuales.
   - `json`: array/objeto de los mismos datos filtrados.
   - `md`: tabla Markdown + título/metadatos (fecha, filtros, usuario).
4. Guardar `ai_artifacts` y devolver en la respuesta:

```json
{
  "artifacts": [
    {
      "id": 9,
      "format": "xlsx",
      "filename": "grades_2025-1.xlsx",
      "download_url": "/api/v1/ai/artifacts/9/download"
    }
  ]
}
```

5. UI: en ambos chats, burbuja con enlace/botón **Descargar**.

### 4.4 Endpoint de descarga

`GET /api/v1/ai/artifacts/<id>/download`  
- Auth JWT; solo dueño o ADMIN.  
- Headers `Content-Disposition` + content-type según formato.

---

## 5. Criterios de aceptación

1. Mensaje enviado en el flotante aparece al abrir el módulo Asistente IA (misma conversación), y viceversa.
2. Recargar la página conserva el historial (persistido en BD).
3. “Nueva conversación” aísla el hilo anterior; el flotante sigue la activa nueva.
4. Pedir “exporta notas en excel” (con permiso) → artifact descargable `.xlsx`.
5. Mismo pedido en `pdf`, `json`, `md` → formatos correctos y no vacíos si hay datos.
6. Usuario sin permiso de export recibe negativa clara, sin archivo.
7. Conversación de usuario A no es legible por usuario B.

---

## 6. Fuera de alcance

- Chat en tiempo real multi-usuario / salas.
- Adjuntar archivos arbitrarios del usuario al LLM (fase posterior).
- Firmas digitales de PDF institucionales.

---

## 7. Modelos de IA sugeridos

Composer / Claude Sonnet — leer SPEC-017 + SKILL-016 (+ SPEC-016 si hay tools de reportes) antes de editar.
