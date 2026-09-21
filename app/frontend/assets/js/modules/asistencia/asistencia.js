/* global SigaApi, SigaAuth, SigaToast, SigaTable */
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

  const SESSION_COLS = ["id", "course_id", "session_date", "topic"];
  const MARK_COLS = ["id", "session_id", "student_id", "status", "notes"];
  const el = (id) => document.getElementById(id);

  function subjectName(id) {
    const s = state.context.subjects.find((x) => x.id === id);
    return s ? `${s.code} — ${s.name}` : `Materia ${id}`;
  }
  function careerName(id) {
    const c = state.context.careers.find((x) => x.id === id);
    return c ? `${c.code} — ${c.name}` : `Carrera ${id}`;
  }
  function termName(id) {
    const t = state.context.terms.find((x) => x.id === id);
    return t ? `${t.code} — ${t.name}` : `Periodo ${id}`;
  }
  function studentLabel(s) {
    return `${s.student_code || "EST"} (id ${s.id})`;
  }
  function parallelLabel(c) {
    return `${c.parallel_code} · ${subjectName(c.subject_id)} · curso ${c.id}`;
  }
  function sessionLabel(s) {
    return `#${s.id} · ${s.session_date}${s.topic ? " · " + s.topic : ""}`;
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

  function setCourseActionsEnabled(enabled) {
    ["btn-create-session", "btn-mark-att", "btn-att-pct", "att-student-id", "pct-student-id"].forEach(
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
    if (el("sessions-tbody")) {
      fillTbody(el("sessions-tbody"), state.context.sessions, SESSION_COLS);
    }
    if (el("marks-tbody")) {
      fillTbody(el("marks-tbody"), state.context.marks, MARK_COLS);
    }
  }

  function fillTerms() {
    const termSel = el("filter-term");
    if (!termSel) return;
    fillSelect(
      termSel,
      state.context.terms,
      (t) => `${t.code} — ${t.name}${t.is_current ? " (actual)" : ""}`,
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
    const [careers, terms, courses, subjects, students, curricula] = await Promise.all([
      api("GET", "/careers"),
      api("GET", "/terms"),
      api("GET", "/courses"),
      api("GET", "/subjects"),
      api("GET", "/students"),
      api("GET", "/curricula"),
    ]);
    state.context.careers = careers.ok && Array.isArray(careers.data) ? careers.data : [];
    state.context.terms = terms.ok && Array.isArray(terms.data) ? terms.data : [];
    state.context.courses = courses.ok && Array.isArray(courses.data) ? courses.data : [];
    state.context.subjects = subjects.ok && Array.isArray(subjects.data) ? subjects.data : [];
    state.context.students = students.ok && Array.isArray(students.data) ? students.data : [];
    state.context.curricula = curricula.ok && Array.isArray(curricula.data) ? curricula.data : [];

    const careerSel = el("filter-career");
    if (careerSel) {
      careerSel.innerHTML = '<option value="">Todas / sin filtrar</option>';
      state.context.careers.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = String(c.id);
        opt.textContent = `${c.code} — ${c.name}`;
        careerSel.appendChild(opt);
      });
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

  el("btn-create-session")?.addEventListener("click", () => createSession());
  el("btn-mark-att")?.addEventListener("click", () => markAttendance());
  el("btn-att-pct")?.addEventListener("click", () => attendancePercent());
  el("filter-career")?.addEventListener("change", () => fillParallels());
  el("filter-term")?.addEventListener("change", () => fillParallels());
  el("filter-parallel")?.addEventListener("change", () => {
    onParallelChange().catch(() => toast("No se pudo cargar el curso", "bad"));
  });

  await loadContext();
})();
