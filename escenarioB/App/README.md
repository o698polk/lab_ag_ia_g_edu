# Sistema de Gestión Académica Institucional

Stack: **Python · Flask · MySQL/SQLite · Bootstrap 5 · DeepSeek**

Construido con metodología **Spec as Skill** (ver `/Spec` y `/Skill`).

## Requisitos

- Python 3.11+
- MySQL 8 (XAMPP) **o** SQLite para desarrollo

## Instalación rápida (SQLite)

```bash
cd App/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
copy ..\.env.example ..\.env   # o use el .env ya incluido
python run.py
```

Abrir: http://127.0.0.1:5000

### Credenciales demo

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `Admin123!` | ADMIN |
| `docente1` | `Docente123!` | TEACHER |
| `estudiante1` | `Estudiante123!` | STUDENT |

## MySQL (XAMPP)

1. Crear base `laboratorio_academico` en phpMyAdmin.
2. En `App/.env`:

```
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/laboratorio_academico
```

3. Ejecutar `python run.py` (crea tablas + seeds).

## DeepSeek

Administración → Configuración IA → API Key, modelo y system prompt.  
La clave se cifra (AES) y nunca se expone al frontend.

## API

Prefijo: `/api/v1/`

Documentación de endpoints según Specs en `/Spec`.

## Estructura

```
App/
├── backend/     → Flask API
├── frontend/    → Templates + static
└── database/    → Seeds / migrations
```
