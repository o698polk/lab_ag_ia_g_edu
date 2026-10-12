/* Sistema de Gestión Académica — Frontend SPA ligera */

const AppState = {
  user: null,
  page: "dashboard",
};

function toast(msg, type = "success") {
  const box = document.getElementById("toasts");
  const el = document.createElement("div");
  el.className = `toast-app ${type}`;
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function applyTheme(theme) {
  const t = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem("theme", t);
  return t;
}

/** SPEC-010: override personal vs tema institucional */
function resolveTheme({ userTheme, defaultTheme, respectOverride = true } = {}) {
  const institutional = defaultTheme === "dark" ? "dark" : defaultTheme === "light" ? "light" : null;
  const override = localStorage.getItem("theme_override") === "1";
  if (respectOverride && override) {
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || stored === "light") return stored;
    if (userTheme === "dark" || userTheme === "light") return userTheme;
  }
  if (institutional) return institutional;
  if (userTheme === "dark" || userTheme === "light") return userTheme;
  return "light";
}

function normalizeHexColor(value, fallback = "#0d6efd") {
  if (!value) return fallback;
  let s = String(value).trim();
  if (/^[0-9a-fA-F]{6}$/.test(s)) s = `#${s}`;
  if (/^#[0-9a-fA-F]{3}$/.test(s)) s = `#${s[1]}${s[1]}${s[2]}${s[2]}${s[3]}${s[3]}`;
  if (!/^#[0-9a-fA-F]{6}$/.test(s)) return fallback;
  return s.toLowerCase();
}

/** Aplica colores/nombre institucionales persistidos en BD */
function applyBrandColors(cfg = {}) {
  const root = document.documentElement;
  const primary = normalizeHexColor(cfg.primary_color, "#0d6efd");
  const secondary = normalizeHexColor(cfg.secondary_color, "#198754");
  const accent = normalizeHexColor(cfg.accent_color, "#0dcaf0");
  root.style.setProperty("--primary", primary);
  root.style.setProperty("--secondary", secondary);
  root.style.setProperty("--accent", accent);
  const payload = {
    primary_color: primary,
    secondary_color: secondary,
    accent_color: accent,
    system_name: cfg.system_name || "",
    default_theme: cfg.default_theme === "dark" ? "dark" : "light",
  };
  localStorage.setItem("brand_colors", JSON.stringify(payload));
  if (cfg.system_name) {
    const brand = document.querySelector(".brand-title");
    if (brand) brand.textContent = cfg.system_name;
    document.title = cfg.system_name;
  }
}

async function loadBrandColors() {
  try {
    const cached = localStorage.getItem("brand_colors");
    if (cached) applyBrandColors(JSON.parse(cached));
  } catch {
    /* ignore */
  }
  try {
    const cfg = await API.get("/config/brand");
    applyBrandColors(cfg);
    return cfg;
  } catch {
    return null;
  }
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute("data-theme") || "light";
  const next = cur === "light" ? "dark" : "light";
  localStorage.setItem("theme_override", "1");
  applyTheme(next);
  if (AppState.user) {
    AppState.user.theme = next;
    API.put("/auth/theme", { theme: next }).catch(() => {});
  }
}

function hasPerm(perm) {
  if (!AppState.user) return false;
  if ((AppState.user.roles || []).includes("ADMIN")) return true;
  return (AppState.user.permissions || []).includes(perm);
}

function setImpersonationBanner() {
  const banner = document.getElementById("impersonationBanner");
  if (AppState.user?.impersonator_id) {
    banner.classList.add("visible");
    document.getElementById("impersonationText").textContent =
      `Viendo como ${AppState.user.full_name} (@${AppState.user.username})`;
  } else {
    banner.classList.remove("visible");
  }
}

function navigateKardex(studentId) {
  AppState._kardexId = Number(studentId);
  navigate("kardex");
}

async function returnToAdmin() {
  try {
    const data = await API.post("/auth/return-to-admin", {});
    API.setTokens(data.access_token, data.refresh_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    AppState.user = data.user;
    AppState.user.impersonator_id = null;
    setImpersonationBanner();
    toast("Sesión de administrador restaurada");
    navigate(defaultHomePage());
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loginAs(userId) {
  if (!confirm("¿Entrar como este usuario?")) return;
  try {
    const data = await API.post(`/users/${userId}/login-as`, {});
    API.setTokens(data.access_token, data.refresh_token);
    AppState.user = { ...data.user, impersonator_id: data.impersonator_id };
    localStorage.setItem("user", JSON.stringify(AppState.user));
    setImpersonationBanner();
    toast(`Impersonando a ${data.user.full_name}`);
    navigate(defaultHomePage());
  } catch (e) {
    toast(e.message, "error");
  }
}

function isStudentOrTeacher() {
  const roles = AppState.user?.roles || [];
  return roles.includes("STUDENT") || roles.includes("TEACHER");
}

function navItems() {
  return [
    { id: "dashboard", label: "Dashboard", icon: "bi-speedometer2", perm: "dashboard.view" },
    { id: "users", label: "Usuarios", icon: "bi-people", perm: "users.view" },
    { id: "students", label: "Estudiantes", icon: "bi-mortarboard", perm: "students.view" },
    { id: "teachers", label: "Docentes", icon: "bi-person-badge", perm: "teachers.view" },
    { id: "careers", label: "Carreras", icon: "bi-building", perm: "careers.view" },
    { id: "subjects", label: "Materias", icon: "bi-book", perm: "subjects.view" },
    { id: "terms", label: "Periodos", icon: "bi-calendar3", perm: "terms.view" },
    { id: "courses", label: "Cursos", icon: "bi-journal-bookmark", perm: "courses.view" },
    { id: "enrollments", label: "Matrículas", icon: "bi-clipboard-check", perm: "enrollments.view" },
    { id: "schedules", label: "Horarios", icon: "bi-clock", perm: "schedules.view" },
    { id: "grades", label: "Notas", icon: "bi-pencil-square", perm: "grades.view" },
    { id: "attendance", label: "Asistencia", icon: "bi-calendar-check", perm: "attendance.view" },
    { id: "kardex", label: "Kárdex", icon: "bi-file-earmark-text", perm: "kardex.view" },
    { id: "reports", label: "Reportes", icon: "bi-bar-chart", perm: "reports.view" },
    { id: "notifications", label: "Notificaciones", icon: "bi-bell", perm: "notifications.view" },
    { id: "ai", label: "Asistente IA", icon: "bi-robot", perm: "ai.use" },
    { id: "logia", label: "LogIA", icon: "bi-journal-text", perm: "ai.view_logs" },
    { id: "audit", label: "Auditoría", icon: "bi-shield-lock", perm: "audit.view" },
    { id: "admin", label: "Administración", icon: "bi-gear", perm: "ai.configure" },
  ].filter((i) => {
    // SPEC-009 / SPEC-014: estudiantes y docentes no ven Kárdex ni Dashboard
    if (i.id === "kardex" && isStudentOrTeacher()) return false;
    if (i.id === "dashboard" && isStudentOrTeacher()) return false;
    return hasPerm(i.perm);
  });
}

/** SPEC-014: página inicial según permisos (no forzar dashboard) */
function defaultHomePage() {
  const items = navItems();
  if (items.length) return items[0].id;
  if (hasPerm("courses.view")) return "courses";
  if (hasPerm("grades.view")) return "grades";
  return "notifications";
}

function renderSidebar() {
  const nav = document.getElementById("sidebarNav");
  nav.innerHTML = navItems()
    .map(
      (i) => `
    <button class="nav-link-item ${AppState.page === i.id ? "active" : ""}" onclick="navigate('${i.id}')">
      <i class="bi ${i.icon}"></i><span>${i.label}</span>
    </button>`
    )
    .join("");
}

async function navigate(page) {
  if (page === "dashboard" && (isStudentOrTeacher() || !hasPerm("dashboard.view"))) {
    page = defaultHomePage();
  }
  AppState.page = page;
  CrudStore.page = page;
  renderSidebar();
  const titleEl = document.getElementById("pageTitle");
  const nav = navItems().find((i) => i.id === page);
  if (titleEl) titleEl.textContent = nav?.label || "Panel";
  const content = document.getElementById("content");
  content.innerHTML = `<div class="panel"><p>Cargando…</p></div>`;
  try {
    const html = await pages[page]();
    content.innerHTML = html;
    applyAdvancedFilters();
    if (pagesAfter[page]) await pagesAfter[page]();
  } catch (e) {
    content.innerHTML = `<div class="panel"><p style="color:var(--danger)">${e.message}</p></div>`;
  }
}

function table(headers, rows, searchable = false) {
  const tbodyId = searchable ? ' id="moduleTableBody"' : "";
  return `
  <div class="table-wrap"><table class="data-table">
    <thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody${tbodyId}>${rows || `<tr><td colspan="${headers.length}">Sin datos</td></tr>`}</tbody>
  </table></div>`;
}

const pages = {
  async dashboard() {
    const d = await API.get("/dashboard");
    return `
      <div class="metric-grid">
        ${[
          ["Estudiantes", d.students],
          ["Docentes", d.teachers],
          ["Cursos", d.courses],
          ["Matrículas activas", d.enrollments_active],
          ["Usuarios activos", d.users_active],
          ["Notas pendientes", d.grades_pending],
        ]
          .map(
            ([l, v]) => `<div class="metric-card"><div class="label">${l}</div><div class="value">${v}</div></div>`
          )
          .join("")}
      </div>
      <div class="panel">
        <h2>Accesos rápidos</h2>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap">
          ${navItems()
            .slice(0, 6)
            .map(
              (i) =>
                `<button class="btn-ghost" onclick="navigate('${i.id}')"><i class="bi ${i.icon}"></i> ${i.label}</button>`
            )
            .join("")}
        </div>
      </div>`;
  },

  async users() {
    const [users, roles] = await Promise.all([API.get("/users"), API.get("/roles").catch(() => [])]);
    CrudStore.items = users;
    CrudStore.meta = { roles };
    const rows = users
      .map((u) => {
        const actions = actionButtons({
          edit: hasPerm("users.edit") ? `openUserForm(${u.id})` : null,
          remove: hasPerm("users.delete") && !u.is_protected ? `crudDelete('/users/${u.id}','users','usuario ${esc(u.username)}')` : null,
          extra:
            hasPerm("users.login-as") && !u.is_protected
              ? `<button type="button" class="btn-icon" title="Entrar como" onclick="loginAs(${u.id})"><i class="bi bi-box-arrow-in-right"></i></button>`
              : "",
        });
        const created = (u.created_at || "").slice(0, 10);
        return `<tr data-search="${dataSearch(u.id, u.username, u.full_name, u.email, ...(u.roles || []))}"
          ${dataAttrs({
            date: created,
            status: u.is_active ? "activo" : "inactivo",
            roles: u.roles || [],
          })}>
          <td>${u.id}</td><td>${esc(u.username)}</td><td>${esc(u.full_name)}</td>
          <td>${esc((u.roles || []).join(", "))}</td>
          <td><span class="badge-status ${u.is_active ? "ok" : "bad"}">${u.is_active ? "Activo" : "Inactivo"}</span></td>
          <td>${esc(created || "-")}</td>
          <td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Usuarios", {
        createPerm: "users.create",
        onCreate: "openUserForm()",
        filters: ["dates", "role", "status"],
        exportType: "users",
        statusOptions: ["activo", "inactivo"],
        roleOptions: roles,
      })}
      ${table(["ID", "Usuario", "Nombre", "Roles", "Estado", "Creado", "Acciones"], rows, true)}
    </div>`;
  },

  async students() {
    const [items, careers] = await Promise.all([
      API.get("/students"),
      API.get("/careers").catch(() => []),
    ]);
    CrudStore.items = items;
    CrudStore.meta = { careers };
    const rows = items
      .map((s) => {
        const actions = actionButtons({
          edit: hasPerm("students.edit") ? `openStudentForm(${s.id})` : null,
          remove: hasPerm("students.edit") ? `crudDelete('/students/${s.id}','students','estudiante ${esc(s.student_code)}')` : null,
        });
        return `<tr data-search="${dataSearch(s.student_code, s.full_name, s.career_name, s.phone, s.email, s.status)}"
          ${dataAttrs({ career: s.career_id, status: s.status })}>
          <td>${esc(s.student_code)}</td><td>${esc(s.full_name)}</td><td>${esc(s.career_name || "-")}</td>
          <td>${esc(s.phone || "-")}</td><td>${esc(s.status)}</td><td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Estudiantes", {
        createPerm: "students.create",
        onCreate: "openStudentForm()",
        filters: ["career", "status"],
        exportType: "students",
        statusOptions: ["active", "inactive", "graduated"],
      })}
      ${table(["Código", "Nombre", "Carrera", "Teléfono", "Estado", "Acciones"], rows, true)}
    </div>`;
  },

  async teachers() {
    const items = await API.get("/teachers");
    CrudStore.items = items;
    const rows = items
      .map((t) => {
        const actions = actionButtons({
          edit: hasPerm("teachers.edit") ? `openTeacherForm(${t.id})` : null,
          remove: hasPerm("teachers.edit") ? `crudDelete('/teachers/${t.id}','teachers','docente ${esc(t.teacher_code)}')` : null,
        });
        return `<tr data-search="${dataSearch(t.teacher_code, t.full_name, t.specialty, t.title, t.email, t.status)}"
          ${dataAttrs({ status: t.status || "active" })}>
          <td>${esc(t.teacher_code)}</td><td>${esc(t.full_name)}</td><td>${esc(t.specialty || "-")}</td>
          <td>${esc(t.title || "-")}</td><td>${esc(t.status || "active")}</td><td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Docentes", {
        createPerm: "teachers.create",
        onCreate: "openTeacherForm()",
        filters: ["status"],
        exportType: "teachers",
        statusOptions: ["active", "inactive"],
      })}
      ${table(["Código", "Nombre", "Especialidad", "Título", "Estado", "Acciones"], rows, true)}
    </div>`;
  },

  async careers() {
    const items = await API.get("/careers");
    CrudStore.items = items;
    const rows = items
      .map((c) => {
        const actions = actionButtons({
          edit: hasPerm("careers.edit") ? `openCareerForm(${c.id})` : null,
          remove: hasPerm("careers.edit") ? `crudDelete('/careers/${c.id}','careers','carrera ${esc(c.code)}')` : null,
        });
        return `<tr data-search="${dataSearch(c.code, c.name, c.description)}"
          ${dataAttrs({ status: c.is_active ? "activa" : "inactiva" })}>
          <td>${esc(c.code)}</td><td>${esc(c.name)}</td><td>${c.duration_semesters}</td>
          <td>${c.is_active ? "Sí" : "No"}</td><td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Carreras", {
        createPerm: "careers.create",
        onCreate: "openCareerForm()",
        filters: ["status"],
        exportType: "careers",
        statusOptions: ["activa", "inactiva"],
      })}
      ${table(["Código", "Nombre", "Semestres", "Activa", "Acciones"], rows, true)}
    </div>`;
  },

  async subjects() {
    const [items, careers] = await Promise.all([API.get("/subjects"), API.get("/careers").catch(() => [])]);
    CrudStore.items = items;
    CrudStore.meta = { careers };
    const canEdit = hasPerm("subjects.create") || hasPerm("subjects.edit");
    const rows = items
      .map((s) => {
        const teachers = s.teachers_label || (Array.isArray(s.teachers) ? s.teachers.join(", ") : "") || "Sin docente asignado";
        const actions = actionButtons({
          edit: hasPerm("subjects.edit") ? `openSubjectForm(${s.id})` : null,
          remove: hasPerm("subjects.edit") ? `crudDelete('/subjects/${s.id}','subjects','materia ${esc(s.code)}')` : null,
        });
        return `<tr data-search="${dataSearch(s.code, s.name, s.career_name, s.credits, teachers)}"
          ${dataAttrs({ career: s.career_id, status: s.is_active === false ? "inactiva" : "activa" })}>
          <td>${esc(s.code)}</td><td>${esc(s.name)}</td><td>${s.credits}</td>
          <td>${esc(s.career_name || "-")}</td>
          <td>${esc(teachers)}</td>
          ${canEdit ? `<td>${actions}</td>` : ""}</tr>`;
      })
      .join("");
    const headers = ["Código", "Nombre", "Créditos", "Carrera", "Docente(s)"];
    if (canEdit) headers.push("Acciones");
    return `<div class="panel">
      ${moduleHeader("Materias", {
        createPerm: "subjects.create",
        onCreate: "openSubjectForm()",
        filters: ["career", "status"],
        exportType: "subjects",
        statusOptions: ["activa", "inactiva"],
      })}
      ${(AppState.user?.roles || []).includes("STUDENT")
        ? `<p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">Docentes asignados a sus cursos en periodos habilitados.</p>`
        : ""}
      ${table(headers, rows, true)}
    </div>`;
  },

  async terms() {
    const items = await API.get("/terms");
    CrudStore.items = items;
    const canEdit = hasPerm("terms.edit");
    const rows = items
      .map((t) => {
        const toggle = canEdit
          ? `<label class="term-toggle">
              <input type="checkbox" ${t.is_active ? "checked" : ""} onchange="toggleTermVisible(${t.id}, this.checked)">
              Habilitado
            </label>`
          : t.is_active
            ? '<span class="badge-status ok">Habilitado</span>'
            : '<span class="badge-status warn">Oculto</span>';
        const actions = actionButtons({
          edit: canEdit ? `openTermForm(${t.id})` : null,
          remove: canEdit ? `crudDelete('/terms/${t.id}','terms','periodo ${esc(t.code)}')` : null,
        });
        return `<tr data-search="${dataSearch(t.code, t.name, t.start_date, t.end_date)}"
          ${dataAttrs({ date: t.start_date, status: t.is_active ? "habilitado" : "oculto" })}>
          <td>${esc(t.code)}</td><td>${esc(t.name)}</td><td>${esc(t.start_date)}</td><td>${esc(t.end_date)}</td>
          <td>${toggle}</td><td>${t.grades_closed ? "Cerrado" : "Abierto"}</td><td>${actions}</td></tr>`;
      })
      .join("");
    const note = canEdit
      ? `<p style="color:var(--muted);font-size:.88rem;margin:0 0 1rem">Habilite periodos para que estudiantes/docentes vean materias y notas.</p>`
      : `<p style="color:var(--muted);font-size:.88rem;margin:0 0 1rem">Solo periodos habilitados por administración.</p>`;
    return `<div class="panel">
      ${moduleHeader("Periodos académicos", {
        createPerm: "terms.create",
        onCreate: "openTermForm()",
        filters: ["dates", "status"],
        exportType: "terms",
        statusOptions: ["habilitado", "oculto"],
      })}
      ${note}
      ${table(["Código", "Nombre", "Inicio", "Fin", "Visibilidad", "Notas", "Acciones"], rows, true)}
    </div>`;
  },

  async courses() {
    const [items, subjects, terms, careers] = await Promise.all([
      API.get("/courses"),
      API.get("/subjects").catch(() => []),
      API.get("/terms").catch(() => []),
      API.get("/careers").catch(() => []),
    ]);
    CrudStore.items = items;
    CrudStore.meta = { subjects, terms, careers, courses: items };
    const canEdit = hasPerm("courses.create") || hasPerm("courses.edit");
    const rows = items
      .map((c) => {
        const actions = actionButtons({
          edit: hasPerm("courses.edit") ? `openCourseForm(${c.id})` : null,
          remove: hasPerm("courses.edit") ? `crudDelete('/courses/${c.id}','courses','curso ${esc(c.code)}')` : null,
        });
        return `<tr data-search="${dataSearch(c.code, c.name, c.subject_name, c.term_name, c.parallel)}"
          ${dataAttrs({ term: c.term_id, career: c.career_id, course: c.id, status: c.is_active === false ? "inactivo" : "activo" })}>
          <td>${esc(c.code)}</td><td>${esc(c.name)}</td><td>${esc(c.subject_name || "-")}</td>
          <td>${esc(c.term_name || "-")}</td><td>${esc(c.parallel)}</td>
          ${canEdit ? `<td>${actions}</td>` : ""}</tr>`;
      })
      .join("");
    const headers = ["Código", "Nombre", "Materia", "Periodo", "Paralelo"];
    if (canEdit) headers.push("Acciones");
    return `<div class="panel">
      ${moduleHeader("Cursos / Paralelos", {
        createPerm: "courses.create",
        onCreate: "openCourseForm()",
        filters: ["career", "term", "status"],
        exportType: "courses",
        statusOptions: ["activo", "inactivo"],
      })}
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">
        ${isStudentOrTeacher() ? "Solo se muestran los cursos de su perfil (matrícula o asignación)." : "Gestión de cursos y paralelos."}
      </p>
      ${table(headers, rows, true)}
    </div>`;
  },

  async enrollments() {
    const [items, students, courses, careers, terms] = await Promise.all([
      API.get("/enrollments"),
      hasPerm("enrollments.create") || hasPerm("enrollments.edit") ? API.get("/students") : Promise.resolve([]),
      API.get("/courses").catch(() => []),
      API.get("/careers").catch(() => []),
      API.get("/terms").catch(() => []),
    ]);
    CrudStore.items = items;
    CrudStore.meta = { students, courses, careers, terms };
    const rows = items
      .map((e) => {
        const actions = actionButtons({
          edit: hasPerm("enrollments.edit") ? `openEnrollmentForm(${e.id})` : null,
          remove: hasPerm("enrollments.edit") ? `crudDelete('/enrollments/${e.id}','enrollments','matrícula #${e.id}')` : null,
        });
        const date = (e.enrolled_at || "").slice(0, 10);
        return `<tr data-search="${dataSearch(e.id, e.student_name, e.course_name, e.status)}"
          ${dataAttrs({ date, career: e.career_id, term: e.term_id, course: e.course_id, status: e.status })}>
          <td>${e.id}</td><td>${esc(e.student_name)}</td><td>${esc(e.course_name)}</td>
          <td>${esc(e.status)}</td><td>${esc(date)}</td><td>${actions}</td></tr>`;
      })
      .join("");
    const canManage = hasPerm("enrollments.create") || hasPerm("enrollments.edit");
    const headers = canManage
      ? ["ID", "Estudiante", "Curso", "Estado", "Fecha", "Acciones"]
      : ["ID", "Curso", "Estado", "Fecha"];
    const studentRows = (AppState.user?.roles || []).includes("STUDENT")
      ? items
          .map((e) => {
            const date = (e.enrolled_at || "").slice(0, 10);
            return `<tr data-search="${dataSearch(e.course_name, e.status)}"
              ${dataAttrs({ date, career: e.career_id, term: e.term_id, course: e.course_id, status: e.status })}>
              <td>${e.id}</td><td>${esc(e.course_name)}</td>
              <td>${esc(e.status)}</td><td>${esc(date)}</td></tr>`;
          })
          .join("")
      : rows;
    return `<div class="panel">
      ${moduleHeader("Matrículas", {
        createPerm: "enrollments.create",
        onCreate: "openEnrollmentForm()",
        filters: ["dates", "career", "term", "course", "status"],
        exportType: "enrollments",
        statusOptions: ["activa", "retirada", "congelada"],
      })}
      ${(AppState.user?.roles || []).includes("STUDENT")
        ? `<p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">Sus matrículas en periodos habilitados.</p>`
        : ""}
      ${table(headers, (AppState.user?.roles || []).includes("STUDENT") ? studentRows : rows, true)}
    </div>`;
  },

  async schedules() {
    const [items, courses, terms] = await Promise.all([
      API.get("/schedules"),
      API.get("/courses").catch(() => []),
      API.get("/terms").catch(() => []),
    ]);
    CrudStore.items = items;
    CrudStore.meta = { courses, terms };
    const canEdit = hasPerm("schedules.create") || hasPerm("schedules.edit");
    const rows = items
      .map((s) => {
        const actions = actionButtons({
          edit: hasPerm("schedules.edit") ? `openScheduleForm(${s.id})` : null,
          remove: hasPerm("schedules.edit") ? `crudDelete('/schedules/${s.id}','schedules','horario')` : null,
        });
        return `<tr data-search="${dataSearch(s.course_code, s.course_name, s.subject_name, s.term_name, s.day_name, s.classroom)}"
          ${dataAttrs({ term: s.term_id, course: s.course_id })}>
          <td>${esc(s.course_code || "-")}</td>
          <td>${esc(s.subject_name || s.course_name || "-")}</td>
          <td>${esc(s.term_name || "-")}</td>
          <td>${esc(s.parallel || "-")}</td>
          <td>${esc(s.day_name)}</td>
          <td>${esc(s.start_time)} - ${esc(s.end_time)}</td>
          <td>${esc(s.classroom || "-")}</td>
          ${canEdit ? `<td>${actions}</td>` : ""}</tr>`;
      })
      .join("");
    const headers = ["Código", "Materia", "Periodo", "Paralelo", "Día", "Horario", "Aula"];
    if (canEdit) headers.push("Acciones");
    return `<div class="panel">
      ${moduleHeader("Horarios", {
        createPerm: "schedules.create",
        onCreate: "openScheduleForm()",
        filters: ["term", "course"],
        exportType: "schedules",
      })}
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">
        ${isStudentOrTeacher() ? "Solo se muestran los horarios de sus cursos." : "Horarios por curso / materia."}
      </p>
      ${table(headers, rows, true)}
    </div>`;
  },

  async grades() {
    const [grades, courses, students, careers, terms] = await Promise.all([
      API.get("/grades"),
      API.get("/courses").catch(() => []),
      hasPerm("grades.manage") ? API.get("/students") : Promise.resolve([]),
      API.get("/careers").catch(() => []),
      API.get("/terms").catch(() => []),
    ]);
    CrudStore.items = grades;
    CrudStore.meta = { courses, students, careers, terms };
    const rows = grades
      .map((g) => {
        const badge = g.status === "aprobado" ? "ok" : g.status === "reprobado" ? "bad" : "warn";
        const actions = actionButtons({
          edit: hasPerm("grades.manage") ? `openGradeForm(${g.id})` : null,
          remove: hasPerm("grades.manage") ? `crudDelete('/grades/${g.id}','grades','nota')` : null,
        });
        return `<tr data-search="${dataSearch(g.student_name, g.course_name, g.term_name, g.status, g.final_grade)}"
          ${dataAttrs({ career: g.career_id, term: g.term_id, course: g.course_id, status: g.status })}>
          <td>${esc(g.student_name)}</td><td>${esc(g.course_name)}</td>
          <td>${g.partial1 ?? "-"}</td><td>${g.partial2 ?? "-"}</td>
          <td>${g.average ?? "-"}</td>
          <td>${g.needs_supplementary ? (g.supplementary ?? "Requerido") : "-"}</td>
          <td>${g.final_grade ?? "-"}</td>
          <td><span class="badge-status ${badge}">${esc(g.status)}</span></td>
          <td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Calificaciones", {
        createPerm: "grades.manage",
        createLabel: "Registrar nota",
        onCreate: "openGradeForm()",
        filters: ["career", "term", "course", "status"],
        exportType: "grades",
        statusOptions: ["en_curso", "aprobado", "reprobado"],
      })}
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">Promedio = (P1+P2)/2. Si &lt; 7 habilita Supletorio.</p>
      ${table(["Estudiante", "Curso", "P1", "P2", "Prom.", "Sup.", "Final", "Estado", "Acciones"], rows, true)}
    </div>`;
  },

  async attendance() {
    const [items, courses, students, careers, terms] = await Promise.all([
      API.get("/attendance"),
      API.get("/courses").catch(() => []),
      hasPerm("attendance.manage") ? API.get("/students") : Promise.resolve([]),
      API.get("/careers").catch(() => []),
      API.get("/terms").catch(() => []),
    ]);
    CrudStore.items = items;
    CrudStore.meta = { courses, students, careers, terms };
    const rows = items
      .map((a) => {
        const actions = actionButtons({
          edit: hasPerm("attendance.manage") ? `openAttendanceForm(${a.id})` : null,
          remove: hasPerm("attendance.manage") ? `crudDelete('/attendance/${a.id}','attendance','asistencia')` : null,
        });
        return `<tr data-search="${dataSearch(a.student_name, a.course_name, a.session_date, a.status, a.notes)}"
          ${dataAttrs({ date: a.session_date, career: a.career_id, term: a.term_id, course: a.course_id, status: a.status })}>
          <td>${esc(a.student_name)}</td><td>${esc(a.course_name || "-")}</td><td>${esc(a.session_date)}</td>
          <td>${esc(a.status)}</td><td>${esc(a.notes || "-")}</td><td>${actions}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Asistencia", {
        createPerm: "attendance.manage",
        createLabel: "Registrar",
        onCreate: "openAttendanceForm()",
        filters: ["dates", "career", "term", "course", "status"],
        exportType: "attendance",
        statusOptions: ["presente", "ausente", "tardanza", "justificada"],
      })}
      ${table(["Estudiante", "Curso", "Fecha", "Estado", "Notas", "Acciones"], rows, true)}
    </div>`;
  },

  async kardex() {
    const students = await API.get("/students");
    CrudStore.meta = { students };
    let sid = AppState._kardexId || students[0]?.id;
    if (AppState.user.roles?.includes("STUDENT")) {
      const mine = students.find((s) => s.user_id === AppState.user.id);
      if (mine) sid = mine.id;
    }
    if (!sid) return `<div class="panel"><p>No hay estudiantes.</p></div>`;
    AppState._kardexId = sid;
    const data = await API.get(`/kardex/${sid}`);
    const rows = data.grades
      .map(
        (g) =>
          `<tr data-search="${dataSearch(g.course_name, g.status, g.final_grade)}">
            <td>${esc(g.course_name)}</td><td>${g.partial1 ?? "-"}</td><td>${g.partial2 ?? "-"}</td>
            <td>${g.supplementary ?? "-"}</td><td>${g.final_grade ?? "-"}</td><td>${esc(g.status)}</td></tr>`
      )
      .join("");
    const picker =
      !AppState.user.roles?.includes("STUDENT")
        ? `<label style="display:flex;gap:.5rem;align-items:center;font-size:.9rem;color:var(--muted)">Estudiante
            <select onchange="navigateKardex(this.value)">${optionsHtml(students, "id", (s) => `${s.student_code} — ${s.full_name}`, sid)}</select>
          </label>`
        : "";
    return `<div class="panel">
      <div class="module-header">
        <h2>Kárdex — ${esc(data.student.full_name)}</h2>
        <div class="module-actions">
          <div class="search-box"><i class="bi bi-search"></i>
            <input type="search" id="moduleSearch" placeholder="Buscar materia…" oninput="filterModuleRows(this.value)">
          </div>
          ${picker}
          ${
            hasPerm("kardex.export")
              ? `<button type="button" class="btn-primary-app" onclick="downloadAuth(event, '/api/v1/kardex/${sid}/pdf')">Exportar PDF</button>`
              : ""
          }
        </div>
      </div>
      ${table(["Materia", "P1", "P2", "Sup.", "Final", "Estado"], rows, true)}
    </div>`;
  },

  async reports() {
    const [s, careers, terms, courses, catalog] = await Promise.all([
      API.get("/reports/summary"),
      API.get("/careers").catch(() => []),
      API.get("/terms").catch(() => []),
      API.get("/courses").catch(() => []),
      API.get("/reports/catalog").catch(() => []),
    ]);
    CrudStore.meta = { careers, terms, courses };
    const reportCards =
      catalog.length
        ? catalog.map((r) => [r.title, r.type])
        : [
            ["Notas", "grades"],
            ["Asistencia", "attendance"],
            ["Matrículas", "enrollments"],
            ["Estudiantes", "students"],
            ["Usuarios", "users"],
            ["Docentes", "teachers"],
          ];
    return `<div class="panel">
      <h2>Reportes institucionales</h2>
      <div class="metric-grid" style="margin-top:1rem">
        ${Object.entries(s)
          .map(
            ([k, v]) =>
              `<div class="metric-card"><div class="label">${k}</div><div class="value">${v}</div></div>`
          )
          .join("")}
      </div>
      <h3 style="margin:1.25rem 0 .5rem;font-size:1rem">Filtros de exportación</h3>
      <div class="filter-bar" id="reportFilters">
        <label class="filter-field">Buscar<input type="search" id="moduleSearch" placeholder="Texto…"></label>
        <label class="filter-field">Desde<input type="date" id="filterFrom"></label>
        <label class="filter-field">Hasta<input type="date" id="filterTo"></label>
        <label class="filter-field">Carrera<select id="filterCareer"><option value="">Todas</option>${optionsHtml(careers, "id", (c) => c.name)}</select></label>
        <label class="filter-field">Periodo<select id="filterTerm"><option value="">Todos</option>${optionsHtml(terms, "id", (t) => t.name)}</select></label>
        <label class="filter-field">Curso<select id="filterCourse"><option value="">Todos</option>${optionsHtml(courses, "id", (c) => c.name)}</select></label>
        <label class="filter-field">Estado<input id="filterStatus" placeholder="aprobado, activa…"></label>
        <label class="filter-field">Rol<input id="filterRole" placeholder="ADMIN, TEACHER…"></label>
      </div>
      <div class="report-grid">
        ${reportCards
          .map(
            ([label, type]) => `
          <div class="report-card">
            <strong>${esc(label)}</strong>
            <div class="row-actions" style="margin-top:.6rem">
              <button type="button" class="btn-primary-app" onclick="exportReport('${type}','xlsx')"><i class="bi bi-file-earmark-excel"></i> Excel</button>
              <button type="button" class="btn-ghost" onclick="exportReport('${type}','pdf')"><i class="bi bi-file-earmark-pdf"></i> PDF</button>
            </div>
          </div>`
          )
          .join("")}
      </div>
      <p style="color:var(--muted);font-size:.85rem;margin-top:1rem">
        Los filtros se aplican a la descarga. Según su rol, solo verá datos permitidos (periodos habilitados, cursos asignados, etc.).
      </p>
    </div>`;
  },

  async notifications() {
    const items = await API.get("/notifications");
    CrudStore.items = items;
    const rows = items
      .map((n) => {
        const date = (n.created_at || "").slice(0, 10);
        return `<tr data-search="${dataSearch(n.title, n.message, n.role_code)}"
          ${dataAttrs({ date, status: n.is_read ? "leida" : "no_leida", role: n.role_code || "" })}>
            <td>${esc(n.title)}</td><td>${esc(n.message)}</td>
            <td>${n.is_read ? "Sí" : "No"}</td><td>${esc((n.created_at || "").slice(0, 19))}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Notificaciones", {
        createPerm: "notifications.send",
        createLabel: "Enviar aviso",
        onCreate: "openNotificationForm()",
        filters: ["dates", "status"],
        exportType: "notifications",
        statusOptions: ["leida", "no_leida"],
      })}
      ${table(["Título", "Mensaje", "Leída", "Fecha"], rows, true)}
    </div>`;
  },

  async ai() {
    // SPEC-018/020/031: no renderizar mensajes aquí — DOM tras insertar HTML; historial reutilizable
    return `<div class="panel"><h2>Asistente IA</h2>
      <div id="aiInsecureBanner" class="ai-insecure-banner hidden" role="alert"></div>
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">Historial compartido con el chat flotante. Al crear una <strong>nueva</strong> conversación, la anterior se guarda en el panel Historial (no se borra).</p>
      <div class="ai-layout">
        <aside class="ai-history-panel">
          <div class="ai-history-head">
            <strong>Historial</strong>
            <button type="button" class="btn-ghost" onclick="AIChatStore.newConversation()" title="Nueva conversación"><i class="bi bi-plus-lg"></i> Nueva</button>
          </div>
          <div class="ai-history-list" id="aiHistoryList"><p class="ai-history-empty">Cargando…</p></div>
        </aside>
        <div class="ai-chat">
          <div class="ai-messages" id="aiMessages"><div class="ai-bubble bot">Cargando historial…</div></div>
          <form class="ai-input-row" onsubmit="return sendAI(event)">
            <input id="aiInput" placeholder="Pregunte sobre el sistema…" style="flex:1" required>
            <button class="btn-primary-app" type="submit">Enviar</button>
          </form>
        </div>
      </div>
    </div>`;
  },

  async logia() {
    // SPEC-026: filtros vía query al API (no solo client-side)
    const f = CrudStore.filters || {};
    const params = buildLogIAQuery(f);
    const items = await API.get(`/ai/agent-logs?${params}`);
    CrudStore.items = items;
    const eventTypes = [
      "chat",
      "tool_call",
      "tool_error",
      "report",
      "policy_block",
      "prompt_injection",
      "privilege_block",
      "confirm",
    ];
    const severities = ["info", "warn", "block", "error"];
    const rows = items
      .map((e) => {
        const date = (e.created_at || "").slice(0, 10);
        const isBlock =
          e.severity === "block" ||
          ["prompt_injection", "policy_block", "privilege_block"].includes(e.event_type);
        const rowClass = isBlock ? " class=\"row-security-block\"" : "";
        const question = e.user_question || "";
        return `<tr${rowClass} data-search="${dataSearch(e.summary, e.keywords, e.username, e.event_type, e.conversation_id, e.role_codes, question)}"
          ${dataAttrs({ date, status: e.event_type, role: e.role_codes || "" })}>
          <td>${esc((e.created_at || "").slice(0, 19))}</td>
          <td>${esc(e.username || "-")}</td>
          <td>${esc(e.role_codes || "-")}</td>
          <td><span class="badge-status ${isBlock || e.severity === "error" ? "bad" : e.severity === "warn" ? "warn" : "ok"}">${esc(e.event_type)}</span></td>
          <td>${isBlock ? `<span class="security-block-label">BLOQUEADO</span>` : esc(e.severity)}</td>
          <td style="font-size:.75rem;max-width:140px;overflow:hidden;text-overflow:ellipsis" title="${esc(question)}">${esc(question || "-")}</td>
          <td style="font-size:.75rem;max-width:120px;overflow:hidden;text-overflow:ellipsis">${esc(e.conversation_id || "-")}</td>
          <td>${esc(e.summary || "")}</td>
        </tr>`;
      })
      .join("");
    return `<div class="panel">
      <div class="module-header">
        <h2>LogIA</h2>
        <div class="module-actions">
          <button type="button" class="btn-ghost" onclick="exportLogIA('xlsx')"><i class="bi bi-file-earmark-excel"></i> Excel</button>
          <button type="button" class="btn-ghost" onclick="exportLogIA('pdf')"><i class="bi bi-file-earmark-pdf"></i> PDF</button>
          <button type="button" class="btn-ghost" onclick="exportLogIA('json')"><i class="bi bi-filetype-json"></i> JSON</button>
          <button type="button" class="btn-primary-app" onclick="applyLogIAFilters()">Aplicar filtros</button>
        </div>
      </div>
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">Registro de chats, tools, reportes y <strong style="color:var(--danger)">bloqueos de seguridad</strong> (prompt injection, jailbreak, mínimo privilegio). Las filas bloqueadas aparecen en rojo.</p>
      <div class="filter-bar">
        <label class="filter-field">Buscar<input type="search" id="moduleSearch" placeholder="Palabra clave…" value="${esc(f.q || "")}"></label>
        <label class="filter-field">Desde<input type="date" id="filterFrom" value="${esc(f.from || "")}"></label>
        <label class="filter-field">Hasta<input type="date" id="filterTo" value="${esc(f.to || "")}"></label>
        <label class="filter-field">Usuario<input id="filterUsername" placeholder="username" value="${esc(f.username || "")}"></label>
        <label class="filter-field">Conversación<input id="filterConversation" placeholder="UUID" value="${esc(f.conversation || "")}"></label>
        <label class="filter-field">Evento
          <select id="filterStatus">
            <option value="">Todos</option>
            ${eventTypes.map((t) => `<option value="${t}" ${f.status === t ? "selected" : ""}>${t}</option>`).join("")}
          </select>
        </label>
        <label class="filter-field">Severidad
          <select id="filterSeverity">
            <option value="">Todas</option>
            ${severities.map((t) => `<option value="${t}" ${f.severity === t ? "selected" : ""}>${t}</option>`).join("")}
          </select>
        </label>
        <label class="filter-field">Rol<input id="filterRole" placeholder="ADMIN, TEACHER…" value="${esc(f.role || "")}"></label>
      </div>
      <p class="module-count" id="moduleCount">${items.length} registro(s)</p>
      ${table(["Fecha", "Usuario", "Roles", "Evento", "Severidad", "Pregunta", "Conversación", "Resumen"], rows, true)}
    </div>`;
  },

  async audit() {
    const items = await API.get("/audit");
    CrudStore.items = items;
    const modules = [...new Set(items.map((a) => a.module).filter(Boolean))].sort();
    const blockActions = new Set([
      "AI_PROMPT_INJECTION_BLOCK",
      "AI_POLICY_BLOCK",
      "AI_PRIVILEGE_BLOCK",
      "AI_UNKNOWN_TOOL_BLOCK",
    ]);
    const rows = items
      .map((a) => {
        const date = (a.created_at || "").slice(0, 10);
        const isBlock =
          a.module === "ai_security" ||
          blockActions.has(a.action) ||
          /BLOCK|INJECTION|JAILBREAK|PRIVILEGE/i.test(a.action || "");
        const rowClass = isBlock ? " class=\"row-security-block\"" : "";
        const actionCell = isBlock
          ? `<span class="badge-status bad">${esc(a.action)}</span> <span class="security-block-label">BLOQUEADO</span>`
          : esc(a.action);
        const moduleCell = isBlock
          ? `<span class="badge-status bad">${esc(a.module)}</span>`
          : esc(a.module);
        return `<tr${rowClass} data-search="${dataSearch(a.action, a.module, a.details, a.user_id, a.ip_address)}"
          ${dataAttrs({ date, status: a.module })}>
            <td>${esc((a.created_at || "").slice(0, 19))}</td><td>${a.user_id ?? "-"}</td>
            <td>${moduleCell}</td><td>${actionCell}</td>
            <td>${esc(a.details || "")}</td><td>${esc(a.ip_address || "")}</td></tr>`;
      })
      .join("");
    return `<div class="panel">
      ${moduleHeader("Auditoría", {
        filters: ["dates", "status"],
        exportType: "audit",
        statusOptions: modules,
      })}
      <p style="color:var(--muted);font-size:.85rem;margin:0 0 .75rem">El filtro Estado selecciona el módulo del evento. Los bloqueos del agente (<code>ai_security</code>: injection, jailbreak, mínimo privilegio) se muestran en <strong style="color:var(--danger)">rojo</strong>.</p>
      ${table(["Fecha", "Usuario", "Módulo", "Acción", "Detalle", "IP"], rows, true)}
    </div>`;
  },

  async admin() {
    const [cfg, ai] = await Promise.all([API.get("/config"), API.get("/ai/config")]);
    const primary = normalizeHexColor(cfg.primary_color, "#0d6efd");
    const secondary = normalizeHexColor(cfg.secondary_color, "#198754");
    const accent = normalizeHexColor(cfg.accent_color, "#0dcaf0");
    applyBrandColors({ ...cfg, primary_color: primary, secondary_color: secondary, accent_color: accent });
    return `<div class="panel"><h2>Configuración del sistema</h2>
      <p style="color:var(--muted);font-size:.88rem;margin:0 0 1rem">Los colores se guardan en la base de datos y se aplican a todo el sistema.</p>
      <form id="configForm" class="form-grid" onsubmit="return saveConfig(event)">
        <label>Nombre del sistema<input name="system_name" value="${esc(cfg.system_name || "")}" required></label>
        <label>Color primario<input name="primary_color" type="color" value="${primary}"></label>
        <label>Color secundario<input name="secondary_color" type="color" value="${secondary}"></label>
        <label>Color acento<input name="accent_color" type="color" value="${accent}"></label>
        <label>Tema por defecto<select name="default_theme">
          <option value="light" ${cfg.default_theme !== "dark" ? "selected" : ""}>Claro</option>
          <option value="dark" ${cfg.default_theme === "dark" ? "selected" : ""}>Oscuro</option>
        </select></label>
        <div style="grid-column:1/-1;display:flex;gap:.5rem;flex-wrap:wrap;align-items:center">
          <button type="submit" class="btn-primary-app">Guardar colores</button>
          <span id="configSaveHint" style="color:var(--muted);font-size:.85rem"></span>
        </div>
      </form></div>
      <div class="panel"><h2>Configuración DeepSeek</h2>
      <form class="form-grid" onsubmit="return saveAI(event)">
        <label>API Key<input name="api_key" type="password" placeholder="${ai.has_api_key ? "••••••••" : "sk-..."}"></label>
        <label>Modelo<input name="model" value="${esc(ai.model || "deepseek-chat")}"></label>
        <label>Temperatura<input name="temperature" type="number" step="0.1" min="0" max="2" value="${ai.temperature ?? 0.3}"></label>
        <label>Habilitado<select name="is_enabled">
          <option value="true" ${ai.is_enabled ? "selected" : ""}>Sí</option>
          <option value="false" ${!ai.is_enabled ? "selected" : ""}>No</option>
        </select></label>
        <label style="grid-column:1/-1">System prompt<textarea name="system_prompt" rows="3">${esc(ai.system_prompt || "")}</textarea></label>
        <div style="grid-column:1/-1"><button class="btn-primary-app">Guardar IA</button></div>
      </form></div>`;
  },
};

const pagesAfter = {
  admin() {
    const root = document.documentElement;
    const bind = (name, cssVar) => {
      const el = document.querySelector(`[name="${name}"]`);
      if (!el) return;
      el.addEventListener("input", () => {
        root.style.setProperty(cssVar, el.value);
      });
    };
    bind("primary_color", "--primary");
    bind("secondary_color", "--secondary");
    bind("accent_color", "--accent");
  },
  async ai() {
    // SPEC-018/020/031: hidratar chat + lista historial DESPUÉS de montar DOM
    if (!hasPerm("ai.use")) return;
    try {
      await AIChatStore.loadSecurityMode();
      await AIChatStore.loadActive();
      AIChatStore.renderAll();
      await AIChatStore.loadHistory();
    } catch (err) {
      const box = document.getElementById("aiMessages");
      if (box) box.innerHTML = `<div class="ai-bubble bot">No se pudo cargar el historial: ${esc(err.message)}</div>`;
    }
  },
};

function findItem(id) {
  return (CrudStore.items || []).find((i) => String(i.id) === String(id));
}

function openUserForm(id) {
  const u = id ? findItem(id) : null;
  const roles = CrudStore.meta.roles || [];
  const selected = new Set(u?.roles || []);
  const roleOptions = (roles || [])
    .map((r) => {
      const code = r.code || r;
      const label = r.name ? `${code} — ${r.name}` : code;
      const sel = selected.has(code) ? "selected" : "";
      return `<option value="${esc(code)}" ${sel}>${esc(label)}</option>`;
    })
    .join("");
  openModal(u ? "Editar usuario" : "Crear usuario", `
    ${u ? "" : `<label>Usuario<input name="username" required value=""></label>
    <label>Contraseña<input name="password" type="password" ${u ? "" : "required"}></label>`}
    <label>Email<input name="email" type="email" required value="${esc(u?.email || "")}"></label>
    <label>Nombre<input name="first_name" required value="${esc(u?.first_name || "")}"></label>
    <label>Apellido<input name="last_name" required value="${esc(u?.last_name || "")}"></label>
    <label>Roles
      <select name="roles" multiple size="${Math.min(8, Math.max(3, (roles || []).length || 3))}" required>
        ${roleOptions}
      </select>
      <small class="field-hint">Mantenga Ctrl (Windows) o Cmd (Mac) para elegir varios.</small>
    </label>
    ${u ? `<label>Nueva contraseña (opcional)<input name="password" type="password"></label>
    <label>Activo<select name="is_active"><option value="true" ${u.is_active ? "selected" : ""}>Sí</option><option value="false" ${!u.is_active ? "selected" : ""}>No</option></select></label>` : ""}
    <input type="hidden" name="id" value="${u?.id || ""}">
  `, "submitUserForm");
}

async function submitUserForm(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  const id = body.id;
  delete body.id;
  body.roles = fd.getAll("roles").filter(Boolean);
  if (body.is_active != null) body.is_active = body.is_active === "true" || body.is_active === true;
  if (!body.password) delete body.password;
  if (id) return crudSave({ method: "PUT", path: `/users/${id}`, body, success: "Usuario actualizado", page: "users" });
  return crudSave({ method: "POST", path: "/users", body, success: "Usuario creado", page: "users" });
}

function openStudentForm(id) {
  const s = id ? findItem(id) : null;
  const careers = CrudStore.meta.careers || [];
  openModal(s ? "Editar estudiante" : "Crear estudiante", `
    <label>Código<input name="student_code" required value="${esc(s?.student_code || "")}"></label>
    ${s ? "" : `<label>Usuario<input name="username" required></label>
    <label>Contraseña<input name="password" type="password" placeholder="Estudiante123!"></label>`}
    <label>Email<input name="email" type="email" ${s ? "" : "required"} value="${esc(s?.email || "")}"></label>
    <label>Nombre<input name="first_name" ${s ? "" : "required"} value="${esc(s?.first_name || "")}"></label>
    <label>Apellido<input name="last_name" ${s ? "" : "required"} value="${esc(s?.last_name || "")}"></label>
    <label>Teléfono<input name="phone" value="${esc(s?.phone || "")}"></label>
    <label>Carrera<select name="career_id"><option value="">—</option>${optionsHtml(careers, "id", (c) => c.name, s?.career_id)}</select></label>
    <label>Estado<input name="status" value="${esc(s?.status || "active")}"></label>
    <input type="hidden" name="id" value="${s?.id || ""}">
  `, "submitStudentForm");
}

async function submitStudentForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  if (body.career_id) body.career_id = Number(body.career_id);
  else delete body.career_id;
  if (id) return crudSave({ method: "PUT", path: `/students/${id}`, body, success: "Estudiante actualizado", page: "students" });
  return crudSave({ method: "POST", path: "/students", body, success: "Estudiante creado", page: "students" });
}

function openTeacherForm(id) {
  const t = id ? findItem(id) : null;
  openModal(t ? "Editar docente" : "Crear docente", `
    <label>Código<input name="teacher_code" required value="${esc(t?.teacher_code || "")}"></label>
    ${t ? "" : `<label>Usuario<input name="username" required></label>
    <label>Contraseña<input name="password" type="password" placeholder="Docente123!"></label>`}
    <label>Email<input name="email" type="email" ${t ? "" : "required"} value="${esc(t?.email || "")}"></label>
    <label>Nombre<input name="first_name" ${t ? "" : "required"} value="${esc(t?.first_name || "")}"></label>
    <label>Apellido<input name="last_name" ${t ? "" : "required"} value="${esc(t?.last_name || "")}"></label>
    <label>Especialidad<input name="specialty" value="${esc(t?.specialty || "")}"></label>
    <label>Título<input name="title" value="${esc(t?.title || "")}"></label>
    <label>Teléfono<input name="phone" value="${esc(t?.phone || "")}"></label>
    <input type="hidden" name="id" value="${t?.id || ""}">
  `, "submitTeacherForm");
}

async function submitTeacherForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  if (id) return crudSave({ method: "PUT", path: `/teachers/${id}`, body, success: "Docente actualizado", page: "teachers" });
  return crudSave({ method: "POST", path: "/teachers", body, success: "Docente creado", page: "teachers" });
}

function openCareerForm(id) {
  const c = id ? findItem(id) : null;
  openModal(c ? "Editar carrera" : "Crear carrera", `
    <label>Código<input name="code" required value="${esc(c?.code || "")}"></label>
    <label>Nombre<input name="name" required value="${esc(c?.name || "")}"></label>
    <label>Semestres<input name="duration_semesters" type="number" value="${c?.duration_semesters ?? 8}"></label>
    <label>Descripción<textarea name="description" rows="2">${esc(c?.description || "")}</textarea></label>
    <label>Activa<select name="is_active"><option value="true" ${c?.is_active !== false ? "selected" : ""}>Sí</option><option value="false" ${c?.is_active === false ? "selected" : ""}>No</option></select></label>
    <input type="hidden" name="id" value="${c?.id || ""}">
  `, "submitCareerForm");
}

async function submitCareerForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  body.duration_semesters = Number(body.duration_semesters || 8);
  body.is_active = body.is_active === "true";
  if (id) return crudSave({ method: "PUT", path: `/careers/${id}`, body, success: "Carrera actualizada", page: "careers" });
  return crudSave({ method: "POST", path: "/careers", body, success: "Carrera creada", page: "careers" });
}

function openSubjectForm(id) {
  const s = id ? findItem(id) : null;
  const careers = CrudStore.meta.careers || [];
  openModal(s ? "Editar materia" : "Crear materia", `
    <label>Código<input name="code" required value="${esc(s?.code || "")}"></label>
    <label>Nombre<input name="name" required value="${esc(s?.name || "")}"></label>
    <label>Créditos<input name="credits" type="number" value="${s?.credits ?? 3}"></label>
    <label>Carrera<select name="career_id"><option value="">—</option>${optionsHtml(careers, "id", (c) => c.name, s?.career_id)}</select></label>
    <input type="hidden" name="id" value="${s?.id || ""}">
  `, "submitSubjectForm");
}

async function submitSubjectForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  body.credits = Number(body.credits || 3);
  if (body.career_id) body.career_id = Number(body.career_id);
  else delete body.career_id;
  if (id) return crudSave({ method: "PUT", path: `/subjects/${id}`, body, success: "Materia actualizada", page: "subjects" });
  return crudSave({ method: "POST", path: "/subjects", body, success: "Materia creada", page: "subjects" });
}

function openTermForm(id) {
  const t = id ? findItem(id) : null;
  openModal(t ? "Editar periodo" : "Crear periodo", `
    <label>Código<input name="code" required value="${esc(t?.code || "")}"></label>
    <label>Nombre<input name="name" required value="${esc(t?.name || "")}"></label>
    <label>Inicio<input name="start_date" type="date" required value="${esc(t?.start_date || "")}"></label>
    <label>Fin<input name="end_date" type="date" required value="${esc(t?.end_date || "")}"></label>
    <label>Habilitado<select name="is_active"><option value="true" ${t?.is_active ? "selected" : ""}>Sí</option><option value="false" ${!t?.is_active ? "selected" : ""}>No</option></select></label>
    <label>Notas cerradas<select name="grades_closed"><option value="false" ${!t?.grades_closed ? "selected" : ""}>No</option><option value="true" ${t?.grades_closed ? "selected" : ""}>Sí</option></select></label>
    <input type="hidden" name="id" value="${t?.id || ""}">
  `, "submitTermForm");
}

async function submitTermForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  body.is_active = body.is_active === "true";
  body.grades_closed = body.grades_closed === "true";
  if (id) return crudSave({ method: "PUT", path: `/terms/${id}`, body, success: "Periodo actualizado", page: "terms" });
  return crudSave({ method: "POST", path: "/terms", body, success: "Periodo creado", page: "terms" });
}

async function toggleTermVisible(termId, isActive) {
  try {
    await API.put(`/terms/${termId}`, { is_active: isActive });
    toast(isActive ? "Periodo habilitado" : "Periodo ocultado");
  } catch (err) {
    toast(err.message, "error");
    navigate("terms");
  }
}

function openCourseForm(id) {
  const c = id ? findItem(id) : null;
  const { subjects = [], terms = [], careers = [] } = CrudStore.meta;
  openModal(c ? "Editar curso" : "Crear curso", `
    <label>Código<input name="code" required value="${esc(c?.code || "")}"></label>
    <label>Nombre<input name="name" required value="${esc(c?.name || "")}"></label>
    <label>Materia<select name="subject_id" required>${optionsHtml(subjects, "id", (s) => `${s.code} — ${s.name}`, c?.subject_id)}</select></label>
    <label>Periodo<select name="term_id" required>${optionsHtml(terms, "id", (t) => t.name, c?.term_id)}</select></label>
    <label>Carrera<select name="career_id"><option value="">—</option>${optionsHtml(careers, "id", (x) => x.name, c?.career_id)}</select></label>
    <label>Paralelo<input name="parallel" value="${esc(c?.parallel || "A")}"></label>
    <label>Cupo<input name="capacity" type="number" value="${c?.capacity ?? 40}"></label>
    <input type="hidden" name="id" value="${c?.id || ""}">
  `, "submitCourseForm");
}

async function submitCourseForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  body.subject_id = Number(body.subject_id);
  body.term_id = Number(body.term_id);
  body.capacity = Number(body.capacity || 40);
  if (body.career_id) body.career_id = Number(body.career_id);
  else delete body.career_id;
  if (id) return crudSave({ method: "PUT", path: `/courses/${id}`, body, success: "Curso actualizado", page: "courses" });
  return crudSave({ method: "POST", path: "/courses", body, success: "Curso creado", page: "courses" });
}

function openEnrollmentForm(id) {
  const e = id ? findItem(id) : null;
  const { students = [], courses = [] } = CrudStore.meta;
  openModal(e ? "Editar matrícula" : "Crear matrícula", `
    ${e ? "" : `<label>Estudiante<select name="student_id" required>${optionsHtml(students, "id", (s) => `${s.student_code} — ${s.full_name}`, null)}</select></label>
    <label>Curso<select name="course_id" required>${optionsHtml(courses, "id", (c) => c.name, null)}</select></label>`}
    <label>Estado<select name="status">
      ${["activa", "retirada", "congelada"].map((st) => `<option value="${st}" ${e?.status === st ? "selected" : ""}>${st}</option>`).join("")}
    </select></label>
    <input type="hidden" name="id" value="${e?.id || ""}">
  `, "submitEnrollmentForm");
}

async function submitEnrollmentForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  if (body.student_id) body.student_id = Number(body.student_id);
  if (body.course_id) body.course_id = Number(body.course_id);
  if (id) return crudSave({ method: "PUT", path: `/enrollments/${id}`, body, success: "Matrícula actualizada", page: "enrollments" });
  return crudSave({ method: "POST", path: "/enrollments", body, success: "Matrícula creada", page: "enrollments" });
}

function openScheduleForm(id) {
  const s = id ? findItem(id) : null;
  const courses = CrudStore.meta.courses || [];
  const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
  openModal(s ? "Editar horario" : "Crear horario", `
    <label>Curso<select name="course_id" required>${optionsHtml(courses, "id", (c) => c.name, s?.course_id)}</select></label>
    <label>Día<select name="day_of_week">${days.map((d, i) => `<option value="${i}" ${s?.day_of_week === i ? "selected" : ""}>${d}</option>`).join("")}</select></label>
    <label>Inicio<input name="start_time" required placeholder="08:00" value="${esc(s?.start_time || "")}"></label>
    <label>Fin<input name="end_time" required placeholder="10:00" value="${esc(s?.end_time || "")}"></label>
    <label>Aula<input name="classroom" value="${esc(s?.classroom || "")}"></label>
    <input type="hidden" name="id" value="${s?.id || ""}">
  `, "submitScheduleForm");
}

async function submitScheduleForm(e) {
  const body = formBody(e);
  const id = body.id;
  delete body.id;
  body.course_id = Number(body.course_id);
  body.day_of_week = Number(body.day_of_week);
  if (id) return crudSave({ method: "PUT", path: `/schedules/${id}`, body, success: "Horario actualizado", page: "schedules" });
  return crudSave({ method: "POST", path: "/schedules", body, success: "Horario creado", page: "schedules" });
}

function openGradeForm(id) {
  const g = id ? findItem(id) : null;
  const { courses = [], students = [] } = CrudStore.meta;
  openModal(g ? "Editar nota" : "Registrar nota", `
    <label>Curso<select name="course_id" required>${optionsHtml(courses, "id", (c) => c.name, g?.course_id)}</select></label>
    <label>Estudiante<select name="student_id" required>${optionsHtml(students, "id", (s) => s.full_name, g?.student_id)}</select></label>
    <label>Parcial 1<input name="partial1" type="number" min="1" max="10" step="0.01" value="${g?.partial1 ?? ""}"></label>
    <label>Parcial 2<input name="partial2" type="number" min="1" max="10" step="0.01" value="${g?.partial2 ?? ""}"></label>
    <label>Supletorio<input name="supplementary" type="number" min="1" max="10" step="0.01" value="${g?.supplementary ?? ""}"></label>
  `, "submitGradeForm");
}

async function submitGradeForm(e) {
  const body = formBody(e);
  body.course_id = Number(body.course_id);
  body.student_id = Number(body.student_id);
  ["partial1", "partial2", "supplementary"].forEach((k) => {
    if (body[k] == null || body[k] === "") delete body[k];
    else body[k] = Number(body[k]);
  });
  return crudSave({ method: "POST", path: "/grades", body, success: "Nota guardada", page: "grades" });
}

function openAttendanceForm(id) {
  const a = id ? findItem(id) : null;
  const { courses = [], students = [] } = CrudStore.meta;
  openModal(a ? "Editar asistencia" : "Registrar asistencia", `
    <label>Curso<select name="course_id" required>${optionsHtml(courses, "id", (c) => c.name, a?.course_id)}</select></label>
    <label>Estudiante<select name="student_id" required>${optionsHtml(students, "id", (s) => s.full_name, a?.student_id)}</select></label>
    <label>Fecha<input name="session_date" type="date" required value="${esc(a?.session_date || "")}"></label>
    <label>Estado<select name="status">${["presente", "ausente", "tardanza", "justificada"].map((st) => `<option ${a?.status === st ? "selected" : ""}>${st}</option>`).join("")}</select></label>
    <label>Notas<input name="notes" value="${esc(a?.notes || "")}"></label>
  `, "submitAttendanceForm");
}

async function submitAttendanceForm(e) {
  const body = formBody(e);
  body.course_id = Number(body.course_id);
  body.student_id = Number(body.student_id);
  return crudSave({ method: "POST", path: "/attendance", body, success: "Asistencia guardada", page: "attendance" });
}

function openNotificationForm() {
  openModal("Enviar notificación", `
    <label>Título<input name="title" required></label>
    <label style="grid-column:1/-1">Mensaje<textarea name="message" rows="3" required></textarea></label>
    <label>Rol destino (opcional)<input name="role_code" placeholder="STUDENT, TEACHER…"></label>
  `, "submitNotificationForm");
}

async function submitNotificationForm(e) {
  const body = formBody(e);
  if (!body.role_code) delete body.role_code;
  return crudSave({ method: "POST", path: "/notifications", body, success: "Notificación enviada", page: "notifications" });
}

/* sendAI + initFloatChat → ai-chat.js (SPEC-017) */

async function saveConfig(e) {
  e.preventDefault();
  const raw = Object.fromEntries(new FormData(e.target).entries());
  const body = {
    system_name: (raw.system_name || "").trim(),
    primary_color: normalizeHexColor(raw.primary_color, "#0d6efd"),
    secondary_color: normalizeHexColor(raw.secondary_color, "#198754"),
    accent_color: normalizeHexColor(raw.accent_color, "#0dcaf0"),
    default_theme: raw.default_theme === "dark" ? "dark" : "light",
  };
  try {
    const res = await API.put("/config", body);
    const saved = res.config || body;
    applyBrandColors(saved);

    // SPEC-010: aplicar tema institucional de inmediato
    localStorage.removeItem("theme_override");
    applyTheme(saved.default_theme || body.default_theme);
    if (AppState.user) {
      AppState.user.theme = saved.default_theme || body.default_theme;
      API.put("/auth/theme", { theme: AppState.user.theme }).catch(() => {});
    }

    const check = await API.get("/config");
    const ok =
      normalizeHexColor(check.primary_color) === body.primary_color &&
      normalizeHexColor(check.secondary_color) === body.secondary_color &&
      (check.system_name || "") === body.system_name &&
      (check.default_theme || "light") === body.default_theme;
    const themeLabel = body.default_theme === "dark" ? "oscuro" : "claro";
    const hint = document.getElementById("configSaveHint");
    if (hint) {
      hint.style.color = ok ? "var(--secondary)" : "var(--danger)";
      hint.textContent = ok
        ? `Guardado: colores + tema ${themeLabel} aplicado`
        : "Guardado, pero la verificación no coincidió. Recargue la página.";
    }
    toast(ok ? `Configuración guardada — tema ${themeLabel} activo` : "Guardado con advertencia", ok ? "success" : "error");
  } catch (err) {
    toast(err.message, "error");
  }
  return false;
}

async function saveAI(e) {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target).entries());
  body.is_enabled = body.is_enabled === "true";
  body.temperature = Number(body.temperature);
  if (!body.api_key) delete body.api_key;
  try {
    await API.put("/ai/config", body);
    toast("Configuración IA guardada");
  } catch (err) {
    toast(err.message, "error");
  }
  return false;
}

async function downloadAuth(e, url) {
  e.preventDefault();
  const { access } = API.getTokens();
  try {
    const res = await fetch(url, { headers: { Authorization: `Bearer ${access}` } });
    if (!res.ok) throw new Error("No se pudo descargar");
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const cd = res.headers.get("Content-Disposition") || "";
    const m = cd.match(/filename="?([^"]+)"?/);
    a.download = m ? m[1] : "reporte.bin";
    a.click();
  } catch (err) {
    toast(err.message, "error");
  }
  return false;
}

/** SPEC-026: query params LogIA */
function buildLogIAQuery(f = {}) {
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  if (f.from) params.set("from", f.from);
  if (f.to) params.set("to", f.to);
  if (f.role) params.set("role", f.role);
  if (f.status) params.set("event_type", f.status);
  if (f.severity) params.set("severity", f.severity);
  if (f.conversation) params.set("conversation_id", f.conversation);
  if (f.username) params.set("username", f.username);
  params.set("limit", "300");
  return params.toString();
}

function syncLogIAFilters() {
  CrudStore.filters = getFilterState();
  return CrudStore.filters;
}

async function applyLogIAFilters() {
  syncLogIAFilters();
  await navigate("logia");
}

async function exportLogIA(fmt) {
  const allowed = ["xlsx", "pdf", "json"];
  if (!allowed.includes(fmt)) {
    toast("Formato no disponible", "error");
    return;
  }
  const f = syncLogIAFilters();
  const qs = buildLogIAQuery(f);
  await downloadAuth(new Event("click"), `/api/v1/ai/agent-logs/export.${fmt}?${qs}`);
}

function logout() {
  const { refresh } = API.getTokens();
  if (refresh) {
    fetch("/api/v1/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${refresh}` },
    }).catch(() => {});
  }
  API.clear();
  location.href = "/";
}

function toggleSidebar() {
  const sb = document.getElementById("sidebar");
  if (window.innerWidth <= 900) sb.classList.toggle("open");
  else sb.classList.toggle("collapsed");
}

async function bootApp() {
  const { access } = API.getTokens();
  if (!access) {
    location.href = "/";
    return;
  }
  try {
    const brand = await loadBrandColors();
    AppState.user = await API.get("/auth/me");
    localStorage.setItem("user", JSON.stringify(AppState.user));
    document.getElementById("userLabel").textContent = AppState.user.full_name;
    setImpersonationBanner();
    applyTheme(
      resolveTheme({
        userTheme: AppState.user.theme,
        defaultTheme: brand?.default_theme,
      })
    );
    renderSidebar();
    initFloatChat();
    initAIChat();
    const chat = document.getElementById("floatChat");
    if (chat && !hasPerm("ai.use")) chat.classList.add("hidden");
    navigate(defaultHomePage());
  } catch {
    API.clear();
    location.href = "/";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "app") bootApp();
});
