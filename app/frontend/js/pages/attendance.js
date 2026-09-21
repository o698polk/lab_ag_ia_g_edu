// Ref: K-022 | Attendance page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError, state } = SigaApi;
  const { $, toast, fillSelect } = SigaUi;

  state.context = state.context || { courses: [], students: [], subjects: [] };

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

  async function loadContext() {
    const [courses, students, subjects] = await Promise.all([
      api("GET", "/courses"),
      api("GET", "/students"),
      api("GET", "/subjects"),
    ]);
    state.context.courses = courses.ok && Array.isArray(courses.data) ? courses.data : [];
    state.context.students = students.ok && Array.isArray(students.data) ? students.data : [];
    state.context.subjects = subjects.ok && Array.isArray(subjects.data) ? subjects.data : [];
    fillSelect($("att-course-id"), state.context.courses, courseLabel, (c) => c.id);
    fillSelect($("pct-course-id"), state.context.courses, courseLabel, (c) => c.id);
    fillSelect($("att-student-id"), state.context.students, studentLabel, (s) => s.id);
    fillSelect($("pct-student-id"), state.context.students, studentLabel, (s) => s.id);
  }

  async function createSession() {
    const courseId = Number($("att-course-id").value);
    if (!courseId) {
      toast("Selecciona un curso.", "bad");
      return;
    }
    const body = {
      course_id: courseId,
      session_date: $("att-date").value,
      topic: $("att-topic").value || null,
    };
    const { ok, data } = await api("POST", "/attendance/sessions", body);
    if (ok && data?.id) $("att-session-id").value = data.id;
    toast(ok ? "Sesión creada." : formatError(data), ok ? "ok" : "bad");
  }

  async function markAttendance() {
    const studentId = Number($("att-student-id").value);
    const sessionId = Number($("att-session-id").value);
    if (!studentId || !sessionId) {
      toast("Indica sesión y estudiante.", "bad");
      return;
    }
    const body = {
      session_id: sessionId,
      student_id: studentId,
      status: $("att-status").value,
    };
    const { ok, data } = await api("PUT", "/attendance/records", body);
    toast(ok ? "Asistencia guardada." : formatError(data), ok ? "ok" : "bad");
  }

  async function attendancePercent() {
    const courseId = Number($("pct-course-id").value);
    const studentId = Number($("pct-student-id").value);
    if (!courseId || !studentId) {
      toast("Selecciona curso y estudiante.", "bad");
      return;
    }
    const { ok, data } = await api(
      "GET",
      `/attendance/courses/${courseId}/students/${studentId}/percent`
    );
    if (!ok) toast(formatError(data), "bad");
    else toast(`Asistencia: ${data.percentage}%`, "ok");
  }

  const dateEl = $("att-date");
  if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);

  $("btn-create-session")?.addEventListener("click", () => createSession());
  $("btn-mark-att")?.addEventListener("click", () => markAttendance());
  $("btn-att-pct")?.addEventListener("click", () => attendancePercent());
  await loadContext();
})();
