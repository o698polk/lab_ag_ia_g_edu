/* Helpers CRUD: búsqueda avanzada, filtros por rol/fechas, exportes, modal — SPEC-019 */

const CrudStore = { items: [], page: "", meta: {}, filters: {} };

function esc(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function userRoles() {
  return AppState.user?.roles || [];
}

function isStaffRole() {
  return userRoles().some((r) =>
    ["ADMIN", "RECTOR", "COORDINATOR", "SECRETARY", "AUDITOR", "REVIEWER", "IT_SUPPORT"].includes(r)
  );
}

function canExport(exportType) {
  if (
    hasPerm("reports.export") ||
    hasPerm("grades.view") ||
    hasPerm("attendance.view") ||
    hasPerm("students.view") ||
    hasPerm("enrollments.view") ||
    hasPerm("users.view") ||
    hasPerm("teachers.view") ||
    hasPerm("careers.view") ||
    hasPerm("subjects.view") ||
    hasPerm("terms.view") ||
    hasPerm("courses.view") ||
    hasPerm("schedules.view") ||
    hasPerm("notifications.view") ||
    hasPerm("audit.view")
  ) {
    return true;
  }
  return !!exportType;
}

/**
 * Barra de módulo con búsqueda, filtros contextuales y exportación.
 * opts.filters: ['dates','career','term','course','status','role']
 * opts.exportType: clave del catálogo de reportes
 * opts.statusOptions: string[]
 * opts.roleOptions: [{code,name}] o string[] de códigos
 */
function moduleHeader(title, opts = {}) {
  const {
    createPerm,
    createLabel = "Crear",
    onCreate,
    filters = [],
    exportType = null,
    statusOptions = [],
    roleOptions = null,
  } = opts;
  const canCreate = createPerm ? hasPerm(createPerm) : false;
  const careers = CrudStore.meta.careers || [];
  const terms = CrudStore.meta.terms || [];
  const courses = CrudStore.meta.courses || [];
  const rolesMeta = roleOptions || CrudStore.meta.roles || [];

  const roles = userRoles();
  const isTeacher = roles.includes("TEACHER");
  const showCareer = filters.includes("career") && isStaffRole() && careers.length;
  const showTerm =
    filters.includes("term") &&
    terms.length &&
    (isStaffRole() || isTeacher || hasPerm("terms.view"));
  const showCourse =
    filters.includes("course") &&
    courses.length &&
    (isStaffRole() || isTeacher);
  const showStatus = filters.includes("status") && statusOptions.length;
  const showDates = filters.includes("dates");
  const showRole = filters.includes("role") && rolesMeta.length;
  const showExport = exportType && canExport(exportType);

  const filterBits = [];
  if (showDates) {
    filterBits.push(`
      <label class="filter-field">Desde
        <input type="date" id="filterFrom" onchange="applyAdvancedFilters()">
      </label>
      <label class="filter-field">Hasta
        <input type="date" id="filterTo" onchange="applyAdvancedFilters()">
      </label>`);
  }
  if (showRole) {
    const optsHtml = rolesMeta
      .map((r) => {
        const code = typeof r === "string" ? r : r.code;
        const label = typeof r === "string" ? r : r.name || r.code;
        return `<option value="${esc(code)}">${esc(label)}</option>`;
      })
      .join("");
    filterBits.push(`
      <label class="filter-field">Rol
        <select id="filterRole" onchange="applyAdvancedFilters()">
          <option value="">Todos</option>
          ${optsHtml}
        </select>
      </label>`);
  }
  if (showCareer) {
    filterBits.push(`
      <label class="filter-field">Carrera
        <select id="filterCareer" onchange="applyAdvancedFilters()">
          <option value="">Todas</option>
          ${optionsHtml(careers, "id", (c) => c.name)}
        </select>
      </label>`);
  }
  if (showTerm) {
    filterBits.push(`
      <label class="filter-field">Periodo
        <select id="filterTerm" onchange="applyAdvancedFilters()">
          <option value="">Todos</option>
          ${optionsHtml(terms, "id", (t) => t.name)}
        </select>
      </label>`);
  }
  if (showCourse) {
    filterBits.push(`
      <label class="filter-field">Curso
        <select id="filterCourse" onchange="applyAdvancedFilters()">
          <option value="">Todos</option>
          ${optionsHtml(courses, "id", (c) => c.name)}
        </select>
      </label>`);
  }
  if (showStatus) {
    filterBits.push(`
      <label class="filter-field">Estado
        <select id="filterStatus" onchange="applyAdvancedFilters()">
          <option value="">Todos</option>
          ${statusOptions.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join("")}
        </select>
      </label>`);
  }

  const exportBtns = showExport
    ? `
    <button type="button" class="btn-ghost" title="Excel" onclick="exportReport('${exportType}','xlsx')">
      <i class="bi bi-file-earmark-excel"></i> Excel
    </button>
    <button type="button" class="btn-ghost" title="PDF" onclick="exportReport('${exportType}','pdf')">
      <i class="bi bi-file-earmark-pdf"></i> PDF
    </button>`
    : "";

  return `
  <div class="module-header">
    <h2>${esc(title)}</h2>
    <div class="module-actions">
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input type="search" id="moduleSearch" placeholder="Buscar…" oninput="applyAdvancedFilters()" autocomplete="off">
      </div>
      ${exportBtns}
      ${
        canCreate
          ? `<button type="button" class="btn-primary-app" onclick="${onCreate}"><i class="bi bi-plus-lg"></i> ${esc(createLabel)}</button>`
          : ""
      }
    </div>
  </div>
  ${filterBits.length ? `<div class="filter-bar">${filterBits.join("")}</div>` : ""}
  <p class="module-count" id="moduleCount"></p>`;
}

function getFilterState() {
  return {
    q: (document.getElementById("moduleSearch")?.value || "").toLowerCase().trim(),
    from: document.getElementById("filterFrom")?.value || "",
    to: document.getElementById("filterTo")?.value || "",
    career: document.getElementById("filterCareer")?.value || "",
    term: document.getElementById("filterTerm")?.value || "",
    course: document.getElementById("filterCourse")?.value || "",
    status: document.getElementById("filterStatus")?.value || "",
    role: document.getElementById("filterRole")?.value || "",
    // SPEC-026 LogIA
    username: document.getElementById("filterUsername")?.value || "",
    conversation: document.getElementById("filterConversation")?.value || "",
    severity: document.getElementById("filterSeverity")?.value || "",
  };
}

function applyAdvancedFilters() {
  const f = getFilterState();
  CrudStore.filters = f;
  const rows = document.querySelectorAll("#moduleTableBody tr[data-search]");
  let visible = 0;
  rows.forEach((tr) => {
    const search = (tr.dataset.search || "").toLowerCase();
    const date = tr.dataset.date || "";
    const career = tr.dataset.career || "";
    const term = tr.dataset.term || "";
    const course = tr.dataset.course || "";
    const status = (tr.dataset.status || "").toLowerCase();
    const role = (tr.dataset.role || "").toUpperCase();
    const roles = (tr.dataset.roles || "").toUpperCase();

    let ok = true;
    if (f.q && !search.includes(f.q)) ok = false;
    if (ok && f.from && (!date || date < f.from)) ok = false;
    if (ok && f.to && (!date || date > f.to)) ok = false;
    if (ok && f.career && career !== f.career) ok = false;
    if (ok && f.term && term !== f.term) ok = false;
    if (ok && f.course && course !== f.course) ok = false;
    if (ok && f.status && status !== f.status.toLowerCase()) ok = false;
    if (ok && f.role) {
      const want = f.role.toUpperCase();
      const bag = roles || role;
      if (!bag.split(/[,\s]+/).filter(Boolean).includes(want) && bag !== want) ok = false;
    }

    tr.style.display = ok ? "" : "none";
    if (ok) visible++;
  });
  const count = document.getElementById("moduleCount");
  if (count) {
    const parts = [`${visible} registro(s)`];
    if (f.q || f.from || f.to || f.career || f.term || f.course || f.status || f.role) {
      parts.push("filtrados");
    }
    count.textContent = parts.join(" ");
  }
}

function filterModuleRows(q) {
  const el = document.getElementById("moduleSearch");
  if (el && q != null) el.value = q;
  applyAdvancedFilters();
}

function buildReportQuery() {
  const f = getFilterState();
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  if (f.from) params.set("from", f.from);
  if (f.to) params.set("to", f.to);
  if (f.career) params.set("career_id", f.career);
  if (f.term) params.set("term_id", f.term);
  if (f.course) params.set("course_id", f.course);
  if (f.status) params.set("status", f.status);
  if (f.role) params.set("role", f.role);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

const EXPORT_TYPES = [
  "grades",
  "attendance",
  "enrollments",
  "students",
  "users",
  "teachers",
  "careers",
  "subjects",
  "terms",
  "courses",
  "schedules",
  "notifications",
  "audit",
];

async function exportReport(type, format) {
  if (!EXPORT_TYPES.includes(type)) {
    toast("Tipo de reporte no disponible", "error");
    return;
  }
  await downloadAuth(new Event("click"), `/api/v1/reports/${type}.${format}${buildReportQuery()}`);
}

function actionButtons({ edit, remove, extra = "" } = {}) {
  const parts = [];
  if (edit) parts.push(`<button type="button" class="btn-icon" title="Editar" onclick="${edit}"><i class="bi bi-pencil"></i></button>`);
  if (remove) parts.push(`<button type="button" class="btn-icon danger" title="Eliminar" onclick="${remove}"><i class="bi bi-trash"></i></button>`);
  if (extra) parts.push(extra);
  return `<div class="row-actions">${parts.join("")}</div>`;
}

function openModal(title, formHtml, onSubmitName) {
  const overlay = document.getElementById("crudModal");
  document.getElementById("crudModalTitle").textContent = title;
  document.getElementById("crudModalBody").innerHTML = `
    <form id="crudForm" class="form-grid" onsubmit="return ${onSubmitName}(event)">
      ${formHtml}
      <div class="modal-footer" style="grid-column:1/-1">
        <button type="button" class="btn-ghost" onclick="closeModal()">Cancelar</button>
        <button type="submit" class="btn-primary-app">Guardar</button>
      </div>
    </form>`;
  overlay.classList.remove("hidden");
}

function closeModal() {
  document.getElementById("crudModal")?.classList.add("hidden");
}

function formBody(e) {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target).entries());
  Object.keys(body).forEach((k) => {
    if (body[k] === "") body[k] = null;
  });
  return body;
}

