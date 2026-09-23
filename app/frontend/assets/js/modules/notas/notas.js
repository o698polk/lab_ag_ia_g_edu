/* global SigaApi, SigaAuth, SigaToast, SigaTable */
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

  const el = (id) => document.getElementById(id);

  function courseLabel(course) {
    if (!course) return "Curso";
    return SigaTable.formatRef(
      course.id,
      course.course_name || course.parallel_code,
      course.subject_name
    );
  }

  function selectedCourse() {
    const id = Number(el("filter-course")?.value || 0);
    const list = state.context?.courses || [];
    return list.find((c) => Number(c.id) === id) || null;
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
      (course.term_name || "—") +
      (course.teacher_name ? " · Docente: " + course.teacher_name : "");
  }

  function parseScore(value) {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function formatScore(value) {
    if (value == null || value === "") return "—";
    return Number(value).toFixed(2);
  }

  function previewStatus(first, second, recovery) {
    if (first == null || second == null) {
      return { average: null, recoveryAllowed: false, status: "IN_PROGRESS" };
    }
    const average = Math.round(((first + second) / 2) * 100) / 100;
    if (average >= 7) {
      return { average, recoveryAllowed: false, status: "APROBADO" };
    }
    if (recovery == null) {
      return { average, recoveryAllowed: true, status: "SUPLETORIO PENDIENTE" };
    }
    if (recovery >= 7) {
      return { average, recoveryAllowed: true, status: "APROBADO POR RECUPERACIÓN" };
    }
    return { average, recoveryAllowed: true, status: "REPROBADO" };
  }

  function gradeInput(studentId, field, value, disabled) {
    return (
      "<input class='form-control form-control-sm grade-input' data-student='" +
      studentId +
      "' data-field='" +
      field +
      "' type='number' min='0' max='10' step='0.01' value='" +
      (value == null ? "" : value) +
      "'" +
      (disabled ? " disabled" : "") +
      " />"
    );
  }

  function syncRow(tr) {
    const first = parseScore(tr.querySelector("[data-field='first_partial']")?.value);
    const second = parseScore(tr.querySelector("[data-field='second_partial']")?.value);
    const recInput = tr.querySelector("[data-field='recovery_grade']");
    const recovery = recInput && !recInput.disabled ? parseScore(recInput.value) : null;
    const preview = previewStatus(first, second, recovery);
    const avgCell = tr.querySelector("[data-avg]");
    const statusCell = tr.querySelector("[data-status]");
    if (avgCell) avgCell.textContent = formatScore(preview.average);
    if (recInput) {
      recInput.disabled = !preview.recoveryAllowed;
      if (!preview.recoveryAllowed) recInput.value = "";
    }
    if (statusCell) statusCell.textContent = preview.status;
  }

  async function loadCourses() {
    const { ok, data } = await api("GET", "/courses");
    const courses = ok && Array.isArray(data) ? data : [];
    state.context = state.context || {};
    state.context.courses = courses;
    fillSelect(el("filter-course"), courses, courseLabel, (c) => c.id, "Seleccionar curso…");
    if (!ok) toast(formatError(data), "bad");
  }

  function paintFinals(rows) {
    const tbody = el("gradebook-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (!rows.length) {
      if (empty) {
        empty.textContent = "No hay estudiantes matriculados en este curso.";
        empty.classList.remove("d-none");
      }
      if (el("btn-save-gradebook")) el("btn-save-gradebook").disabled = true;
      return;
    }
    if (empty) empty.classList.add("d-none");
    rows.forEach((row, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        (idx + 1) +
        "</td><td>" +
        SigaTable.escapeHtml(row.name) +
        "</td><td>" +
        gradeInput(row.student_id, "first_partial", row.first_partial, false) +
        "</td><td>" +
        gradeInput(row.student_id, "second_partial", row.second_partial, false) +
        "</td><td data-avg>" +
        formatScore(row.final_average) +
        "</td><td>" +
        gradeInput(row.student_id, "recovery_grade", row.recovery_grade, !row.recovery_allowed) +
        "</td><td data-status>" +
        SigaTable.escapeHtml(row.academic_status || "IN_PROGRESS") +
        "</td><td></td>";
      tbody.appendChild(tr);
      syncRow(tr);
    });
    tbody.querySelectorAll(".grade-input").forEach((input) => {
      input.addEventListener("input", () => syncRow(input.closest("tr")));
    });
    if (el("btn-save-gradebook")) el("btn-save-gradebook").disabled = false;
  }

  async function loadFinals() {
    const course = selectedCourse();
    paintCourseMeta(course);
    if (!course) {
      paintFinals([]);
      return;
    }
    const { ok, data } = await api("GET", "/courses/" + course.id + "/final-grades");
    if (!ok) {
      toast(formatError(data), "bad");
      paintFinals([]);
      return;
    }
    paintFinals(data.students || []);
  }

  async function saveFinals() {
    const course = selectedCourse();
    if (!course) {
      toast("Seleccione un curso.", "bad");
      return;
    }
    const items = [...document.querySelectorAll("#gradebook-tbody tr")]
      .map((tr) => {
        const first = tr.querySelector("[data-field='first_partial']");
        const studentId = Number(first?.getAttribute("data-student") || 0);
        const rec = tr.querySelector("[data-field='recovery_grade']");
        return {
          student_id: studentId,
          first_partial: parseScore(first?.value),
          second_partial: parseScore(tr.querySelector("[data-field='second_partial']")?.value),
          recovery_grade: rec && !rec.disabled ? parseScore(rec.value) : null,
        };
      })
      .filter((item) => item.student_id && (item.first_partial != null || item.second_partial != null));
    if (!items.length) {
      toast("Ingrese al menos un parcial.", "bad");
      return;
    }
    const { ok, data } = await api("PUT", "/courses/" + course.id + "/final-grades", { items });
    toast(ok ? "Calificaciones guardadas." : formatError(data), ok ? "ok" : "bad");
    if (ok) paintFinals(data.students || []);
  }

  function paintStudentTables(rows) {
    fillTbody(
      el("student-subjects-tbody"),
      rows.map((r) => ({
        subject: r.subject_name || "—",
        teacher: r.teacher_name || "—",
        term: r.term_name || "—",
      })),
      ["subject", "teacher", "term"]
    );
    fillTbody(
      el("student-grades-tbody"),
      rows.map((r) => ({
        subject: r.subject_name || "—",
        first_partial: formatScore(r.first_partial),
        second_partial: formatScore(r.second_partial),
        final_average: formatScore(r.final_average),
        recovery: formatScore(r.recovery_grade),
        status: r.academic_status || "IN_PROGRESS",
      })),
      ["subject", "first_partial", "second_partial", "final_average", "recovery", "status"]
    );
    fillTbody(
      el("student-attendance-tbody"),
      rows.map((r) => ({
        subject: r.subject_name || "—",
        attendance: (r.attendance_pct == null ? 0 : r.attendance_pct) + "%",
      })),
      ["subject", "attendance"]
    );
  }

  async function loadStudentAcademic() {
    const { ok, data } = await api("GET", "/me/academic");
    if (!ok) {
      toast(formatError(data), "bad");
      paintStudentTables([]);
      return;
    }
    paintStudentTables(Array.isArray(data) ? data : []);
  }

  el("filter-course")?.addEventListener("change", () => loadFinals());
  el("btn-save-gradebook")?.addEventListener("click", () => saveFinals());
  el("btn-load-gradebook")?.addEventListener("click", () => loadFinals());

  if (canTeach) {
    await loadCourses();
    await loadFinals();
  } else {
    await loadStudentAcademic();
  }
})();
