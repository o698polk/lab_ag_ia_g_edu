// Ref: K-022 | Grades page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError, state } = SigaApi;
  const { $, toast, renderTable, fillSelect } = SigaUi;

  state.context = state.context || { courses: [], students: [], evaluations: [], subjects: [] };

  function subjectName(subjectId) {
    const s = state.context.subjects.find((x) => x.id === subjectId);
    return s ? `${s.code} — ${s.name}` : `Materia ${subjectId}`;
  }
  function courseLabel(c) {
    return `Curso ${c.id} · ${subjectName(c.subject_id)} · ${c.parallel_code}`;
  }
  function studentLabel(s) {
    return `${s.student_code || "EST"} (id ${s.id})`;
  }
  function evaluationLabel(e) {
    return `${e.name} (id ${e.id})`;
  }

  async function loadEvaluationsForCourse(courseId) {
    if (!courseId) {
      state.context.evaluations = [];
      fillSelect($("grade-eval-id"), [], evaluationLabel, (e) => e.id);
      return;
    }
    const { ok, data } = await api("GET", `/courses/${courseId}/evaluations`);
    state.context.evaluations = ok && Array.isArray(data) ? data : [];
    fillSelect($("grade-eval-id"), state.context.evaluations, evaluationLabel, (e) => e.id);
  }

  async function loadContext() {
    const [courses, students, subjects] = await Promise.all([
      api("GET", "/courses"),
      api("GET", "/students"),
      api("GET", "/subjects"),
    ]);
    state.context.courses = courses.ok && Array.isArray(courses.data) ? courses.data : [];
    state.context.students = students.ok && Array.isArray(students.data) ? students.data : [];
    state.context.subjects = subjects.ok && Array.isArray(subjects.data) ? subjects.data : [];
    fillSelect($("grades-course-id"), state.context.courses, courseLabel, (c) => c.id);
    fillSelect($("grade-student-id"), state.context.students, studentLabel, (s) => s.id);
    const courseId = Number($("grades-course-id")?.value || state.context.courses[0]?.id || 0);
    if (courseId) await loadEvaluationsForCourse(courseId);
  }

  async function loadMyGrades() {
    const { ok, data } = await api("GET", "/me/grades");
    if (!ok) {
      $("grades-table").innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    renderTable($("grades-table"), Array.isArray(data) ? data : [data]);
    toast("Notas cargadas.", "ok");
  }

  async function loadMyKardex() {
    const { ok, data } = await api("GET", "/me/kardex");
    if (!ok) {
      $("grades-table").innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    renderTable($("grades-table"), Array.isArray(data) ? data : [data]);
  }

  async function loadCourseGrades() {
    const courseId = Number($("grades-course-id").value);
    if (!courseId) {
      toast("Selecciona un curso.", "bad");
      return;
    }
    const { ok, data } = await api("GET", `/courses/${courseId}/grades`);
    if (!ok) {
      $("grades-table").innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    renderTable($("grades-table"), Array.isArray(data) ? data : [data]);
  }

  async function upsertGrade() {
    const evaluationId = Number($("grade-eval-id").value);
    const studentId = Number($("grade-student-id").value);
    if (!evaluationId || !studentId) {
      toast("Selecciona evaluación y estudiante.", "bad");
      return;
    }
    const body = {
      evaluation_id: evaluationId,
      student_id: studentId,
      score: Number($("grade-score").value),
      comment: $("grade-comment").value || null,
    };
    const { ok, data } = await api("PUT", "/grades", body);
    toast(ok ? "Nota guardada." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadCourseGrades();
  }

  $("btn-my-grades")?.addEventListener("click", () => loadMyGrades());
  $("btn-my-kardex")?.addEventListener("click", () => loadMyKardex());
  $("btn-course-grades")?.addEventListener("click", () => loadCourseGrades());
  $("btn-upsert-grade")?.addEventListener("click", () => upsertGrade());
  $("grades-course-id")?.addEventListener("change", () => {
    loadEvaluationsForCourse(Number($("grades-course-id").value));
  });
  await loadContext();
})();