async function crudSave({ method, path, body, success, page }) {
  try {
    if (method === "POST") await API.post(path, body);
    else if (method === "PUT") await API.put(path, body);
    toast(success || "Guardado");
    closeModal();
    navigate(page);
  } catch (err) {
    toast(err.message, "error");
  }
  return false;
}

async function crudDelete(path, page, label = "este registro") {
  if (!confirm(`¿Eliminar ${label}?`)) return;
  try {
    await API.del(path);
    toast("Eliminado");
    navigate(page);
  } catch (err) {
    toast(err.message, "error");
  }
}

function optionsHtml(items, valueKey, labelFn, selected) {
  return (items || [])
    .map((i) => {
      const val = i[valueKey];
      const sel = String(val) === String(selected) ? "selected" : "";
      return `<option value="${esc(val)}" ${sel}>${esc(labelFn(i))}</option>`;
    })
    .join("");
}

function dataSearch(...parts) {
  return esc(parts.filter((p) => p != null && p !== "").join(" ").toLowerCase());
}

function dataAttrs(obj) {
  const parts = [];
  if (obj.date) parts.push(`data-date="${esc(obj.date)}"`);
  if (obj.career != null && obj.career !== "") parts.push(`data-career="${esc(obj.career)}"`);
  if (obj.term != null && obj.term !== "") parts.push(`data-term="${esc(obj.term)}"`);
  if (obj.course != null && obj.course !== "") parts.push(`data-course="${esc(obj.course)}"`);
  if (obj.status) parts.push(`data-status="${esc(String(obj.status).toLowerCase())}"`);
  if (obj.role) parts.push(`data-role="${esc(String(obj.role).toUpperCase())}"`);
  if (obj.roles) {
    const list = Array.isArray(obj.roles) ? obj.roles.join(",") : obj.roles;
    parts.push(`data-roles="${esc(String(list).toUpperCase())}"`);
  }
  return parts.join(" ");
}
