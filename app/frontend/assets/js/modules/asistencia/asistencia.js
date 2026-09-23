/* global SigaApi, SigaAuth, SigaToast, SigaTable, SigaModal, SigaAdminTable */
// Ref: PromptMaster FASE 6 | carrera → periodo → paralelo | attendance API
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody, fillSelect } = SigaTable;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  const canTeach = roles.includes("TEACHER") || roles.includes("ADMINISTRATOR");
  if (!canTeach) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  state.context = state.context || {};
  Object.assign(state.context, {
    careers: [],
    terms: [],
    courses: [],
    curricula: [],
    subjects: [],
    students: [],
    courseStudents: [],
    sessions: [],
    marks: [],
  });

  const SESSION_COLS = ["id", "course", "session_date", "topic"];
  const MARK_COLS = ["id", "session", "student", "status", "notes"];
  const el = (id) => document.getElementById(id);
  const sessionsTable = SigaAdminTable.bind({
    tbody: el("sessions-tbody"),
    columns: SESSION_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-sessions"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de sesión",
          body: SigaModal.viewDl(SESSION_COLS.map((k) => [k, row[k]])),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") {
        if (el("att-session-id")) el("att-session-id").value = String(row.id);
        openMarkForm();
      }
    },
  });
  const marksTable = SigaAdminTable.bind({
    tbody: el("marks-tbody"),
    columns: MARK_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-marks"),
    statusKeys: ["status"],
    actions: () => SigaAdminTable.actionButtons(["view", "edit"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de asistencia",
          body: SigaModal.viewDl(MARK_COLS.map((k) => [k, row[k]])),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") {
        if (el("att-session-id")) el("att-session-id").value = String(row.session_id);
        if (el("att-student-id")) el("att-student-id").value = String(row.student_id);
        if (el("att-status")) el("att-status").value = row.status;
        if (el("att-notes")) el("att-notes").value = row.notes || "";
        openMarkForm();
      }
    },
  });

  function openSessionForm() {
    const wrap = el("session-form-wrap");
    if (!wrap) return;
    SigaModal.openParked({
      title: "Nueva sesión",
      node: wrap,
      footer:
        '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
        '<button type="button" class="btn btn-siga" id="btn-modal-save-session">Guardar</button>',
    });
    document.getElementById("btn-modal-save-session")?.addEventListener("click", () => createSession());
  }

  function openMarkForm() {
    const wrap = el("mark-form-wrap");
    if (!wrap) return;
    SigaModal.openParked({
      title: "Marcar asistencia",
      node: wrap,
      footer:
        '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
        '<button type="button" class="btn btn-siga" id="btn-modal-save-mark">Guardar</button>',
      wide: true,
    });
    document.getElementById("btn-modal-save-mark")?.addEventListener("click", () => markAttendance());
  }

  function subjectName(id) {
    const s = state.context.subjects.find((x) => x.id === id);
    return s ? SigaTable.formatRef(s.id, (s.code || "") + " — " + (s.name || "")) : SigaTable.formatRef(id, "Asignatura");
  }
  function careerName(id) {
    const c = state.context.careers.find((x) => x.id === id);
    return c ? SigaTable.formatRef(c.id, (c.code || "") + " — " + (c.name || "")) : SigaTable.formatRef(id, "Carrera");
  }
  function termName(id) {
    const t = state.context.terms.find((x) => x.id === id);
    return t ? SigaTable.formatRef(t.id, (t.code || "") + " — " + (t.name || "")) : SigaTable.formatRef(id, "Periodo");
  }
  function studentLabel(s) {
    const id = s.id || s.student_id;
    const name = s.name || s.full_name || s.student_code || "Estudiante";
    return SigaTable.formatRef(id, name);
  }

  function mapSessionRow(row) {
    const course = state.context.courses.find((c) => Number(c.id) === Number(row.course_id));
    return {
      ...row,
      course: course ? parallelLabel(course) : SigaTable.formatRef(row.course_id, "Curso"),
    };
  }

  function mapMarkRow(row) {
    const student =
      state.context.courseStudents.find(
        (s) => Number(s.id) === Number(row.student_id) || Number(s.student_id) === Number(row.student_id)
      ) || state.context.students.find((s) => Number(s.id) === Number(row.student_id));
    const session = state.context.sessions.find((s) => Number(s.id) === Number(row.session_id));
    return {
      ...row,
      session: session ? sessionLabel(session) : SigaTable.formatRef(row.session_id, "Sesión"),
      student: student ? studentLabel(student) : SigaTable.formatRef(row.student_id, "Estudiante"),
    };
  }
  function parallelLabel(c) {
    const sub = state.context.subjects.find((x) => x.id === c.subject_id);
    const title = sub ? (sub.name || sub.code) : "Curso";
    const par = c.parallel_code ? " · " + c.parallel_code : "";
    return SigaTable.formatRef(c.id, title + par);
  }
  function sessionLabel(s) {
    return SigaTable.formatRef(s.id, (s.session_date || "Sesión") + (s.topic ? " · " + s.topic : ""));
  }

  function subjectIdsForCareer(careerId) {
    if (!careerId) return null;
    const ids = new Set();
    state.context.curricula
      .filter((cur) => cur.career_id === careerId && cur.status !== "INACTIVE")
      .forEach((cur) => (cur.subject_ids || []).forEach((sid) => ids.add(sid)));
    return ids.size ? ids : null;
  }

  function filteredCourses() {
    const careerId = Number(el("filter-career")?.value || 0);
    const termId = Number(el("filter-term")?.value || 0);
    let list = state.context.courses.slice();
    if (termId) list = list.filter((c) => c.term_id === termId);
    const subjectIds = subjectIdsForCareer(careerId);
    if (subjectIds) list = list.filter((c) => subjectIds.has(c.subject_id));
    return list;
  }

  function selectedCourseId() {
    return Number(el("filter-parallel")?.value || 0);
  }

  function updateCascadePath() {
    const path = el("cascade-path");
    if (!path) return;
    const careerId = Number(el("filter-career")?.value || 0);
    const courseId = selectedCourseId();
    const course = state.context.courses.find((c) => c.id === courseId);
    if (!course) {
      path.textContent = "Sin curso seleccionado.";
      return;
    }
    const parts = [];
    if (careerId) parts.push(careerName(careerId));
    parts.push(termName(course.term_id));
    parts.push(`Paralelo ${course.parallel_code} · ${subjectName(course.subject_id)}`);
    path.textContent = parts.join(" → ");
  }

  function hoursForCourse(course) {
    if (!course) return [1];
    const n = (course.hours_theory || 0) + (course.hours_practical || 0) || course.hours_attendable || 1;
    const count = Math.max(1, Number(n) || 1);
    return Array.from({ length: count }, (_, i) => i + 1);
  }

  function fillHourSlots(course) {
    const sel = el("att-hour");
    if (!sel) return;
    const hours = hoursForCourse(course);
    const current = sel.value;
    sel.innerHTML = hours.map((h) => '<option value="' + h + '">Hora ' + h + "</option>").join("");
    if (hours.map(String).includes(current)) sel.value = current;
  }

  function paintRoster(data) {
    const tbody = el("roster-tbody");
    if (!tbody) return;
    const students = (data && data.students) || [];
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (!students.length) {
      tbody.innerHTML = "";
      if (empty) empty.classList.remove("d-none");
      if (el("btn-save-roster")) el("btn-save-roster").disabled = true;
      return;
    }
    if (empty) empty.classList.add("d-none");
    tbody.innerHTML = students
      .map((s) => {
        const checked = s.present ? " checked" : "";
        return (
          "<tr><td>" +
          SigaModal.escapeHtml(String(s.student_id || s.id || "")) +
          "</td><td>" +
          SigaModal.escapeHtml(s.name || s.student_code || "") +
          '</td><td><input type="checkbox" class="form-check-input" data-student="' +
          s.student_id +
          '"' +
          checked +
          " /></td></tr>"
        );
      })
      .join("");
    if (el("btn-save-roster")) el("btn-save-roster").disabled = false;
  }

  async function loadRoster() {
    const courseId = selectedCourseId();
    const sessionDate = el("att-date")?.value;
    const hourSlot = Number(el("att-hour")?.value || 1);
    if (!courseId || !sessionDate) {
      paintRoster({ students: [] });
      return;
    }
    const { ok, data } = await api(
      "GET",
      "/attendance/roster?course_id=" +
        courseId +
        "&session_date=" +
        encodeURIComponent(sessionDate) +
        "&hour_slot=" +
        hourSlot
    );
    if (!ok) {
      toast(formatError(data), "bad");
      paintRoster({ students: [] });
      return;
    }
    if (data.hours_available && data.hours_available.length && el("att-hour")) {
      const current = el("att-hour").value;
      el("att-hour").innerHTML = data.hours_available
        .map((h) => '<option value="' + h + '">Hora ' + h + "</option>")
        .join("");
      el("att-hour").value = String(hourSlot || current || data.hours_available[0]);
    }
    paintRoster(data);
  }

  async function saveRoster() {
    const courseId = selectedCourseId();
    const sessionDate = el("att-date")?.value;
    const hourSlot = Number(el("att-hour")?.value || 1);
    if (!courseId || !sessionDate) {
      toast("Seleccione curso y fecha.", "bad");
      return;
    }
    const records = [...document.querySelectorAll("#roster-tbody [data-student]")].map((box) => ({
      student_id: Number(box.getAttribute("data-student")),
      status: box.checked ? "PRESENT" : "ABSENT",
    }));
    const { ok, data } = await api("PUT", "/attendance/bulk", {
      course_id: courseId,
      session_date: sessionDate,
      hour_slot: hourSlot,
      records,
    });
    toast(ok ? "Asistencia guardada." : formatError(data), ok ? "ok" : "bad");
    if (ok) {
      paintRoster(data);
      if (data.session_id && el("att-session-id")) {
        el("att-session-id").value = String(data.session_id);
      }
    }
  }

  function setCourseActionsEnabled(enabled) {
    ["btn-create-session", "btn-mark-att", "btn-att-pct", "att-student-id", "pct-student-id", "btn-save-roster"].forEach(
      (id) => {
        const node = el(id);
        if (node) node.disabled = !enabled;
      }
    );
  }

  function renderSessionSelect() {
    const courseId = selectedCourseId();
    const sessions = state.context.sessions.filter((s) => s.course_id === courseId);
    const sel = el("att-session-id");
    if (!sel) return;
    if (!sessions.length) {
      sel.innerHTML = '<option value="">Crea o elige sesión</option>';
      sel.disabled = true;
      return;
    }
    fillSelect(sel, sessions, sessionLabel, (s) => s.id);
    sel.disabled = false;
  }

  function renderLogs() {
    sessionsTable.setRows((state.context.sessions || []).map(mapSessionRow));
    marksTable.setRows((state.context.marks || []).map(mapMarkRow));
  }

  function fillTerms() {
    const termSel = el("filter-term");
    if (!termSel) return;
    fillSelect(
      termSel,
      state.context.terms,
      (t) => SigaTable.formatRef(t.id, (t.code || "") + " — " + (t.name || "") + (t.is_current ? " (actual)" : "")),
      (t) => t.id
    );
    termSel.disabled = !state.context.terms.length;
    const current = state.context.terms.find((t) => t.is_current);
    if (current) termSel.value = String(current.id);
  }

  async function loadCourseStudents(courseId) {
    if (!courseId) {
      state.context.courseStudents = [];
      fillSelect(el("att-student-id"), [], studentLabel, (s) => s.id);
      fillSelect(el("pct-student-id"), [], studentLabel, (s) => s.id);
      setCourseActionsEnabled(false);
      return;
    }
    const { ok, data } = await api("GET", `/enrollments?course_id=${courseId}`);
    const ens = ok && Array.isArray(data) ? data : [];
    const ids = new Set(ens.filter((e) => e.status === "ACTIVE").map((e) => e.student_id));
    state.context.courseStudents = state.context.students.filter((s) => ids.has(s.id));
    if (!state.context.courseStudents.length && ids.size) {
      state.context.courseStudents = [...ids].map((id) => ({ id, student_code: `EST-${id}` }));
    }
    fillSelect(el("att-student-id"), state.context.courseStudents, studentLabel, (s) => s.id);
    fillSelect(el("pct-student-id"), state.context.courseStudents, studentLabel, (s) => s.id);
    setCourseActionsEnabled(true);
    renderSessionSelect();
    const course = state.context.courses.find((c) => c.id === courseId);
    fillHourSlots(course);
    await loadRoster();
  }

  function fillParallels() {
    const parallel = el("filter-parallel");
    if (!parallel) return;
    const termId = Number(el("filter-term")?.value || 0);
    const courses = filteredCourses();
    if (!termId) {
      parallel.innerHTML = '<option value="">Selecciona periodo</option>';
      parallel.disabled = true;
      setCourseActionsEnabled(false);
      updateCascadePath();
      return;
    }
    if (!courses.length) {
      parallel.innerHTML = '<option value="">Sin paralelos para este filtro</option>';
      parallel.disabled = true;
      setCourseActionsEnabled(false);
      updateCascadePath();
      return;
    }
    fillSelect(parallel, courses, parallelLabel, (c) => c.id);
    parallel.disabled = false;
    onParallelChange().catch(() => toast("No se pudo cargar el curso", "bad"));
  }

  async function onParallelChange() {
    updateCascadePath();
    await loadCourseStudents(selectedCourseId());
  }

  async function loadContext() {
    const [careers, terms, courses, subjects, students, curricula, users] = await Promise.all([
      api("GET", "/careers"),
      api("GET", "/terms"),
      api("GET", "/courses"),
      api("GET", "/subjects"),
      api("GET", "/students"),
      api("GET", "/curricula"),
      api("GET", "/users"),
    ]);
    state.context.careers = careers.ok && Array.isArray(careers.data) ? careers.data : [];
    state.context.terms = terms.ok && Array.isArray(terms.data) ? terms.data : [];
    state.context.courses = courses.ok && Array.isArray(courses.data) ? courses.data : [];
    state.context.subjects = subjects.ok && Array.isArray(subjects.data) ? subjects.data : [];
    const userList = users.ok && Array.isArray(users.data) ? users.data : [];
    state.context.students = (students.ok && Array.isArray(students.data) ? students.data : []).map((s) => {
      const user = userList.find((u) => Number(u.id) === Number(s.user_id));
      const name = user
        ? [user.first_name, user.last_name].filter(Boolean).join(" ").trim() || user.full_name || user.username
        : "";
      return { ...s, name };
    });
    state.context.curricula = curricula.ok && Array.isArray(curricula.data) ? curricula.data : [];

    const careerSel = el("filter-career");
    if (careerSel) {
      careerSel.innerHTML = '<option value="">Todas / sin filtrar</option>';
      state.context.careers.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = String(c.id);
        opt.textContent = SigaTable.formatRef(c.id, (c.code || "") + " — " + (c.name || ""));
        careerSel.appendChild(opt);
      });
      SigaTable.makeSearchable(careerSel);
    }
    fillTerms();
    fillParallels();
    if (![careers, terms, courses].every((r) => r.ok)) {
      toast("No se pudieron cargar todos los catálogos de asistencia.", "bad");
    }
  }

  async function createSession() {
    const courseId = selectedCourseId();
    if (!courseId) {
      toast("Selecciona carrera → periodo → paralelo.", "bad");
      return;
    }
    const body = {
      course_id: courseId,
      session_date: el("att-date").value,
      topic: el("att-topic").value || null,
      hour_slot: Number(el("att-hour")?.value || 1),
    };
    if (!body.session_date) {
      toast("Indica la fecha de la sesión.", "bad");
      return;
    }
    const { ok, data } = await api("POST", "/attendance/sessions", body);
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    state.context.sessions = [data, ...state.context.sessions.filter((s) => s.id !== data.id)];
    renderSessionSelect();
    if (el("att-session-id")) el("att-session-id").value = String(data.id);
    renderLogs();
    toast("Sesión creada.", "ok");
  }

  async function markAttendance() {
    const studentId = Number(el("att-student-id")?.value || 0);
    const sessionId = Number(el("att-session-id")?.value || 0);
    if (!studentId || !sessionId) {
      toast("Indica sesión y estudiante.", "bad");
      return;
    }
    const body = {
      session_id: sessionId,
      student_id: studentId,
      status: el("att-status").value,
      notes: (el("att-notes")?.value || "").trim() || null,
    };
    const { ok, data } = await api("PUT", "/attendance/records", body);
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    state.context.marks = [data, ...state.context.marks].slice(0, 20);
    renderLogs();
    toast("Asistencia guardada.", "ok");
  }

  async function attendancePercent() {
    const courseId = selectedCourseId();
    let studentId = Number(el("pct-student-id")?.value || 0);
    if (!studentId) studentId = Number(el("att-student-id")?.value || 0);
    if (!courseId || !studentId) {
      toast("Selecciona paralelo y estudiante.", "bad");
      return;
    }
    const { ok, data } = await api(
      "GET",
      `/attendance/courses/${courseId}/students/${studentId}/percent`
    );
    const out = el("pct-result");
    if (!ok) {
      if (out) out.textContent = formatError(data);
      toast(formatError(data), "bad");
      return;
    }
    const msg = `Asistencia: ${data.percentage}%`;
    if (out) out.textContent = msg;
    toast(msg, "ok");
  }

  const dateEl = el("att-date");
  if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);

  el("btn-new-record")?.addEventListener("click", () => openSessionForm());
  el("btn-create-session")?.addEventListener("click", () => createSession());
  el("btn-mark-att")?.addEventListener("click", () => markAttendance());
  el("btn-att-pct")?.addEventListener("click", () => attendancePercent());
  el("filter-career")?.addEventListener("change", () => fillParallels());
  el("filter-term")?.addEventListener("change", () => fillParallels());
  el("filter-parallel")?.addEventListener("change", () => {
    onParallelChange().catch(() => toast("No se pudo cargar el curso", "bad"));
  });
  el("btn-load-roster")?.addEventListener("click", () => loadRoster());
  el("btn-save-roster")?.addEventListener("click", () => saveRoster());
  el("att-date")?.addEventListener("change", () => loadRoster());
  el("att-hour")?.addEventListener("change", () => loadRoster());

  await loadContext();
})();
