# Replace pre-PromptMaster /ui/js and /ui/css with thin shims → assets/
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "frontend"
JS = ROOT / "js"
CSS = ROOT / "css"

CORE = {
    "api.js": "/ui/assets/js/core/api.js",
    "auth-guard.js": "/ui/assets/js/core/auth.js",
    "ui-common.js": "/ui/assets/js/components/toast.js",
    "app.js": None,
}

PAGES = {
    "ai.js": "/ui/pages/asistente/asistente.html",
    "attendance.js": "/ui/pages/asistencia/asistencia.html",
    "catalog.js": "/ui/pages/catalogos/catalogos.html",
    "dashboard.js": "/ui/pages/dashboard/dashboard.html",
    "grades.js": "/ui/pages/notas/notas.html",
    "login.js": "/ui/pages/auth/login.html",
    "notifications.js": "/ui/pages/avisos/avisos.html",
    "profile.js": "/ui/pages/cuenta/perfil.html",
    "reports.js": "/ui/pages/reportes/reportes.html",
}


def shim_load(target: str) -> str:
    return (
        "/* DEPRECATED — PromptMaster F2+: use assets/. Auto-loads canonical script. */\n"
        "(function () {\n"
        f'  var src = "{target}";\n'
        "  if (document.querySelector('script[data-siga-shim=\"' + src + '\"]')) return;\n"
        "  var s = document.createElement('script');\n"
        "  s.src = src;\n"
        "  s.async = false;\n"
        '  s.dataset.sigaShim = src;\n'
        "  document.head.appendChild(s);\n"
        "})();\n"
    )


def shim_page(url: str, name: str) -> str:
    return (
        f"/* DEPRECATED — /ui/js/pages/{name} removed. Canonical UI: {url} */\n"
        f'console.warn("[SIGA] Legacy /ui/js/pages/{name} — open {url}");\n'
    )


def main() -> None:
    JS.mkdir(parents=True, exist_ok=True)
    (JS / "pages").mkdir(parents=True, exist_ok=True)
    CSS.mkdir(parents=True, exist_ok=True)

    (JS / "api.js").write_text(shim_load(CORE["api.js"]), encoding="utf-8")
    (JS / "auth-guard.js").write_text(shim_load(CORE["auth-guard.js"]), encoding="utf-8")
    (JS / "ui-common.js").write_text(
        "/* DEPRECATED — PromptMaster F2+: use /ui/assets/js/components/{toast,table}.js */\n"
        "(function () {\n"
        "  function load(src) {\n"
        "    if (document.querySelector('script[data-siga-shim=\"' + src + '\"]')) return;\n"
        "    var s = document.createElement('script');\n"
        "    s.src = src;\n"
        "    s.async = false;\n"
        "    s.dataset.sigaShim = src;\n"
        "    document.head.appendChild(s);\n"
        "  }\n"
        '  load("/ui/assets/js/components/toast.js");\n'
        '  load("/ui/assets/js/components/table.js");\n'
        "})();\n",
        encoding="utf-8",
    )
    (JS / "app.js").write_text(
        "/* DEPRECATED — SPA router removed (A01 / PromptMaster). */\n"
        'console.warn("[SIGA] Use /ui/pages/*.html — no hash router.");\n',
        encoding="utf-8",
    )

    for name, url in PAGES.items():
        (JS / "pages" / name).write_text(shim_page(url, name), encoding="utf-8")

    (CSS / "main.css").write_text(
        "/* DEPRECATED — use /ui/assets/css/*.css */\n"
        '@import url("/ui/assets/css/base.css");\n'
        '@import url("/ui/assets/css/layout.css");\n'
        '@import url("/ui/assets/css/components.css");\n'
        '@import url("/ui/assets/css/forms.css");\n'
        '@import url("/ui/assets/css/tables.css");\n'
        '@import url("/ui/assets/css/responsive.css");\n',
        encoding="utf-8",
    )

    (JS / "README.md").write_text(
        "# Legacy `/ui/js` (deprecated)\n\n"
        "Canonical frontend: `/ui/assets/js/` + `/ui/pages/`.\n\n"
        "These files remain as **shims** so old bookmarks do not 404.\n",
        encoding="utf-8",
    )
    print("legacy shims written")


if __name__ == "__main__":
    main()
