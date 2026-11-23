# SKILL-025 — Módulo LogIA

**Spec:** SPEC-026

1. Leer SPEC-026.
2. Modelo `AIAgentLog` + `db.create_all` / ensure table.
3. Servicio `ai_agent_log.py`: `log_agent_event`, `scan_prompt_injection`, `list_logs`, export rows.
4. Instrumentar orchestrator + executor.
5. API list + export xlsx/pdf/json.
6. Frontend page `logia` con filtros y exports.
7. Seed: asegurar `ai.view_logs` en ADMIN/AUDITOR/IT_SUPPORT (ya existe).
8. Validar bloque injection + list + export.
