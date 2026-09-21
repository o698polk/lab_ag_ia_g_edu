# SEC-01 — Evaluación de seguridad OWASP / Zero Trust

| Campo | Valor |
|---|---|
| Proyecto | SIGA (`siga-polkdev`) |
| Fase | F8 — Security |
| Skill | K-007 Security Auditor |
| Fecha | 2026-09-20 |
| Spec | S05 RNF-SEC-* · A05 · PromptMaster §52–53 |

---

## 1. Alcance

Evaluación local (localhost) del laboratorio Zero Trust: autenticación JWT, RBAC+ABAC, Tool Gateway/PDP, secretos, controles OWASP Top 10 aplicables.

---

## 2. Matriz OWASP Top 10 (aplicable)

| # | Riesgo | Estado | Evidencia / control |
|---|---|---|---|
| A01 | Broken Access Control | **Mitigado** | `require_permission`, ABAC `teaching_assignment`, anti-IDOR, PDP DENY |
| A02 | Cryptographic Failures | **Mitigado** | Argon2 passwords; JWT HS256; refresh hashed SHA-256 |
| A03 | Injection | **Mitigado** | SQLAlchemy ORM (sin SQL crudo de usuario); login payloads denegados |
| A04 | Insecure Design | **Mitigado** | Deny-by-Default; IA no toca MySQL; Gateway PEP |
| A05 | Security Misconfiguration | **Mitigado (local)** | Headers seguridad; CORS restringido; docs solo si `APP_DEBUG` |
| A06 | Vulnerable Components | **Aceptado residual** | Dependencias pinned en ranges; revisión F12 |
| A07 | Identification/Auth Failures | **Mitigado** | JWT type/alg whitelist; rate limit login; LOGIN_FAILURE audit |
| A08 | Software/Data Integrity | **Parcial** | Policies versionadas YAML; sin supply-chain CI aún |
| A09 | Security Logging Failures | **Mitigado** | `audit_events` + `security_events` separados de historial usuario |
| A10 | SSRF | **N/A local** | Sin fetch arbitrario de URL por usuario |

---

## 3. Controles F8 añadidos

1. Middleware `SecurityHeadersMiddleware` (nosniff, frame-deny, CSP API, no-store).
2. Middleware `LoginRateLimitMiddleware` (429 RATE_LIMITED).
3. JWT: rechazo `alg=none`, whitelist algoritmo, `type=access` obligatorio.
4. Pydantic `extra=forbid` en schemas IAM sensibles (anti mass-assignment).
5. CORS métodos/headers acotados.
6. Registro `LOGIN_FAILURE` en `security_events`.
7. OpenAPI `/docs` solo con `APP_DEBUG=true`.

---

## 4. Secretos

| Control | Estado |
|---|---|
| `.env` en `.gitignore` | ✅ |
| `.env.example` sin secretos reales | ✅ |
| `JWT_SECRET` placeholder detectado en `/ready` | ✅ |
| Sin API keys en código | ✅ |
| AI_API_KEY vacío por defecto | ✅ |

---

## 5. Hallazgos

| ID | Severidad | Hallazgo | Decisión |
|---|---|---|---|
| H-F8-01 | Baja | Cobertura de ramas global &lt; 70% | Aceptado → mejorar en F12 / deuda documentada ADR-013 |
| H-F8-02 | Info | Rate limit in-memory (no distribuido) | Aceptado en lab localhost (ADR-013) |
| H-F8-03 | Info | CSRF N/A (Bearer JWT, no cookies de sesión) | Aceptado |

**Ningún hallazgo crítico abierto que bloquee Gate F8.**

---

## 6. Trazabilidad de pruebas

| Control | Test |
|---|---|
| JWT / IDOR / SQLi / XSS / escalation | `tests/security/test_owasp_basics.py` |
| Headers / ABAC teacher / tampering / login audit | `tests/security/test_f8_hardening.py` |
| AI DENY update_grade | `tests/unit/test_zero_trust.py` + e2e |

---

## 7. Conclusión Gate F8

**GO recomendado** hacia F9 Documentation, con residuales no críticos aceptados en ADR-013.
