# Ref: RF-AUTH / RNF-UX / PromptMaster F2+F3 | Skill: K-006/K-022
"""Multi-page UI with assets/ layout — API + structure tests."""

from pathlib import Path

import pytest

FRONTEND = Path(__file__).resolve().parents[2] / "app" / "frontend"
PAGES = FRONTEND / "pages"
ASSETS = FRONTEND / "assets"


@pytest.mark.unit
def test_home_ui_served(client):
    res = client.get("/ui/pages/home.html")
    assert res.status_code == 200
    assert "Laboratorio Zero Trust" in res.text
    assert 'href="/ui/pages/auth/login.html"' in res.text


@pytest.mark.unit
def test_root_redirects_to_ui(client):
    res = client.get("/", follow_redirects=False)
    assert res.status_code in (307, 302)
    assert "/ui/pages/home.html" in res.headers.get("location", "")


@pytest.mark.unit
def test_login_ok_reaches_me_and_dashboard(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    dash = client.get("/api/v1/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["role_view"] == "ADMINISTRATOR"


@pytest.mark.unit
def test_login_incorrect_credentials_message(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-pass"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "INVALID_CREDENTIALS"


@pytest.mark.unit
def test_login_unknown_user(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "no-existe", "password": "Admin123!"},
    )
    assert res.status_code == 401


@pytest.mark.unit
def test_login_empty_rejected(client):
    res = client.post("/api/v1/auth/login", json={"username": "", "password": ""})
    assert res.status_code == 422


@pytest.mark.unit
def test_jwt_valid_me_after_reissue_refresh(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_headers = {"Authorization": f"Bearer {refreshed.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=new_headers).status_code == 200


@pytest.mark.unit
def test_jwt_invalid_rejected(client):
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer totally-invalid-token"},
    )
    assert res.status_code == 401


@pytest.mark.unit
def test_protected_without_session(client):
    assert client.get("/api/v1/dashboard").status_code == 401
    assert client.get("/api/v1/me/grades").status_code == 401


@pytest.mark.unit
def test_logout_invalidates_refresh(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    ).json()
    out = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
    )
    assert out.status_code == 204
    again = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert again.status_code == 401


@pytest.mark.unit
def test_register_user_admin_ok_student_denied(client, admin_token, student_token):
    created = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "navuser1",
            "email": "navuser1@siga.local",
            "password": "NavUser123!",
            "role_codes": ["STUDENT"],
        },
    )
    assert created.status_code == 201
    denied = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "username": "navuser2",
            "email": "navuser2@siga.local",
            "password": "NavUser123!",
            "role_codes": ["STUDENT"],
        },
    )
    assert denied.status_code == 403


