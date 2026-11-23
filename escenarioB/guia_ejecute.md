# Guía de ejecución — Sistema de Gestión Académica

Paso a paso para levantar el proyecto en Windows (PowerShell + XAMPP) **sin errores**.

---

## Error frecuente: “la ejecución de scripts está deshabilitada”

Si al activar el entorno virtual aparece:

```text
.\.venv\Scripts\activate : No se puede cargar el archivo ...\Activate.ps1 porque
la ejecución de scripts está deshabilitada en este sistema.
```

PowerShell bloquea `.ps1`. Usa **una** de estas soluciones:

### Opción A (recomendada, solo para esta ventana)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate
```

`Scope Process` solo afecta la terminal actual; no cambia la política del PC.

### Opción B (sin activar el venv)

Llama a Python del venv directamente:

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
.\.venv\Scripts\python.exe run.py
```

### Opción C (CMD en lugar de PowerShell)

```cmd
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
.venv\Scripts\activate.bat
python run.py
```

### Opción D (política del usuario, permanente)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Cierra y abre la terminal, luego:

```powershell
.\.venv\Scripts\activate
```

---

## Requisitos previos

1. Python 3.11 o superior instalado (`python --version`).
2. XAMPP instalado.
3. En el panel de XAMPP: **Start** en **MySQL** (y Apache si usas phpMyAdmin).
4. Proyecto en `D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB`.

---

## Paso 1 — Ir al backend

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
```

---

## Paso 2 — Crear el entorno virtual (solo la primera vez)

```powershell
python -m venv .venv
```

---

## Paso 3 — Activar el venv (evitar el error de scripts)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate
```

Debes ver `(.venv)` al inicio del prompt.

Si no quieres cambiar la política, usa siempre:

```powershell
.\.venv\Scripts\python.exe
```

en lugar de `python` (ver opción B arriba).

---

## Paso 4 — Instalar dependencias (solo la primera vez o si cambian)

```powershell
pip install -r requirements.txt
```

Con venv sin activar:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Paso 5 — Archivo `.env`

Comprueba que exista `D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\.env`.

Si no existe:

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App
copy .env.example .env
cd backend
```

Contenido mínimo para MySQL (XAMPP, root sin contraseña):

```env
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/laboratorioB
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!
```

Si MySQL tiene contraseña:

```env
DATABASE_URL=mysql+pymysql://root:TU_CLAVE@127.0.0.1:3306/laboratorioB
```

**Alternativa sin MySQL (SQLite):**

```env
DATABASE_URL=sqlite:///../database/laboratorio.db
```

---

## Paso 6 — Crear base de datos, tablas y seeds desde cero (MySQL)

Con MySQL de XAMPP en marcha:

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate
python setup_mysql.py
```

Sin activar el venv:

```powershell
.\.venv\Scripts\python.exe setup_mysql.py
```

Esto:

1. Lee `DATABASE_URL` del `.env` (BD `laboratorioB`).
2. Hace `DROP` + `CREATE` de la base (desde cero).
3. Crea todas las tablas (`db.create_all`).
4. Ejecuta seed base (roles, permisos, admin) + seed masivo académico.

---

## Paso 7 — Levantar el servidor

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate
python run.py
```

O sin activar:

```powershell
.\.venv\Scripts\python.exe run.py
```

Deja la ventana abierta. Abre el navegador en:

**http://127.0.0.1:5000**

---

## Paso 8 — Iniciar sesión

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `Admin123!` | ADMIN |
| `rector` | `Rector123!` | RECTOR |
| `auditor` | `Auditor123!` | AUDITOR |
| `coord01`–`coord03` | `Coord123!` | COORDINATOR |
| `secretaria` | `Secretaria123!` | SECRETARY |
| `tutor1` | `Tutor123!` | GUARDIAN |
| `soporte` | `Soporte123!` | IT_SUPPORT |
| `docente01`–`docente20` | `Docente123!` | TEACHER |
| `est0001`–`est0400` | `Estudiante123!` | STUDENT |

Dataset (SPEC-033): 3 carreras, 2 periodos (`2025-1`/`2025-2`), 20 docentes, 400 estudiantes, matrículas/notas/asistencias/horarios coherentes. Regenerar: `python setup_mysql.py` desde `App/backend`.

---

## Comandos rápidos (cada vez que abras la consola)

Copia y pega esto en PowerShell:

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate
python run.py
```

O la versión que **nunca** falla por política de scripts:

```powershell
cd D:\PROYECTOS\lab_ag_ia_g_edu\laboratorioIB\App\backend
.\.venv\Scripts\python.exe run.py
```

---

## Problemas frecuentes

| Error | Solución |
|-------|----------|
| Ejecución de scripts deshabilitada | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` o usar `.\.venv\Scripts\python.exe` |
| No se puede conectar a MySQL | Arrancar MySQL en XAMPP |
| Puerto 5000 en uso | Cerrar el otro `run.py` o poner `PORT=5001` en `.env` |
| `ModuleNotFoundError` | Instalar deps: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| No existe admin / BD vacía | Ejecutar `python setup_mysql.py` |
| Página sin estilos / JS viejo | Recargar con `Ctrl + F5` |

---

## DeepSeek (opcional)

1. Login como `admin`.
2. Administración → Configuración IA.
3. Pegar API Key y guardar.

Sin API Key el sistema funciona; solo el chatbot IA no responderá.
