/* global SigaApi, SigaAuth, SigaToast, SigaTable */
// Ref: PromptMaster FASE 5 | carrera → periodo → paralelo | endpoints existentes
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody, fillSelect } = SigaTable;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  const canTeach = roles.includes("TEACHER") || roles.includes("ADMINISTRATOR");
  if (location.pathname.includes("ingreso-notas") && !canTeach) {
    location.replace("/ui/pages/notas/notas.html");
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
    enrollments: [],
    evaluations: [],
    courseStudents: [],
  });

  const GRADE_COLS = ["id", "evaluation_id", "student_id", "score", "comment", "graded_at"];
  const KARDEX_COLS = ["id", "term_id", "subject_id", "final_grade", "academic_status", "credits"];

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

  function evaluationLabel(e) {
    return `${e.name} (${e.weight_percent}%) · id ${e.id}`;
  }

  function parallelLabel(c) {
    return `${c.parallel_code} · ${subjectName(c.subject_id)} · curso ${c.id}`;
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

  function showGradesPanel() {
    el("panel-grades")?.classList.remove("d-none");
    el("panel-kardex")?.classList.add("d-none");
  }

  function showKardexPanel() {
    el("panel-grades")?.classList.add("d-none");
    el("panel-kardex")?.classList.remove("d-none");
  }

  function showGradeRows(rows) {
    showGradesPanel();
    fillTbody(el("grades-tbody"), rows, GRADE_COLS);
  }

  function updateCascadePath() {
    const path = el("cascade-path");
    if (!path) return;
    const careerId = Number(el("filter-career")?.value || 0);
    const termId = Number(el("filter-term")?.value || 0);
    const courseId = Number(el("filter-parallel")?.value || 0);
    const course = state.context.courses.find((c) => c.id === courseId);
    if (!course) {
      path.textContent = "Sin curso seleccionado.";
      return;
    }
    const parts = [];
    if (careerId) parts.push(careerName(careerId));
    parts.push(termName(course.term_id || termId));
    parts.push(`Paralelo ${course.parallel_code} · ${subjectName(course.subject_id)}`);
    path.textContent = parts.join(" → ");
  }

  function setCourseActionsEnabled(enabled) {
    ["btn-course-grades", "btn-upsert-grade", "grade-eval-id", "grade-student-id"].forEach((id) => {
      const node = el(id);
      if (node) node.disabled = !enabled;
    });
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

  async function loadEvaluationsAndStudents(courseId) {
    if (!courseId) {
      state.context.evaluations = [];
      state.context.courseStudents = [];
      fillSelect(el("grade-eval-id"), [], evaluationLabel, (e) => e.id);
      fillSelect(el("grade-student-id"), [], studentLabel, (s) => s.id);
      setCourseActionsEnabled(false);
      return;
    }
    const [evals, enrollments] = await Promise.all([
      api("GET", `/courses/${courseId}/evaluations`),
      api("GET", `/enrollments?course_id=${courseId}`),
    ]);
    state.context.evaluations = evals.ok && Array.isArray(evals.data) ? evals.data : [];
    const ens = enrollments.ok && Array.isArray(enrollments.data) ? enrollments.data : [];
    const studentIds = new Set(
      ens.filter((e) => e.status === "ACTIVE").map((e) => e.student_id)
    );
    state.context.courseStudents = state.context.students.filter((s) => studentIds.has(s.id));
    if (!state.context.courseStudents.length && studentIds.size) {
      state.context.courseStudents = [...studentIds].map((id) => ({
        id,
        student_code: `EST-${id}`,
      }));
    }
    fillSelect(el("grade-eval-id"), state.context.evaluations, evaluationLabel, (e) => e.id);
    fillSelect(el("grade-student-id"), state.context.courseStudents, studentLabel, (s) => s.id);
    setCourseActionsEnabled(true);
  }

  async function onParallelChange() {
    const courseId = Number(el("filter-parallel")?.value || 0);
    updateCascadePath();
    await loadEvaluationsAndStudents(courseId);
  }

  async function loadContext() {
    if (!canTeach) return;

    const [careers, terms, courses, subjects, students, curricula, enrollments] = await Promise.all([
      api("GET", "/careers"),
      api("GET", "/terms"),
      api("GET", "/courses"),
      api("GET", "/subjects"),
      api("GET", "/students"),
      api("GET", "/curricula"),
      api("GET", "/enrollments"),
    ]);

    state.context.careers = careers.ok && Array.isArray(careers.data) ? careers.data : [];
    state.context.terms = terms.ok && Array.isArray(terms.data) ? terms.data : [];
    state.context.courses = courses.ok && Array.isArray(courses.data) ? courses.data : [];
    state.context.subjects = subjects.ok && Array.isArray(subjects.data) ? subjects.data : [];
    state.context.students = students.ok && Array.isArray(students.data) ? students.data : [];
    state.context.curricula = curricula.ok && Array.isArray(curricula.data) ? curricula.data : [];
    state.context.enrollments =
      enrollments.ok && Array.isArray(enrollments.data) ? enrollments.data : [];

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
      toast("No se pudieron cargar todos los catálogos del flujo de notas.", "bad");
    }
  }

  async function loadMyGrades() {
    const { ok, data } = await api("GET", "/me/grades");
    if (!ok) {
      toast(formatError(data), "bad");
      showGradeRows([]);
      return;
    }
    showGradeRows(Array.isArray(data) ? data : [data]);
    toast("Notas cargadas.", "ok");
  }

  async function loadMyKardex() {
    const { ok, data } = await api("GET", "/me/kardex");
    if (!ok) {
      toast(formatError(data), "bad");
      showKardexPanel();
      fillTbody(el("kardex-tbody"), [], KARDEX_COLS);
      return;
    }
    showKardexPanel();
    fillTbody(el("kardex-tbody"), Array.isArray(data) ? data : [data], KARDEX_COLS);
    toast("Kardex cargado.", "ok");
  }

  async function loadCourseGrades() {
    const courseId = Number(el("filter-parallel")?.value || 0);
    if (!courseId) {
      toast("Selecciona carrera → periodo → paralelo.", "bad");
      return;
    }
    const { ok, data } = await api("GET", `/courses/${courseId}/grades`);
    if (!ok) {
      toast(formatError(data), "bad");
      showGradeRows([]);
      return;
    }
    showGradeRows(Array.isArray(data) ? data : [data]);
    toast("Notas del curso cargadas.", "ok");
  }

  async function upsertGrade() {
    const evaluationId = Number(el("grade-eval-id")?.value || 0);
    const studentId = Number(el("grade-student-id")?.value || 0);
    if (!evaluationId || !studentId) {
      toast("Selecciona evaluación y estudiante.", "bad");
      return;
    }
    const body = {
      evaluation_id: evaluationId,
      student_id: studentId,
      score: Number(el("grade-score").value),
      comment: el("grade-comment").value || null,
    };
    const { ok, data } = await api("PUT", "/grades", body);
    toast(ok ? "Nota guardada." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadCourseGrades();
  }

  el("btn-my-grades")?.addEventListener("click", () => loadMyGrades());
  el("btn-my-kardex")?.addEventListener("click", () => loadMyKardex());
  el("btn-course-grades")?.addEventListener("click", () => loadCourseGrades());
  el("btn-upsert-grade")?.addEventListener("click", () => upsertGrade());
  el("filter-career")?.addEventListener("change", () => fillParallels());
  el("filter-term")?.addEventListener("change", () => fillParallels());
  el("filter-parallel")?.addEventListener("change", () => {
    onParallelChange().catch(() => toast("No se pudo cargar el curso", "bad"));
  });

  await loadContext();
})();