@pytest.mark.unit
def test_module_routes_with_session(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.get("/api/v1/dashboard", headers=headers).status_code == 200
    assert client.get("/api/v1/courses", headers=headers).status_code == 200
    assert client.get("/api/v1/notifications", headers=headers).status_code == 200
    assert client.get("/api/v1/reports/logs", headers=headers).status_code == 200


@pytest.mark.unit
def test_ui_f2f3_architecture():
    """PromptMaster F2+F3: assets/, modular pages/, sidebar layout, no SPA router."""
    expected_pages = [
        PAGES / "home.html",
        PAGES / "auth" / "login.html",
        PAGES / "auth" / "registro.html",
        PAGES / "dashboard" / "dashboard.html",
        PAGES / "notas" / "notas.html",
        PAGES / "asistencia" / "asistencia.html",
        PAGES / "catalogos" / "catalogos.html",
        PAGES / "reportes" / "reportes.html",
        PAGES / "avisos" / "avisos.html",
        PAGES / "asistente" / "asistente.html",
        PAGES / "cuenta" / "perfil.html",
    ]
    for path in expected_pages:
        assert path.is_file(), f"missing {path}"

    for name in ("base.css", "layout.css", "components.css", "forms.css", "tables.css", "responsive.css"):
        assert (ASSETS / "css" / name).is_file()

    for name in ("api.js", "auth.js", "navigation.js"):
        assert (ASSETS / "js" / "core" / name).is_file()
    assert (ASSETS / "js" / "components" / "table.js").is_file()
    assert (ASSETS / "js" / "components" / "toast.js").is_file()

    dash = (PAGES / "dashboard" / "dashboard.html").read_text(encoding="utf-8")
    assert "app-sidebar" in dash
    assert "breadcrumb" in dash
    assert "/ui/assets/css/layout.css" in dash
    assert 'data-metric="students"' in dash

    notas = (PAGES / "notas" / "notas.html").read_text(encoding="utf-8")
    assert 'id="grades-tbody"' in notas
    assert "<thead>" in notas

    login_js = (ASSETS / "js" / "modules" / "auth" / "login.js").read_text(encoding="utf-8")
    assert "Credenciales incorrectas. Verifica tu usuario y contraseña." in login_js

    auth_js = (ASSETS / "js" / "core" / "auth.js").read_text(encoding="utf-8")
    assert "requireAuth" in auth_js
    assert "hashchange" not in auth_js

    table_js = (ASSETS / "js" / "components" / "table.js").read_text(encoding="utf-8")
    assert "fillTbody" in table_js


@pytest.mark.unit
def test_ui_f4_dashboard_polish():
    """PromptMaster FASE 4: welcome, full metrics, shortcuts, avisos, history table."""
    dash = (PAGES / "dashboard" / "dashboard.html").read_text(encoding="utf-8")
    assert "dash-welcome" in dash
    assert "dash-shortcuts" in dash
    assert 'id="history-tbody"' in dash
    assert "<thead>" in dash
    assert 'data-metric="attendance_sessions"' in dash
    assert 'data-metric="careers"' in dash
    assert 'data-metric="grades_recorded"' in dash
    assert 'data-metric="my_kardex"' in dash
    assert 'id="dash-notif-list"' in dash

    js = (ASSETS / "js" / "modules" / "dashboard" / "dashboard.js").read_text(encoding="utf-8")
    assert 'api("GET", "/dashboard")' in js
    assert 'api("GET", "/notifications")' in js
    assert 'api("GET", "/me/history")' in js
    assert "fillTbody" in js
    assert "innerHTML" not in js

    css = (ASSETS / "css" / "components.css").read_text(encoding="utf-8")
    assert ".dash-welcome" in css
    assert ".dash-shortcut" in css


@pytest.mark.unit
def test_ui_f5_notas_cascade():
    """PromptMaster FASE 5: carrera → periodo → paralelo + ingreso page."""
    notas = (PAGES / "notas" / "notas.html").read_text(encoding="utf-8")
    assert 'id="filter-career"' in notas
    assert 'id="filter-term"' in notas
    assert 'id="filter-parallel"' in notas
    assert 'id="grades-tbody"' in notas
    assert 'id="kardex-tbody"' in notas
    assert "<thead>" in notas
    assert "filter-cascade" in notas

    ingreso = PAGES / "notas" / "ingreso-notas.html"
    assert ingreso.is_file()
    ingreso_html = ingreso.read_text(encoding="utf-8")
    assert 'id="filter-parallel"' in ingreso_html
    assert 'id="btn-upsert-grade"' in ingreso_html

    js = (ASSETS / "js" / "modules" / "notas" / "notas.js").read_text(encoding="utf-8")
    assert 'api("GET", "/careers")' in js
    assert 'api("GET", "/terms")' in js
    assert 'api("GET", "/courses")' in js
    assert 'api("PUT", "/grades"' in js
    assert 'api("GET", "/me/grades")' in js
    assert "filter-career" in js
    assert "filter-parallel" in js

    forms = (ASSETS / "css" / "forms.css").read_text(encoding="utf-8")
    assert ".filter-cascade" in forms


@pytest.mark.unit
def test_ui_f6_asistencia_cascade():
    """PromptMaster FASE 6: asistencia cascade + registro rápido."""
    page = (PAGES / "asistencia" / "asistencia.html").read_text(encoding="utf-8")
    assert 'id="filter-career"' in page
    assert 'id="filter-term"' in page
    assert 'id="filter-parallel"' in page
    assert 'id="btn-create-session"' in page
    assert 'id="btn-mark-att"' in page
    assert 'id="sessions-tbody"' in page
    assert 'id="marks-tbody"' in page
    assert "<thead>" in page

    registro = PAGES / "asistencia" / "registro.html"
    assert registro.is_file()
    reg = registro.read_text(encoding="utf-8")
    assert 'id="filter-parallel"' in reg
    assert 'id="btn-create-session"' in reg

    js = (ASSETS / "js" / "modules" / "asistencia" / "asistencia.js").read_text(encoding="utf-8")
    assert 'api("POST", "/attendance/sessions"' in js
    assert 'api("PUT", "/attendance/records"' in js
    assert "/attendance/courses/" in js
    assert "filter-career" in js
    assert "filter-parallel" in js


@pytest.mark.unit
def test_ui_f7_catalogos_por_entidad():
    """PromptMaster FASE 7: una HTML por entidad + entity.js."""
    entities = [
        "carreras",
        "asignaturas",
        "periodos",
        "estudiantes",
        "docentes",
        "cursos",
        "matriculas",
    ]
    index = (PAGES / "catalogos" / "catalogos.html").read_text(encoding="utf-8")
    assert "catalog-index" in index or "dash-shortcuts" in index
    for slug in entities:
        path = PAGES / "catalogos" / f"{slug}.html"
        assert path.is_file(), f"missing {path}"
        html = path.read_text(encoding="utf-8")
        assert "data-entity=" in html
        assert 'id="catalog-tbody"' in html
        assert "<thead>" in html
        assert 'id="catalog-create-form"' in html
        assert "/ui/assets/js/modules/catalogos/entity.js" in html

    js = (ASSETS / "js" / "modules" / "catalogos" / "entity.js").read_text(encoding="utf-8")
    assert 'path: "/careers"' in js
    assert 'path: "/subjects"' in js
    assert 'path: "/terms"' in js
    assert 'path: "/students"' in js
    assert 'path: "/teachers"' in js
    assert 'path: "/courses"' in js
    assert 'path: "/enrollments"' in js
    assert 'api("POST"' in js
    assert "ADMINISTRATOR" in js

    carreras = (PAGES / "catalogos" / "carreras.html").read_text(encoding="utf-8")
    assert 'data-entity="careers"' in carreras
    assert "Código" in carreras

    periodos = (PAGES / "catalogos" / "periodos.html").read_text(encoding="utf-8")
    assert 'id="btn-term-status"' in periodos

    matriculas = (PAGES / "catalogos" / "matriculas.html").read_text(encoding="utf-8")
    assert 'id="btn-enroll-cancel"' in matriculas


@pytest.mark.unit
def test_ui_f8_reportes_categorias():
    """PromptMaster FASE 8: categorías, preview, logs table."""
    page = (PAGES / "reportes" / "reportes.html").read_text(encoding="utf-8")
    assert 'id="report-categories"' in page
    assert 'data-group="people"' in page
    assert 'data-group="academic"' in page
    assert 'data-group="ops"' in page
    assert 'id="report-type"' in page
    assert 'id="report-format"' in page
    assert 'id="btn-report"' in page
    assert 'id="logs-tbody"' in page
    assert 'id="preview-tbody"' in page
    assert "<thead>" in page
    assert 'id="param-term-id"' in page
    assert 'id="param-student-id"' in page

    js = (ASSETS / "js" / "modules" / "reportes" / "reportes.js").read_text(encoding="utf-8")
    assert 'api("GET", "/reports/catalog")' in js
    assert 'api("POST", "/reports"' in js
    assert 'api("GET", "/reports/logs")' in js
    assert "showPreview" in js
    assert "term_academic" in js

    css = (ASSETS / "css" / "components.css").read_text(encoding="utf-8")
    assert ".report-categories" in css
    assert ".report-preview-html" in css


@pytest.mark.unit
def test_ui_f9_usuarios_roles():
    """PromptMaster FASE 9: usuarios, roles/permisos, perfil password."""
    usuarios = PAGES / "usuarios" / "usuarios.html"
    roles = PAGES / "usuarios" / "roles.html"
    assert usuarios.is_file()
    assert roles.is_file()

    uh = usuarios.read_text(encoding="utf-8")
    assert 'id="users-tbody"' in uh
    assert 'id="user-create-form"' in uh
    assert 'id="btn-user-roles"' in uh
    assert "<thead>" in uh

    rh = roles.read_text(encoding="utf-8")
    assert 'id="roles-tbody"' in rh
    assert 'id="perms-tbody"' in rh
    assert 'id="btn-assign-perms"' in rh

    ujs = (ASSETS / "js" / "modules" / "usuarios" / "usuarios.js").read_text(encoding="utf-8")
    assert 'api("GET", "/users")' in ujs
    assert 'api("POST", "/users"' in ujs
    assert "/users/" in ujs
    assert "ADMINISTRATOR" in ujs

    rjs = (ASSETS / "js" / "modules" / "usuarios" / "roles.js").read_text(encoding="utf-8")
    assert 'api("GET", "/roles")' in rjs
    assert 'api("GET", "/permissions")' in rjs
    assert "/permissions" in rjs

    perfil = (PAGES / "cuenta" / "perfil.html").read_text(encoding="utf-8")
    assert 'id="pf-permissions"' in perfil
    assert 'id="change-password-form"' in perfil

    pjs = (ASSETS / "js" / "modules" / "cuenta" / "perfil.js").read_text(encoding="utf-8")
    assert 'api("POST", "/auth/change-password"' in pjs
    assert "pf-permissions" in pjs

    nav = (ASSETS / "js" / "core" / "navigation.js").read_text(encoding="utf-8")
    assert "ensureAdminNav" in nav
    assert "/ui/pages/usuarios/usuarios.html" in nav

    auth = (ASSETS / "js" / "core" / "auth.js").read_text(encoding="utf-8")
    assert "ensureAdminNav" in auth


@pytest.mark.unit
def test_ui_f10_a11y_responsive():
    """PromptMaster FASE 10: skip-link, focus, toast a11y, reduced-motion."""
    css = (ASSETS / "css" / "responsive.css").read_text(encoding="utf-8")
    assert ".skip-link" in css
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert "prefers-contrast" in css
    assert ".nav-backdrop" in css
    assert "min-height: 44px" in css

    nav = (ASSETS / "js" / "core" / "navigation.js").read_text(encoding="utf-8")
    assert "ensureSkipLink" in nav
    assert "nav-backdrop" in nav
    assert 'ev.key === "Escape"' in nav
    assert "ensureSkipLink()" in nav

    toast = (ASSETS / "js" / "components" / "toast.js").read_text(encoding="utf-8")
    assert 'kind === "bad" ? "alert"' in toast
    assert "assertive" in toast

    home = (PAGES / "home.html").read_text(encoding="utf-8")
    assert 'class="skip-link"' in home
    assert 'id="gate-main"' in home
    assert 'lang="es"' in home

    login = (PAGES / "auth" / "login.html").read_text(encoding="utf-8")
    assert 'class="skip-link"' in login
    assert 'href="#gate-main"' in login

    checklist = (
        Path(__file__).resolve().parents[2]
        / "evidence"
        / "verify"
        / "UX-F10-CHECKLIST.md"
    )
    assert checklist.is_file()
    assert "FASE 10" in checklist.read_text(encoding="utf-8")

    # Protected shell pages load responsive CSS
    dash = (PAGES / "dashboard" / "dashboard.html").read_text(encoding="utf-8")
    assert "responsive.css" in dash
    assert 'lang="es"' in dash


@pytest.mark.unit
def test_ui_f10_avisos_asistente_polish():
    """Cierre deuda post-F10: avisos (filtro + alta admin) y asistente a11y."""
    avisos = (PAGES / "avisos" / "avisos.html").read_text(encoding="utf-8")
    assert 'id="filt-unread"' in avisos
    assert 'id="notif-create-form"' in avisos
    assert 'id="ntf-user"' in avisos
    assert 'data-roles="ADMINISTRATOR"' in avisos

    ajs = (ASSETS / "js" / "modules" / "avisos" / "avisos.js").read_text(encoding="utf-8")
    assert 'api("GET", "/notifications"' in ajs
    assert 'api("POST", "/notifications"' in ajs
    assert "unread_only" in ajs
    assert 'api("GET", "/users")' in ajs

    asi = (PAGES / "asistente" / "asistente.html").read_text(encoding="utf-8")
    assert 'for="ai-message"' in asi
    assert 'id="ai-status"' in asi
    assert 'id="ai-empty"' in asi

    aijs = (ASSETS / "js" / "modules" / "asistente" / "asistente.js").read_text(
        encoding="utf-8"
    )
    assert 'api("POST", "/ai/chat"' in aijs
    assert "textContent" in aijs
    assert "setBusy" in aijs

    # Legacy stubs still redirect
    assert "asistente/asistente.html" in (PAGES / "ai.html").read_text(encoding="utf-8")
    assert "avisos/avisos.html" in (PAGES / "notifications.html").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_ui_legacy_js_css_shims():
    """Legacy /ui/js and /ui/css are shims → assets (no dual implementation)."""
    legacy_js = FRONTEND / "js"
    assert "DEPRECATED" in (legacy_js / "app.js").read_text(encoding="utf-8")
    assert "/ui/assets/js/core/api.js" in (legacy_js / "api.js").read_text(
        encoding="utf-8"
    )
    assert "/ui/assets/js/core/auth.js" in (legacy_js / "auth-guard.js").read_text(
        encoding="utf-8"
    )
    ai = (legacy_js / "pages" / "ai.js").read_text(encoding="utf-8")
    assert "DEPRECATED" in ai
    assert "/ui/pages/asistente/asistente.html" in ai

    css = (FRONTEND / "css" / "main.css").read_text(encoding="utf-8")
    assert "@import" in css
    assert "/ui/assets/css/base.css" in css

    # Live pages must not reference legacy /ui/js
    dash = (PAGES / "dashboard" / "dashboard.html").read_text(encoding="utf-8")
    assert "/ui/assets/js/" in dash
    assert "/ui/js/" not in dash


@pytest.mark.unit
def test_ui_complete_missing_functions():
    """Páginas y JS para APIs que estaban sin UI o incompletas."""
    recover = PAGES / "auth" / "recuperar.html"
    assert recover.is_file()
    recover_html = recover.read_text(encoding="utf-8")
    assert 'id="forgot-form"' in recover_html
    assert 'id="reset-form"' in recover_html
    assert "/ui/assets/js/modules/auth/recuperar.js" in recover_html

    rjs = (ASSETS / "js" / "modules" / "auth" / "recuperar.js").read_text(encoding="utf-8")
    assert 'api("POST", "/auth/forgot-password"' in rjs
    assert "/auth/reset-password" in rjs

    login = (PAGES / "auth" / "login.html").read_text(encoding="utf-8")
    assert "/ui/pages/auth/recuperar.html" in login

    sec = PAGES / "seguridad" / "seguridad.html"
    assert sec.is_file()
    sec_html = sec.read_text(encoding="utf-8")
    assert 'id="policies-tbody"' in sec_html
    assert 'id="tools-tbody"' in sec_html
    assert 'id="audit-tbody"' in sec_html
    assert 'id="security-tbody"' in sec_html
    assert "<thead>" in sec_html

    sjs = (ASSETS / "js" / "modules" / "seguridad" / "seguridad.js").read_text(
        encoding="utf-8"
    )
    assert 'api("GET", "/policies")' in sjs
    assert 'api("GET", "/tools")' in sjs
    assert 'api("GET", "/audit/events")' in sjs
    assert 'api("GET", "/security/events")' in sjs

    nav = (ASSETS / "js" / "core" / "navigation.js").read_text(encoding="utf-8")
    assert "ensureSeguridadNav" in nav
    assert "ensureCatalogExtras" in nav

    extras = ["mallas", "aulas", "horarios", "asignaciones"]
    for slug in extras:
        path = PAGES / "catalogos" / f"{slug}.html"
        assert path.is_file(), f"missing {path}"
        html = path.read_text(encoding="utf-8")
        assert "data-entity=" in html
        assert 'id="catalog-tbody"' in html
        assert "<thead>" in html

    ejs = (ASSETS / "js" / "modules" / "catalogos" / "entity.js").read_text(
        encoding="utf-8"
    )
    assert 'path: "/curricula"' in ejs
    assert 'path: "/classrooms"' in ejs
    assert 'path: "/schedules"' in ejs
    assert 'path: "/teaching-assignments"' in ejs

    notas = (PAGES / "notas" / "notas.html").read_text(encoding="utf-8")
    assert 'id="btn-create-eval"' in notas
    assert 'id="btn-upsert-kardex"' in notas

    njs = (ASSETS / "js" / "modules" / "notas" / "notas.js").read_text(encoding="utf-8")
    assert 'api("POST", "/evaluations"' in njs
    assert 'api("PUT", "/kardex"' in njs

    reportes = (PAGES / "reportes" / "reportes.html").read_text(encoding="utf-8")
    assert 'value="PDF"' in reportes
    assert 'value="XLSX"' in reportes

    permisos = PAGES / "usuarios" / "permisos.html"
    assert permisos.is_file()
    ph = permisos.read_text(encoding="utf-8")
    assert 'id="perms-page-tbody"' in ph
    assert 'id="perm-create-form"' in ph

    roles_html = (PAGES / "usuarios" / "roles.html").read_text(encoding="utf-8")
    assert 'id="perm-boxes"' in roles_html
    assert 'id="btn-assign-perms"' in roles_html

    asistencia = (PAGES / "asistencia" / "asistencia.html").read_text(encoding="utf-8")
    assert 'id="roster-tbody"' in asistencia
    assert 'id="att-hour"' in asistencia
    assert 'id="btn-create-session"' in asistencia

    notas_html = (PAGES / "notas" / "notas.html").read_text(encoding="utf-8")
    assert 'id="gradebook-tbody"' in notas_html

    ejs_lookup = (ASSETS / "js" / "modules" / "catalogos" / "entity.js").read_text(
        encoding="utf-8"
    )
    assert "LOOKUPS" in ejs_lookup
    assert "hours_theory" in ejs_lookup
    table_js = (ASSETS / "js" / "components" / "table.js").read_text(encoding="utf-8")
    assert "formatRef" in table_js
    assert "makeSearchable" in table_js

    rjs_rep = (ASSETS / "js" / "modules" / "reportes" / "reportes.js").read_text(
        encoding="utf-8"
    )
    assert 'format === "PDF"' in rjs_rep

    roles = (PAGES / "usuarios" / "roles.html").read_text(encoding="utf-8")
    assert 'id="role-create-form"' in roles
    assert 'id="btn-role-deactivate"' in roles

    roles_js = (ASSETS / "js" / "modules" / "usuarios" / "roles.js").read_text(
        encoding="utf-8"
    )
    assert 'api("POST", "/roles"' in roles_js
    assert "DELETE" in roles_js

    users_js = (ASSETS / "js" / "modules" / "usuarios" / "usuarios.js").read_text(
        encoding="utf-8"
    )
    assert "/password" in users_js


@pytest.mark.unit
def test_ui_admin_crud_pattern():
    """Patrón administrativo: toolbar, tabla, modales CRUD y componentes comunes."""
    css = (ASSETS / "css" / "admin.css").read_text(encoding="utf-8")
    assert ".admin-toolbar" in css
    assert ".status-badge" in css
    assert ".siga-modal" in css

    modal = (ASSETS / "js" / "components" / "modal.js").read_text(encoding="utf-8")
    assert "confirmDelete" in modal
    assert "openParked" in modal
    assert "footerCancelSave" in modal

    table = (ASSETS / "js" / "components" / "admin-table.js").read_text(encoding="utf-8")
    assert "SigaAdminTable" in table
    assert "actionButtons" in table

    pages = [
        PAGES / "catalogos" / "carreras.html",
        PAGES / "usuarios" / "usuarios.html",
        PAGES / "usuarios" / "roles.html",
        PAGES / "avisos" / "avisos.html",
        PAGES / "reportes" / "reportes.html",
        PAGES / "notas" / "notas.html",
        PAGES / "asistencia" / "asistencia.html",
        PAGES / "seguridad" / "seguridad.html",
    ]
    for path in pages:
        html = path.read_text(encoding="utf-8")
        assert "admin.css" in html, path.name
        assert "modal.js" in html, path.name
        assert "admin-table.js" in html, path.name
        assert "Acciones" in html, path.name
        assert "module-head" in html, path.name

    carreras = (PAGES / "catalogos" / "carreras.html").read_text(encoding="utf-8")
    assert 'id="btn-new-record"' in carreras
    assert 'id="catalog-create-form"' in carreras

    entity = (ASSETS / "js" / "modules" / "catalogos" / "entity.js").read_text(
        encoding="utf-8"
    )
    assert "SigaModal" in entity
    assert "SigaAdminTable" in entity
    assert "confirmDelete" in entity
