/* global SigaApi, SigaAuth, SigaToast, SigaTable, SigaModal, SigaAdminTable */
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

  const GRADE_COLS = ["id", "evaluation", "student", "score", "comment", "graded_at"];
  const KARDEX_COLS = ["id", "term", "subject", "final_grade", "academic_status", "credits"];

  const el = (id) => document.getElementById(id);
  const gradesTable = SigaAdminTable.bind({
    tbody: el("grades-tbody"),
    columns: GRADE_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-grades"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de nota",
          body: SigaModal.viewDl(GRADE_COLS.map((k) => [k, row[k]])),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") {
        if (el("grade-eval-id")) el("grade-eval-id").value = String(row.evaluation_id || "");
        if (el("grade-student-id")) el("grade-student-id").value = String(row.student_id || "");
        if (el("grade-score")) el("grade-score").value = row.score ?? "";
        if (el("grade-comment")) el("grade-comment").value = row.comment || "";
        openGradeForm();
      }
    },
  });
  const kardexTable = SigaAdminTable.bind({
    tbody: el("kardex-tbody"),
    columns: KARDEX_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-kardex"),
    statusKeys: ["academic_status"],
    actions: () => SigaAdminTable.actionButtons(["view"]),
    onAction: (act, row) => {
      if (act !== "view" || !row) return;
      SigaModal.open({
        title: "Consulta de kardex",
        body: SigaModal.viewDl(KARDEX_COLS.map((k) => [k, row[k]])),
        footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      });
    },
  });

  function openGradeForm() {
    const wrap = el("grade-form-wrap");
    if (!wrap) return;
    SigaModal.openParked({
      title: "Registrar nota",
      node: wrap,
      footer:
        '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
        '<button type="button" class="btn btn-siga" id="btn-modal-save-grade">Guardar</button>',
      wide: true,
    });
    document.getElementById("btn-modal-save-grade")?.addEventListener("click", () => upsertGrade());
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

  function findStudent(id) {
    return (
      state.context.courseStudents.find((s) => Number(s.id) === Number(id) || Number(s.student_id) === Number(id)) ||
      state.context.students.find((s) => Number(s.id) === Number(id)) ||
      null
    );
  }

  function mapGradeRow(row) {
    const ev = state.context.evaluations.find((e) => Number(e.id) === Number(row.evaluation_id));
    const st = findStudent(row.student_id);
    return {
      ...row,
      evaluation: ev ? evaluationLabel(ev) : SigaTable.formatRef(row.evaluation_id, "Evaluación"),
      student: st ? studentLabel(st) : SigaTable.formatRef(row.student_id, "Estudiante"),
      graded_at: row.graded_at ? String(row.graded_at).replace("T", " ").slice(0, 16) : "",
    };
  }

  function mapKardexRow(row) {
    return {
      ...row,
      term: termName(row.term_id),
      subject: subjectName(row.subject_id),
    };
  }

  function evaluationLabel(e) {
    return SigaTable.formatRef(e.id, `${e.name} (${e.weight_percent}%)`);
  }

  function parallelLabel(c) {
    const sub = state.context.subjects.find((x) => x.id === c.subject_id);
    const title = sub ? (sub.name || sub.code) : "Curso";
    const par = c.parallel_code ? " · " + c.parallel_code : "";
    return SigaTable.formatRef(c.id, title + par);
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
    gradesTable.setRows((Array.isArray(rows) ? rows : []).map(mapGradeRow));
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
      (t) => SigaTable.formatRef(t.id, (t.code || "") + " — " + (t.name || "") + (t.is_current ? " (actual)" : "")),
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
    fillSelect(el("filter-eval"), state.context.evaluations, evaluationLabel, (e) => e.id);
    fillSelect(el("grade-student-id"), state.context.courseStudents, studentLabel, (s) => s.id);
    fillSelect(el("kx-student"), state.context.courseStudents, studentLabel, (s) => s.id);
    setCourseActionsEnabled(true);
    if (state.context.evaluations.length) await loadGradebook();
  }

  async function onParallelChange() {
    const courseId = Number(el("filter-parallel")?.value || 0);
    updateCascadePath();
    await loadEvaluationsAndStudents(courseId);
  }

  async function loadContext() {
    if (!canTeach) return;

    const [careers, terms, courses, subjects, students, curricula, enrollments, users] = await Promise.all([
      api("GET", "/careers"),
      api("GET", "/terms"),
      api("GET", "/courses"),
      api("GET", "/subjects"),
      api("GET", "/students"),
      api("GET", "/curricula"),
      api("GET", "/enrollments"),
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
    state.context.enrollments =
      enrollments.ok && Array.isArray(enrollments.data) ? enrollments.data : [];

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
    fillSelect(el("kx-term"), state.context.terms, (t) => SigaTable.formatRef(t.id, (t.code || "") + " — " + (t.name || "")), (t) => t.id);
    fillSelect(el("kx-subject"), state.context.subjects, (s) => SigaTable.formatRef(s.id, (s.code || "") + " — " + (s.name || "")), (s) => s.id);

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
      kardexTable.setRows([]);
      return;
    }
    showKardexPanel();
    kardexTable.setRows((Array.isArray(data) ? data : [data]).map(mapKardexRow));
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

  function paintGradebook(data) {
    const tbody = el("gradebook-tbody");
    if (!tbody) return;
    const students = (data && data.students) || [];
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (!students.length) {
      tbody.innerHTML = "";
      if (empty) empty.classList.remove("d-none");
      if (el("btn-save-gradebook")) el("btn-save-gradebook").disabled = true;
      return;
    }
    if (empty) empty.classList.add("d-none");
    tbody.innerHTML = students
      .map((s) => {
        const score = s.score == null ? "" : s.score;
        return (
          "<tr><td>" +
          SigaModal.escapeHtml(String(s.student_id || s.id || "")) +
          "</td><td>" +
          SigaModal.escapeHtml(s.name || s.student_code || "") +
          "</td><td>" +
          SigaModal.escapeHtml((s.attendance_pct ?? 0) + "%") +
          '</td><td><input type="number" class="form-control grade-input" min="0" max="100" step="0.01" data-student="' +
          s.student_id +
          '" value="' +
          score +
          '" /></td></tr>'
        );
      })
      .join("");
    if (el("btn-save-gradebook")) el("btn-save-gradebook").disabled = false;
  }

  async function loadGradebook() {
    const courseId = Number(el("filter-parallel")?.value || 0);
    const evaluationId = Number(el("filter-eval")?.value || el("grade-eval-id")?.value || 0);
    if (!courseId) {
      paintGradebook({ students: [] });
      return;
    }
    if (el("grade-eval-id") && evaluationId) el("grade-eval-id").value = String(evaluationId);
    const qs = evaluationId ? "?evaluation_id=" + evaluationId : "";
    const { ok, data } = await api("GET", "/courses/" + courseId + "/gradebook" + qs);
    if (!ok) {
      toast(formatError(data), "bad");
      paintGradebook({ students: [] });
      return;
    }
    paintGradebook(data);
  }

  async function saveGradebook() {
    const evaluationId = Number(el("filter-eval")?.value || el("grade-eval-id")?.value || 0);
    if (!evaluationId) {
      toast("Seleccione un componente evaluativo.", "bad");
      return;
    }
    const inputs = [...document.querySelectorAll("#gradebook-tbody .grade-input")];
    let okAll = true;
    for (const input of inputs) {
      if (input.value === "") continue;
      const score = Number(input.value);
      if (Number.isNaN(score) || score < 0 || score > 100) {
        toast("La calificación debe estar entre 0 y 100.", "bad");
        okAll = false;
        break;
      }
      const { ok, data } = await api("PUT", "/grades", {
        evaluation_id: evaluationId,
        student_id: Number(input.getAttribute("data-student")),
        score,
      });
      if (!ok) {
        toast(formatError(data), "bad");
        okAll = false;
        break;
      }
    }
    if (okAll) {
      toast("Calificaciones guardadas.", "ok");
      await loadCourseGrades();
    }
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

  async function createEvaluation() {
    const courseId = Number(el("filter-parallel")?.value || 0);
    const name = (el("eval-name")?.value || "").trim();
    if (!courseId || !name) {
      toast("Selecciona paralelo y nombre de evaluación.", "bad");
      return;
    }
    const { ok, data } = await api("POST", "/evaluations", {
      course_id: courseId,
      name,
      weight_percent: Number(el("eval-weight")?.value || 30),
      due_date: el("eval-due")?.value || null,
    });
    toast(ok ? "Evaluación creada." : formatError(data), ok ? "ok" : "bad");
    if (ok) await onParallelChange();
  }

  async function upsertKardex() {
    const studentId = Number(el("kx-student")?.value || 0);
    const termId = Number(el("kx-term")?.value || el("filter-term")?.value || 0);
    const subjectId = Number(el("kx-subject")?.value || 0);
    if (!studentId || !termId || !subjectId) {
      toast("Indica estudiante, periodo y asignatura.", "bad");
      return;
    }
    const { ok, data } = await api("PUT", "/kardex", {
      student_id: studentId,
      term_id: termId,
      subject_id: subjectId,
      course_id: Number(el("filter-parallel")?.value || 0) || null,
      final_grade: el("kx-grade")?.value === "" ? null : Number(el("kx-grade").value),
      academic_status: "IN_PROGRESS",
      credits: Number(el("kx-credits")?.value || 0),
    });
    toast(ok ? "Kardex actualizado." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadMyKardex();
  }

  el("btn-new-record")?.addEventListener("click", () => openGradeForm());
  el("btn-create-eval")?.addEventListener("click", () => createEvaluation());
  el("btn-upsert-kardex")?.addEventListener("click", () => upsertKardex());
  el("btn-my-grades")?.addEventListener("click", () => loadMyGrades());
  el("btn-my-kardex")?.addEventListener("click", () => loadMyKardex());
  el("btn-course-grades")?.addEventListener("click", () => loadCourseGrades());
  el("btn-upsert-grade")?.addEventListener("click", () => upsertGrade());
  el("filter-career")?.addEventListener("change", () => fillParallels());
  el("filter-term")?.addEventListener("change", () => fillParallels());
  el("filter-parallel")?.addEventListener("change", () => {
    onParallelChange().catch(() => toast("No se pudo cargar el curso", "bad"));
  });
  el("filter-eval")?.addEventListener("change", () => {
    if (el("grade-eval-id")) el("grade-eval-id").value = el("filter-eval").value;
    loadGradebook();
  });
  el("btn-load-gradebook")?.addEventListener("click", () => loadGradebook());
  el("btn-save-gradebook")?.addEventListener("click", () => saveGradebook());

  await loadContext();
})();
