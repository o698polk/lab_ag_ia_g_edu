"""Inject admin CSS/JS and standardize catalog module shells."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "app" / "frontend" / "pages"

CSS_LINE = '  <link rel="stylesheet" href="/ui/assets/css/admin.css" />\n'
JS_MODAL = '  <script src="/ui/assets/js/components/modal.js"></script>\n'
JS_TABLE = '  <script src="/ui/assets/js/components/admin-table.js"></script>\n'

TOOLBAR = """
        <div class="module-head">
          <h2>Administración de registros</h2>
          <p>Tabla principal. Las operaciones se realizan en ventanas emergentes.</p>
        </div>
        <div class="admin-toolbar">
          <button type="button" class="btn btn-siga" id="btn-new-record">+ Nuevo</button>
          <input id="admin-search" class="form-control admin-search" type="search" placeholder="Buscar..." />
          <select id="admin-filter" class="form-select admin-filter" aria-label="Filtro de estado">
            <option value="">Todos los estados</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="PLANNED">PLANNED</option>
            <option value="CLOSED">CLOSED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
          <button type="button" class="btn btn-outline-secondary" id="btn-refresh-catalog">Actualizar</button>
        </div>
"""

PAGER = '          <div class="admin-pager" id="admin-pager"></div>\n'


def inject_assets(html: str) -> str:
    if "admin.css" not in html and "tables.css" in html:
        html = html.replace(
            '<link rel="stylesheet" href="/ui/assets/css/tables.css" />',
            '<link rel="stylesheet" href="/ui/assets/css/tables.css" />\n' + CSS_LINE.rstrip() + "\n",
        )
    if "admin-table.js" not in html and "table.js" in html:
        html = html.replace(
            '<script src="/ui/assets/js/components/table.js"></script>',
            '<script src="/ui/assets/js/components/table.js"></script>\n'
            + JS_MODAL
            + JS_TABLE,
        )
    return html


def ensure_acciones(html: str) -> str:
    if "Acciones" in html:
        return html
    # last </tr> in thead
    marker = "</tr>\n            </thead>"
    if marker in html:
        html = html.replace(
            marker,
            '<th scope="col">Acciones</th></tr>\n            </thead>',
            1,
        )
        return html
    marker2 = "</thead>"
    if "<thead>" in html and "Acciones" not in html:
        html = html.replace("</tr>\n            </thead>", '<th scope="col">Acciones</th></tr>\n            </thead>', 1)
    return html


def transform_catalog(html: str) -> str:
    html = inject_assets(html)
    if 'id="btn-new-record"' not in html:
        html = html.replace('<main class="app-content">', '<main class="app-content">' + TOOLBAR, 1)
    if 'id="admin-pager"' not in html and 'id="catalog-tbody"' in html:
        html = html.replace(
            "</table>\n        </section>",
            "</table>\n" + PAGER + "        </section>",
            1,
        )
    html = ensure_acciones(html)
    # hide inline alta card visually but keep form
    html = html.replace(
        '<section class="card-soft mb-3">\n          <h3>Alta</h3>',
        '<section class="card-soft mb-3 d-none" id="catalog-create-wrap">\n          <h3>Alta</h3>',
        1,
    )
    html = html.replace('class="card-soft mt-3"', 'class="card-soft mt-3 d-none admin-extra"', 1)
    return html


def transform_generic(html: str) -> str:
    return inject_assets(html)


def main() -> None:
    catalog_dir = PAGES / "catalogos"
    for path in catalog_dir.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        if path.name == "catalogos.html":
            path.write_text(transform_generic(text), encoding="utf-8")
            continue
        path.write_text(transform_catalog(text), encoding="utf-8")
        print("catalog", path.name)

    for folder in (
        "dashboard",
        "notas",
        "asistencia",
        "reportes",
        "usuarios",
        "avisos",
        "asistente",
        "cuenta",
        "seguridad",
    ):
        d = PAGES / folder
        if not d.is_dir():
            continue
        for path in d.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            path.write_text(transform_generic(text), encoding="utf-8")
            print("page", path.relative_to(PAGES))


if __name__ == "__main__":
    main()
