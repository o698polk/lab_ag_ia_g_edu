# -*- coding: utf-8 -*-
"""Generate FASE 7 catalog entity pages. Run: python scripts/_build_catalogos_f7.py"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "frontend"
PAGES = ROOT / "pages" / "catalogos"

SIDEBAR = """
<aside class="app-sidebar" aria-label="Menú principal">
  <a class="app-brand" href="/ui/pages/dashboard/dashboard.html">
    <span class="app-brand-dot"></span><span>SIGA</span>
  </a>
  <p class="side-section">Módulos</p>
  <nav class="side-nav">
    <a class="side-link" href="/ui/pages/dashboard/dashboard.html">Dashboard</a>
    <a class="side-link" href="/ui/pages/notas/notas.html">Notas</a>
    <a class="side-link" href="/ui/pages/asistencia/asistencia.html" data-roles="TEACHER,ADMINISTRATOR">Asistencia</a>
    <a class="side-link active" href="/ui/pages/catalogos/catalogos.html" data-roles="ADMINISTRATOR">Catálogos</a>
    <a class="side-link" href="/ui/pages/reportes/reportes.html" data-roles="TEACHER,ADMINISTRATOR">Reportes</a>
    <a class="side-link" href="/ui/pages/avisos/avisos.html">Avisos</a>
    <a class="side-link" href="/ui/pages/asistente/asistente.html">Asistente</a>
    <a class="side-link" href="/ui/pages/cuenta/perfil.html">Perfil</a>
  </nav>
  <p class="side-section">Catálogos</p>
  <nav class="side-nav side-nav-sub" data-roles="ADMINISTRATOR">
    <a class="side-link{carreras}" href="/ui/pages/catalogos/carreras.html">Carreras</a>
    <a class="side-link{asignaturas}" href="/ui/pages/catalogos/asignaturas.html">Asignaturas</a>
    <a class="side-link{periodos}" href="/ui/pages/catalogos/periodos.html">Periodos</a>
    <a class="side-link{estudiantes}" href="/ui/pages/catalogos/estudiantes.html">Estudiantes</a>
    <a class="side-link{docentes}" href="/ui/pages/catalogos/docentes.html">Docentes</a>
    <a class="side-link{cursos}" href="/ui/pages/catalogos/cursos.html">Cursos</a>
    <a class="side-link{matriculas}" href="/ui/pages/catalogos/matriculas.html">Matrículas</a>
  </nav>
</aside>
"""

CSS = """
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="/ui/assets/css/base.css" />
  <link rel="stylesheet" href="/ui/assets/css/layout.css" />
  <link rel="stylesheet" href="/ui/assets/css/components.css" />
  <link rel="stylesheet" href="/ui/assets/css/forms.css" />
  <link rel="stylesheet" href="/ui/assets/css/tables.css" />
  <link rel="stylesheet" href="/ui/assets/css/responsive.css" />
"""

SCRIPTS = """
  <script src="/ui/assets/js/core/api.js"></script>
  <script src="/ui/assets/js/components/toast.js"></script>
  <script src="/ui/assets/js/components/table.js"></script>
  <script src="/ui/assets/js/core/navigation.js"></script>
  <script src="/ui/assets/js/core/auth.js"></script>
  <script src="/ui/assets/js/modules/catalogos/entity.js"></script>
