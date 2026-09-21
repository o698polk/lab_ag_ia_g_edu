# Credenciales de usuarios — laboratorio local

Solo para el laboratorio en `127.0.0.1`. No usar fuera de esta máquina. El servidor decide el acceso; estas cuentas no otorgan permisos por sí solas si la política responde DENY.

Se crean con `python scripts\seed_iam.py`. Si la base ya tiene el usuario, el script no cambia la contraseña.

## Administrador

| Usuario | Contraseña | Rol | Correo |
|---|---|---|---|
| `admin` | `Admin123!` | ADMINISTRATOR | `admin@siga.local` |

Ve inicio, notas, asistencia, asistente, avisos, catálogo y reportes.

## Docente

| Usuario | Contraseña | Rol | Correo |
|---|---|---|---|
| `teacher1` | `Teacher123!` | TEACHER | `teacher1@siga.local` |

Ve inicio, notas, asistencia, asistente, avisos y reportes. No ve el catálogo.

## Estudiante

| Usuario | Contraseña | Rol | Correo |
|---|---|---|---|
| `student1` | `Student123!` | STUDENT | `student1@siga.local` |

Ve inicio, sus notas, asistente y avisos. No ve asistencia, catálogo ni reportes.

En la pantalla de entrada, los botones Administrador, Docente y Estudiante rellenan estas mismas cuentas.
