# SPEC-008 — Impersonación de Usuarios

## Flujo
1. Admin → Usuarios → "Entrar"
2. Modal confirmación → `POST /api/v1/users/{id}/login-as`
3. Tokens con `impersonator_id` en JWT
4. Banner "Viendo como {usuario}" + "Regresar a mi cuenta"
5. `POST /api/v1/auth/return-to-admin`
6. Eventos `IMPERSONATION_START` / `IMPERSONATION_END`

## Restricciones
- Permiso `users.login-as`.
- No: propia cuenta, admin protegido, inactivos, anidada.
- Banner visible en todas las páginas.

## JWT claim
```json
{
  "sub": "<id impersonado>",
  "roles": ["TEACHER"],
  "permissions": ["..."],
  "impersonator_id": <id admin>
}
```
