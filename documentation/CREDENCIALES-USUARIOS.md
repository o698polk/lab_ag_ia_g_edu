# Credenciales de usuarios — laboratorio local

Solo para el laboratorio en `127.0.0.1`. No usar fuera de esta máquina. El servidor decide el acceso; estas cuentas no otorgan permisos por sí solas si la política responde DENY.

Se crean con `scripts/seed_iam.py` y el campus se puebla con `scripts/seed_academic.py`. Contraseñas de prueba (hash del sistema):

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `Admin123!` |
| Docente | `teacher1` … `teacher16` | `Teacher123!` |
| Estudiante | `student1` … `student300` | `Student123!` |

## Cuentas de referencia

| Usuario | Nombre | Rol | Uso |
|---|---|---|---|
| `admin` | Ana Administradora | ADMINISTRATOR | Catálogos, matrículas, reportes |
| `teacher1` | Juan Pérez | TEACHER | IIPA 2026: Programación Web, Desarrollo Móvil y Seguridad Informática |
| `student1` | María Fernanda López | STUDENT | DSW nivel 2: materias, notas y asistencia |

En la pantalla de entrada, los botones Administrador, Docente y Estudiante rellenan `admin`, `teacher1` y `student1`.
