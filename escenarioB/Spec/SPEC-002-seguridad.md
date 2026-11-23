# SPEC-002 — Seguridad (OWASP Top 10 2025)

**Objetivo:** Garantizar la seguridad del sistema en todos sus niveles.

| # | Riesgo OWASP | Mitigación |
| --- | --- | --- |
| A01 | Broken Access Control | Permisos granulares en cada endpoint |
| A02 | Cryptographic Failures | bcrypt, JWT firmado, HTTPS en producción |
| A03 | Injection | ORM parametrizado, sanitización |
| A04 | Insecure Design | Specs de seguridad desde el diseño |
| A05 | Security Misconfiguration | .env, cabeceras de seguridad |
| A06 | Vulnerable Components | Dependencias auditadas |
| A07 | Auth Failures | JWT + refresh, bloqueo por intentos |
| A08 | Software Integrity | Validación de integridad |
| A09 | Logging | Auditoría de eventos críticos |
| A10 | SSRF | Validación de URLs externas (IA) |

## Reglas

- Cabeceras: `X-Frame-Options`, `CSP`, `HSTS`, `X-Content-Type-Options`.
- Rate limiting en login y API IA.
- Tokens de impersonación con TTL limitado.
- API Key DeepSeek solo en backend (cifrada).
- Logs con IP, timestamp, usuario y acción.
