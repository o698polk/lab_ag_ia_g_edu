// Ref: K-022 | Shared UI helpers — fill existing DOM only (no page layout).
/* global SigaApi */

const METRIC_LABEL = {
  students: "Estudiantes",
  teachers: "Docentes",
  courses: "Cursos",
  enrollments: "Matrículas activas",
  users: "Usuarios",
  grades: "Notas",
  attendance_sessions: "Sesiones de clase",
  careers: "Carreras",
  unread_notifications: "Avisos sin leer",
  assigned_courses: "Cursos asignados",
  grades_recorded: "Notas registradas",
  my_courses: "Mis cursos",
  my_grades: "Mis notas",
  my_kardex: "Entradas de kardex",
};

const COL_LABEL = {
  id: "Id",
  score: "Nota",
  comment: "Comentario",
  evaluation_id: "Evaluación",
  student_id: "Estudiante",
  graded_by_teacher_id: "Docente",
  graded_at: "Fecha",
  academic_status: "Estado académico",
  final_grade: "Nota final",
  credits: "Créditos",
  term_id: "Periodo",
  subject_id: "Materia",
  course_id: "Curso",
  code: "Código",
  name: "Nombre",
  status: "Estado",
  parallel_code: "Paralelo",
  capacity: "Cupo",
  title: "Título",
  body: "Mensaje",
  type: "Tipo",
  student_code: "Código estudiante",
  teacher_code: "Código docente",
  specialty: "Especialidad",
  level: "Nivel",
  username: "Usuario",
  email: "Correo",
};

let toastTimer;

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function toast(message, kind) {
  const el = $("toast");
  if (!el) return;
  el.textContent = message;
  el.className = `siga-toast show ${kind || ""}`.trim();
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3400);
}

function renderTable(container, rows) {
  if (!container) return;
  if (!rows || !rows.length) {
    container.innerHTML = `<p class="empty-state mb-0">No hay datos para mostrar.</p>`;
    return;
  }
  const keys = Object.keys(rows[0]);
  const head = keys.map((k) => `<th>${COL_LABEL[k] || k}</th>`).join("");
  const body = rows
    .map(
      (row) =>
        `<tr>${keys.map((k) => `<td>${escapeHtml(row[k] ?? "")}</td>`).join("")}</tr>`
    )
    .join("");
  container.innerHTML = `<table class="table table-sm table-hover align-middle"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function fillSelect(el, items, labelFn, valueFn) {
  if (!el) return;
  const current = el.value;
  if (!items || !items.length) {
    el.innerHTML = `<option value="">Sin datos</option>`;
    return;
  }
  el.innerHTML = items
    .map((item) => {
      const value = valueFn(item);
      const label = labelFn(item);
      return `<option value="${value}">${escapeHtml(label)}</option>`;
    })
    .join("");
  if (current && [...el.options].some((o) => o.value === current)) {
    el.value = current;
  }
}

function setSessionChip(user) {
  const chip = $("session-chip");
  if (!chip) return;
  if (!user) {
    chip.textContent = "Sin sesión";
    chip.classList.remove("ok");
    chip.classList.add("muted");
    return;
  }
  chip.textContent = `${user.username} · ${(user.roles || []).join(", ") || "sin rol"}`;
  chip.classList.add("ok");
  chip.classList.remove("muted");
}

function applyRoleVisibility(user) {
  const roles = (user && user.roles) || [];
  document.querySelectorAll("[data-roles]").forEach((el) => {
    const wanted = String(el.getAttribute("data-roles") || "")
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
    const show = !wanted.length || wanted.some((r) => roles.includes(r));
    el.classList.toggle("d-none", !show);
  });
}

function wireMobileNav() {
  const btn = $("btn-menu");
  const shell = document.querySelector(".shell");
  if (!btn || !shell) return;
  btn.addEventListener("click", () => {
    const open = shell.classList.toggle("nav-open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
}

window.SigaUi = {
  $,
  toast,
  escapeHtml,
  renderTable,
  fillSelect,
  setSessionChip,
  applyRoleVisibility,
  wireMobileNav,
  METRIC_LABEL,
  COL_LABEL,
};
