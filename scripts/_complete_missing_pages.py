# Generate missing catalog entity pages from the carreras template.
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "frontend" / "pages" / "catalogos"
SRC = (ROOT / "carreras.html").read_text(encoding="utf-8")

PAGES = {
    "mallas.html": {
        "title": "Mallas",
        "entity": "curricula",
        "hint": "GET/POST /curricula y POST /curricula/{id}/subjects.",
        "fields": [
            ("career_id", "Carrera (id)", "number"),
            ("version", "Versión", "text"),
        ],
        "ths": ["Id", "Carrera", "Versión", "Estado", "Asignaturas"],
        "extra": """
          <div class="card-soft mt-3">
            <h3>Agregar asignatura a malla</h3>
            <div class="row g-2 align-items-end">
              <div class="col-md-2"><label class="form-label" for="cur-id">Malla (id)</label><input id="cur-id" type="number" class="form-control" min="1" /></div>
              <div class="col-md-2"><label class="form-label" for="cur-subject-id">Asignatura (id)</label><input id="cur-subject-id" type="number" class="form-control" min="1" /></div>
              <div class="col-md-2"><label class="form-label" for="cur-level">Nivel</label><input id="cur-level" type="number" class="form-control" value="1" /></div>
              <div class="col-md-2"><label class="form-label" for="cur-semester">Semestre</label><input id="cur-semester" type="number" class="form-control" value="1" /></div>
              <div class="col-md-3"><button type="button" class="btn btn-outline-secondary" id="btn-cur-subject">Agregar</button></div>
            </div>
          </div>
        """,
    },
    "aulas.html": {
        "title": "Aulas",
        "entity": "classrooms",
        "hint": "GET/POST /classrooms.",
        "fields": [
            ("code", "Código", "text"),
            ("name", "Nombre", "text"),
            ("capacity", "Capacidad", "number"),
        ],
        "ths": ["Id", "Código", "Nombre", "Capacidad"],
        "extra": "",
    },
    "horarios.html": {
        "title": "Horarios",
        "entity": "schedules",
        "hint": "GET/POST /schedules.",
        "fields": [
            ("course_id", "Curso (id)", "number"),
            ("teacher_id", "Docente (id)", "number"),
            ("classroom_id", "Aula (id)", "number"),
            ("term_id", "Periodo (id)", "number"),
            ("day_of_week", "Día", "text"),
            ("start_time", "Inicio", "time"),
            ("end_time", "Fin", "time"),
        ],
        "ths": ["Id", "Curso", "Docente", "Aula", "Periodo", "Día", "Inicio", "Fin"],
        "extra": "",
    },
    "asignaciones.html": {
        "title": "Asignaciones",
        "entity": "assignments",
        "hint": "GET/POST /teaching-assignments.",
        "fields": [
            ("teacher_id", "Docente (id)", "number"),
            ("course_id", "Curso (id)", "number"),
            ("term_id", "Periodo (id)", "number"),
        ],
        "ths": ["Id", "Docente", "Curso", "Periodo", "Estado"],
        "extra": "",
    },
}


def fields_html(fields):
    parts = []
    for name, label, typ in fields:
        parts.append(
            f"""
            <div class="col-md-3">
              <label class="form-label" for="f-{name}">{label}</label>
              <input id="f-{name}" name="{name}" type="{typ}" class="form-control" data-field="{name}" required />
            </div>"""
        )
    parts.append(
        """
            <div class="col-md-3">
              <button type="submit" class="btn btn-siga w-100">Crear</button>
            </div>"""
    )
    return "\n".join(parts)


def main() -> None:
    for filename, spec in PAGES.items():
        html = SRC
        html = html.replace("Carreras · Catálogos · SIGA", f"{spec['title']} · Catálogos · SIGA")
        html = html.replace('data-entity="careers"', f'data-entity="{spec["entity"]}"')
        html = html.replace("<h1 class=\"topbar-title\">Carreras</h1>", f"<h1 class=\"topbar-title\">{spec['title']}</h1>")
        html = html.replace("<span>Carreras</span>", f"<span>{spec['title']}</span>")
        html = html.replace("GET/POST /careers. Tabla con thead en HTML.", spec["hint"])
        html = html.replace(
            'href="/ui/pages/catalogos/carreras.html">Carreras</a>',
            f'href="/ui/pages/catalogos/{filename}">{spec["title"]}</a>',
        )
        # form fields: replace inner of catalog-create-form
        start = html.find('<form id="catalog-create-form"')
        end = html.find("</form>", start) + len("</form>")
        form = f"""<form id="catalog-create-form" class="row g-2 align-items-end" novalidate>
{fields_html(spec["fields"])}
          </form>"""
        html = html[:start] + form + html[end:]
        ths = "".join(f'<th scope="col">{h}</th>' for h in spec["ths"])
        html = html.replace(
            "<tr><th scope=\"col\">Id</th><th scope=\"col\">Código</th><th scope=\"col\">Nombre</th><th scope=\"col\">Modalidad</th><th scope=\"col\">Semestres</th><th scope=\"col\">Estado</th></tr>",
            f"<tr>{ths}</tr>",
        )
        if spec["extra"]:
            html = html.replace(
                '<p id="create-out" class="hint mt-2 mb-0"></p>\n        </section>',
                '<p id="create-out" class="hint mt-2 mb-0"></p>\n        </section>\n'
                + spec["extra"],
            )
        (ROOT / filename).write_text(html, encoding="utf-8")
        print("wrote", filename)

    index = ROOT / "catalogos.html"
    text = index.read_text(encoding="utf-8")
    extra_cards = """
          <a class="dash-shortcut" href="/ui/pages/catalogos/mallas.html"><strong>Mallas</strong><span>Currículo por carrera</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/aulas.html"><strong>Aulas</strong><span>Aulas y capacidad</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/horarios.html"><strong>Horarios</strong><span>Día y franja</span></a>
          <a class="dash-shortcut" href="/ui/pages/catalogos/asignaciones.html"><strong>Asignaciones</strong><span>Docente ↔ curso</span></a>"""
    if "mallas.html" not in text:
        text = text.replace(
            '<a class="dash-shortcut" href="/ui/pages/catalogos/matriculas.html"><strong>Matrículas</strong><span>Inscripción a cursos</span></a>',
            '<a class="dash-shortcut" href="/ui/pages/catalogos/matriculas.html"><strong>Matrículas</strong><span>Inscripción a cursos</span></a>'
            + extra_cards,
        )
        index.write_text(text, encoding="utf-8")
        print("updated catalogos.html")


if __name__ == "__main__":
    main()