"""

ENTITIES = [
    {
        "slug": "carreras",
        "title": "Carreras",
        "entity": "careers",
        "hint": "GET/POST /careers",
        "cols": [
            ("id", "Id"),
            ("code", "Código"),
            ("name", "Nombre"),
            ("modality", "Modalidad"),
            ("duration_semesters", "Semestres"),
            ("status", "Estado"),
        ],
        "fields": [
            ("code", "Código", "text", True),
            ("name", "Nombre", "text", True),
            ("modality", "Modalidad", "text", False),
            ("duration_semesters", "Semestres", "number", False),
        ],
    },
    {
        "slug": "asignaturas",
        "title": "Asignaturas",
        "entity": "subjects",
        "hint": "GET/POST /subjects",
        "cols": [
            ("id", "Id"),
            ("code", "Código"),
            ("name", "Nombre"),
            ("credits", "Créditos"),
            ("hours", "Horas"),
            ("type", "Tipo"),
            ("status", "Estado"),
        ],
        "fields": [
            ("code", "Código", "text", True),
            ("name", "Nombre", "text", True),
            ("credits", "Créditos", "number", False),
            ("hours", "Horas", "number", False),
            ("type", "Tipo", "text", False),
        ],
    },
    {
        "slug": "periodos",
        "title": "Periodos",
        "entity": "terms",
        "hint": "GET/POST /terms · PATCH status",
        "cols": [
            ("id", "Id"),
            ("code", "Código"),
            ("name", "Nombre"),
            ("start_date", "Inicio"),
            ("end_date", "Fin"),
            ("status", "Estado"),
            ("is_current", "Actual"),
        ],
        "fields": [
            ("code", "Código", "text", True),
            ("name", "Nombre", "text", True),
            ("start_date", "Inicio", "date", True),
            ("end_date", "Fin", "date", True),
            ("status", "Estado", "text", False),
        ],
        "extra": """
          <div class="card-soft mt-3">
            <h3>Cambiar estado</h3>
            <div class="row g-2 align-items-end">
              <div class="col-md-3">
                <label class="form-label" for="term-id">Periodo (id)</label>
                <input id="term-id" type="number" class="form-control" min="1" />
              </div>
              <div class="col-md-3">
                <label class="form-label" for="term-status">Estado</label>
                <select id="term-status" class="form-select">
                  <option value="PLANNED">PLANNED</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="CLOSED">CLOSED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>
              <div class="col-md-3">
                <button type="button" class="btn btn-outline-secondary" id="btn-term-status">Actualizar estado</button>
              </div>
            </div>
          </div>
        """,
    },
    {
        "slug": "estudiantes",
        "title": "Estudiantes",
        "entity": "students",
        "hint": "GET/POST /students (requiere user_id IAM)",
        "cols": [
            ("id", "Id"),
            ("user_id", "Usuario"),
            ("student_code", "Código"),
            ("career_id", "Carrera"),
            ("level", "Nivel"),
            ("status", "Estado"),
        ],
        "fields": [
            ("user_id", "User id", "number", True),
            ("student_code", "Código estudiante", "text", True),
            ("career_id", "Carrera id", "number", False),
            ("level", "Nivel", "text", False),
        ],
    },
    {
        "slug": "docentes",
        "title": "Docentes",
        "entity": "teachers",
        "hint": "GET/POST /teachers (requiere user_id IAM)",
        "cols": [
            ("id", "Id"),
            ("user_id", "Usuario"),
            ("teacher_code", "Código"),
            ("specialty", "Especialidad"),
            ("status", "Estado"),
        ],
        "fields": [
            ("user_id", "User id", "number", True),
            ("teacher_code", "Código docente", "text", True),
            ("specialty", "Especialidad", "text", False),
        ],
    },
    {
        "slug": "cursos",
        "title": "Cursos / paralelos",
        "entity": "courses",
        "hint": "GET/POST /courses",
        "cols": [
            ("id", "Id"),
            ("subject_id", "Materia"),
            ("term_id", "Periodo"),
            ("parallel_code", "Paralelo"),
            ("capacity", "Cupo"),
            ("status", "Estado"),
        ],
        "fields": [
            ("subject_id", "Subject id", "number", True),
            ("term_id", "Term id", "number", True),
            ("parallel_code", "Paralelo", "text", False),
            ("capacity", "Cupo", "number", False),
        ],
    },
    {
        "slug": "matriculas",
        "title": "Matrículas",
        "entity": "enrollments",
        "hint": "GET/POST /enrollments · cancel",
        "cols": [
            ("id", "Id"),
            ("student_id", "Estudiante"),
            ("course_id", "Curso"),
            ("term_id", "Periodo"),
            ("status", "Estado"),
        ],
        "fields": [
            ("student_id", "Student id", "number", True),
            ("course_id", "Course id", "number", True),
            ("term_id", "Term id", "number", True),
        ],
        "extra": """
          <div class="card-soft mt-3">
            <h3>Cancelar matrícula</h3>
            <div class="row g-2 align-items-end">
              <div class="col-md-3">
                <label class="form-label" for="enroll-cancel-id">Matrícula (id)</label>
                <input id="enroll-cancel-id" type="number" class="form-control" min="1" />
              </div>
              <div class="col-md-3">
                <button type="button" class="btn btn-outline-secondary" id="btn-enroll-cancel">Cancelar</button>
              </div>
            </div>
          </div>
        """,
    },
]


def sidebar(active: str) -> str:
    marks = {e["slug"]: "" for e in ENTITIES}
    marks[active] = " active"
    out = SIDEBAR
    for k, v in marks.items():
        out = out.replace("{" + k + "}", v)
    return out


def fields_html(fields: list) -> str:
    chunks = []
    for name, label, typ, required in fields:
        req = " required" if required else ""
        chunks.append(
            f"""
            <div class="col-md-3">
              <label class="form-label" for="f-{name}">{label}</label>
              <input id="f-{name}" name="{name}" type="{typ}" class="form-control" data-field="{name}"{req} />
            </div>"""
        )
    return "\n".join(chunks)


def thead_html(cols: list) -> str:
    return "".join(f"<th scope=\"col\">{label}</th>" for _, label in cols)


def page(entity: dict) -> str:
    slug = entity["slug"]
    extra = entity.get("extra", "")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{entity["title"]} · Catálogos · SIGA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
{CSS}
</head>
<body data-entity="{entity["entity"]}">
  <div id="toast" class="siga-toast" role="status" aria-live="polite"></div>
  <div class="app-frame">
{sidebar(slug)}
    <div class="app-main">
      <header class="app-topbar">
        <button type="button" id="btn-sidebar" class="btn-sidebar" aria-expanded="false" aria-label="Abrir menú">Menú</button>
        <h1 class="topbar-title">{entity["title"]}</h1>
        <div class="topbar-actions">
          <a href="/ui/pages/cuenta/perfil.html" id="session-chip" class="siga-chip muted">Sin sesión</a>
          <a class="btn btn-outline-secondary btn-sm" href="/ui/pages/catalogos/catalogos.html">Índice</a>
          <button type="button" id="btn-logout" class="btn btn-outline-secondary btn-sm">Cerrar sesión</button>
        </div>
      </header>
      <nav class="breadcrumb" aria-label="Miga de pan">
        <a href="/ui/pages/dashboard/dashboard.html">Dashboard</a>
        <span class="sep">/</span>
        <a href="/ui/pages/catalogos/catalogos.html">Catálogos</a>
        <span class="sep">/</span>
        <span>{entity["title"]}</span>
      </nav>
      <main class="app-content">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Catálogo</p>
            <p class="hint">{entity["hint"]}. Tabla con thead en HTML.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-refresh-catalog">Actualizar</button>
        </div>

        <section class="card-soft mb-3">
          <h3>Alta</h3>
          <form id="catalog-create-form" class="row g-2 align-items-end" novalidate>
{fields_html(entity["fields"])}
            <div class="col-md-3">
              <button type="submit" class="btn btn-siga w-100">Crear</button>
            </div>
          </form>
          <p id="create-out" class="hint mt-2 mb-0"></p>
        </section>
{extra}
        <section class="table-wrap mt-3">
          <p class="empty-state mb-0" data-empty>Cargando…</p>
          <table class="table table-sm table-hover align-middle data-table">
            <thead>
              <tr>{thead_html(entity["cols"])}</tr>
            </thead>
            <tbody id="catalog-tbody"></tbody>
          </table>
        </section>
      </main>
    </div>
  </div>
{SCRIPTS}
</body>
</html>
"""


