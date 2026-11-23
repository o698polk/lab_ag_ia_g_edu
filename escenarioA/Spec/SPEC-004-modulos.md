# SPEC-004 — Módulos del Sistema

## 4.1 Auth
- Login JWT (access 15 min + refresh 7 días).
- Bloqueo tras 5 intentos fallidos (15 min).
- Logout con revocación de refresh.
- Cambio de contraseña obligatorio en primer acceso.

## 4.2 Usuarios
- CRUD, roles, activar/desactivar, impersonación (`users.login-as`), historial de sesiones.

## 4.3–4.6 Académico
- Estudiantes, docentes, carreras, periodos, materias, mallas, cursos, asignaciones, horarios.

## 4.7 Matrículas
- Estados: activa, retirada, congelada. Validación de prerrequisitos.

## 4.8 Notas
- Parcial1, Parcial2 (1–10). Promedio = (P1+P2)/2.
- Si promedio < 7.0 → habilitar Supletorio.
- Con supletorio → nota final = supletorio.
- Solo docente asignado; cierre por periodo (admin reabre).
- Auditoría en cada cambio.

## 4.9 Asistencia
- presente, ausente, tardanza, justificada.
- Alerta al superar 25% de faltas.

## 4.10–4.13
- Kárdex (PDF), Reportes (PDF/Excel), Notificaciones, Auditoría append-only.
