/* global SigaApi, SigaAuth, SigaToast, SigaTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillSelect } = SigaTable;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  const canTeach = roles.includes("TEACHER") || roles.includes("ADMINISTRATOR");
  if (!canTeach) {
    location.replace("/ui/pages/notas/notas.html");
    return;
  }

  const el = (id) => document.getElementById(id);
  if (el("att-date") && !el("att-date").value) {
    el("att-date").value = new Date().toISOString().slice(0, 10);
  }

  function courseLabel(course) {
    return SigaTable.formatRef(
      course.id,
      course.course_name || course.parallel_code,
      course.subject_name
    );
  }

  function selectedCourse() {
    const id = Number(el("filter-course")?.value || 0);
    return (state.context?.courses || []).find((c) => Number(c.id) === id) || null;
  }

  function paintHours(course) {
    const sel = el("att-hour");
    if (!sel) return;
    const n = Math.max(1, Number(course && course.hours_attendable) || 1);
    const items = [];
    for (let i = 1; i <= n; i += 1) items.push({ id: i, name: "Hora " + i });
    fillSelect(sel, items, (h) => h.name, (h) => h.id, "");
    if (!sel.value) sel.value = "1";
  }

  function paintCourseMeta(course) {
    const path = el("cascade-path");
    if (!path) return;
    if (!course) {
      path.textContent = "Sin curso seleccionado.";
      return;
    }
    path.textContent =
      "Curso: " +
      (course.course_name || course.parallel_code || "—") +
      " · Materia: " +
      (course.subject_name || "—") +
      " · Periodo: " +
      (course.term_name || "—");
  }

  function paintRoster(students) {
    const tbody = el("roster-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (!students.length) {
      if (empty) {
        empty.textContent = "No hay estudiantes matriculados en este curso.";
        empty.classList.remove("d-none");
      }
      if (el("btn-save-roster")) el("btn-save-roster").disabled = true;
      return;
    }
    if (empty) empty.classList.add("d-none");
    students.forEach((row, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        (idx + 1) +
        "</td><td>" +
        SigaTable.escapeHtml(row.name) +
        "</td><td><input class='form-check-input' type='checkbox' data-student='" +
        row.student_id +
        "'" +
        (row.present ? " checked" : "") +
        " /></td>";
      tbody.appendChild(tr);
    });
    if (el("btn-save-roster")) el("btn-save-roster").disabled = false;
  }

  async function loadCourses() {
    const { ok, data } = await api("GET", "/courses");
    const courses = ok && Array.isArray(data) ? data : [];
    state.context = state.context || {};
    state.context.courses = courses;
    fillSelect(el("filter-course"), courses, courseLabel, (c) => c.id, "Seleccionar curso…");
    if (!ok) toast(formatError(data), "bad");
  }

  async function loadRoster() {
    const course = selectedCourse();
    paintCourseMeta(course);
    paintHours(course);
    if (!course || !el("att-date")?.value) {
      paintRoster([]);
      return;
    }
    const hour = Number(el("att-hour")?.value || 1);
    const qs =
      "?course_id=" +
      course.id +
      "&session_date=" +
      encodeURIComponent(el("att-date").value) +
      "&hour_slot=" +
      hour;
    const { ok, data } = await api("GET", "/attendance/roster" + qs);
    if (!ok) {
      toast(formatError(data), "bad");
      paintRoster([]);
      return;
    }
    paintRoster(data.students || []);
  }

  async function saveRoster() {
    const course = selectedCourse();
    if (!course || !el("att-date")?.value) {
      toast("Seleccione curso y fecha.", "bad");
      return;
    }
    const records = [...document.querySelectorAll("#roster-tbody [data-student]")].map((box) => ({
      student_id: Number(box.getAttribute("data-student")),
      status: box.checked ? "PRESENT" : "ABSENT",
    }));
    const { ok, data } = await api("PUT", "/attendance/bulk", {
      course_id: course.id,
      session_date: el("att-date").value,
      hour_slot: Number(el("att-hour")?.value || 1),
      records,
    });
    toast(ok ? "Asistencia guardada." : formatError(data), ok ? "ok" : "bad");
    if (ok) paintRoster(data.students || []);
  }

  el("filter-course")?.addEventListener("change", () => loadRoster());
  el("att-date")?.addEventListener("change", () => loadRoster());
  el("att-hour")?.addEventListener("change", () => loadRoster());
  el("btn-load-roster")?.addEventListener("click", () => loadRoster());
  el("btn-save-roster")?.addEventListener("click", () => saveRoster());

  await loadCourses();
  await loadRoster();
})();