INDEX = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Catálogos · SIGA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
{CSS}
</head>
<body>
  <div id="toast" class="siga-toast" role="status" aria-live="polite"></div>
  <div class="app-frame">
{sidebar("")}
    <div class="app-main">
      <header class="app-topbar">
        <button type="button" id="btn-sidebar" class="btn-sidebar" aria-expanded="false" aria-label="Abrir menú">Menú</button>
        <h1 class="topbar-title">Catálogos</h1>
        <div class="topbar-actions">
          <a href="/ui/pages/cuenta/perfil.html" id="session-chip" class="siga-chip muted">Sin sesión</a>
          <a class="btn btn-outline-secondary btn-sm" href="/ui/pages/cuenta/perfil.html">Perfil</a>
          <button type="button" id="btn-logout" class="btn btn-outline-secondary btn-sm">Cerrar sesión</button>
        </div>
      </header>
      <nav class="breadcrumb" aria-label="Miga de pan">
        <a href="/ui/pages/dashboard/dashboard.html">Dashboard</a>
        <span class="sep">/</span>
        <span>Catálogos</span>
      </nav>
      <main class="app-content">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Administración</p>
            <p class="hint">Una pantalla por entidad. Solo administrador.</p>
          </div>
        </div>
        <div class="dash-shortcuts" id="catalog-index">
          <a class="dash-shortcut" href="/ui/pages/catalogos/carreras.html"><strong>Carreras</strong><span>Código, modalidad, duración</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/asignaturas.html"><strong>Asignaturas</strong><span>Materias y créditos</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/periodos.html"><strong>Periodos</strong><span>Términos académicos</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/estudiantes.html"><strong>Estudiantes</strong><span>Perfiles académicos</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/docentes.html"><strong>Docentes</strong><span>Perfiles y especialidad</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/cursos.html"><strong>Cursos</strong><span>Paralelos ofertados</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/matriculas.html"><strong>Matrículas</strong><span>Inscripción a cursos</span></a>
        </div>
      </main>
    </div>
  </div>
  <script src="/ui/assets/js/core/api.js"></script>
  <script src="/ui/assets/js/components/toast.js"></script>
  <script src="/ui/assets/js/components/table.js"></script>
  <script src="/ui/assets/js/core/navigation.js"></script>
  <script src="/ui/assets/js/core/auth.js"></script>
  <script>
    (async function () {{
      if (!(await SigaAuth.requireAuth())) return;
      const roles = (SigaApi.state.user && SigaApi.state.user.roles) || [];
      if (!roles.includes("ADMINISTRATOR")) {{
        location.replace("/ui/pages/dashboard/dashboard.html");
      }}
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    (PAGES / "catalogos.html").write_text(INDEX, encoding="utf-8")
    for ent in ENTITIES:
        path = PAGES / f"{ent['slug']}.html"
        path.write_text(page(ent), encoding="utf-8")
        print("wrote", path.relative_to(ROOT))
    print("OK F7 catalog pages")


if __name__ == "__main__":
    main()
