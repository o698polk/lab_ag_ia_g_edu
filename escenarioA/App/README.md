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

### Credenciales demo (tras `seed_coherent` / SPEC-011)

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `Admin123!` | ADMIN |
| `rector` | `Rector123!` | RECTOR |
| `auditor` | `Auditor123!` | AUDITOR |
| `coord01`–`coord03` | `Coord123!` | COORDINATOR |
| `secretaria` | `Secretaria123!` | SECRETARY |
| `tutor1` | `Tutor123!` | GUARDIAN |
| `itsupport` | `Soporte123!` | IT_SUPPORT |
| `docente01`–`docente20` | `Docente123!` | TEACHER |
| `est0001`–`est0400` | `Estudiante123!` | STUDENT |

Dataset: 3 carreras × 6 materias, 2 periodos (`2025-1`, `2025-2`), 18 cursos, 2400 matrículas/notas, 24000 asistencias.

## MySQL (XAMPP)

1. En `App/.env` apunta a la BD `laboratorioA` (XAMPP):

```
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/laboratorioA
```

2. Con MySQL de XAMPP en marcha, recrear desde cero:

```
cd App/backend
.\.venv\Scripts\python.exe setup_mysql.py
```

3. Cargar dataset académico coherente:

```
$env:PYTHONPATH="..\database\seeds"
.\.venv\Scripts\python.exe -c "from run import app; from seed_coherent import seed_coherent; print(seed_coherent(app))"
```

4. O ejecutar `python run.py` (crea tablas + seed base si la BD ya existe).

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
