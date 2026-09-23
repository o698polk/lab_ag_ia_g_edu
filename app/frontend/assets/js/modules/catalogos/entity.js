/* global SigaApi, SigaAuth, SigaToast, SigaTable, SigaModal, SigaAdminTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const ctx = {
    subjects: [],
    terms: [],
    teachers: [],
    students: [],
    users: [],
    courses: [],
    careers: [],
    classrooms: [],
  };

  function byId(list, id) {
    if (id == null || id === "") return null;
    return (list || []).find((item) => Number(item.id) === Number(id)) || null;
  }

  function visibleName(name, code) {
    const title = String(name || "").trim();
    const extra = String(code || "").trim();
    if (title && extra && extra !== title) return title + " — " + extra;
    return title || extra || "—";
  }

  function withId(text) {
    return String(text || "").trim() || "—";
  }

  function userName(user) {
    if (!user) return "";
    return (
      [user.first_name, user.last_name].filter(Boolean).join(" ").trim() ||
      user.full_name ||
      user.username ||
      ""
    );
  }

  function labelUser(id) {
    const user = byId(ctx.users, id);
    if (!user) return id == null || id === "" ? "—" : "Usuario";
    return visibleName(userName(user) || user.username, user.cedula);
  }

  function labelCareer(id) {
    const career = byId(ctx.careers, id);
    if (!career) return id == null || id === "" ? "—" : "Carrera";
    return visibleName(career.name, career.code);
  }

  function labelSubject(id) {
    const subject = byId(ctx.subjects, id);
    if (!subject) return id == null || id === "" ? "—" : "Asignatura";
    return visibleName(subject.name, subject.code);
  }

  function labelTerm(id) {
    const term = byId(ctx.terms, id);
    if (!term) return id == null || id === "" ? "—" : "Periodo";
    return visibleName(term.name, term.code);
  }

  function labelTeacher(id) {
    const teacher = byId(ctx.teachers, id);
    if (!teacher) return id == null || id === "" ? "—" : "Docente";
    return visibleName(userName(byId(ctx.users, teacher.user_id)), teacher.teacher_code);
  }

  function labelStudent(id) {
    const student = byId(ctx.students, id);
    if (!student) return id == null || id === "" ? "—" : "Estudiante";
    return visibleName(userName(byId(ctx.users, student.user_id)), student.student_code);
  }

  function labelCourse(id) {
    const course = byId(ctx.courses, id);
    if (!course) return id == null || id === "" ? "—" : "Curso";
    const subject = byId(ctx.subjects, course.subject_id);
    return visibleName(
      course.course_name || course.parallel_code,
      course.subject_name || (subject && subject.name)
    );
  }

  function labelClassroom(id) {
    const room = byId(ctx.classrooms, id);
    if (!room) return id == null || id === "" ? "—" : "Aula";
    return visibleName(room.name, room.code);
  }

  function labelSubjects(ids) {
    if (!ids || !ids.length) return "—";
    return ids.map((sid) => labelSubject(sid)).join("; ");
  }

  const LOOKUPS = {
    user_id: { path: "/users", label: (u) => visibleName(userName(u) || u.username, u.cedula) },
    career_id: { path: "/careers", label: (c) => visibleName(c.name, c.code) },
    subject_id: { path: "/subjects", label: (s) => visibleName(s.name, s.code) },
    term_id: { path: "/terms", label: (t) => visibleName(t.name, t.code) },
    student_id: { path: "/students", label: (s) => labelStudent(s.id) },
    course_id: { path: "/courses", label: (c) => labelCourse(c.id) },
    teacher_id: { path: "/teachers", label: (t) => labelTeacher(t.id) },
    classroom_id: { path: "/classrooms", label: (c) => visibleName(c.name, c.code) },
  };

  const DISPLAY_NEEDED = {
    students: ["user_id", "career_id"],
    teachers: ["user_id"],
    courses: ["subject_id", "term_id", "teacher_id", "user_id"],
    enrollments: ["student_id", "course_id", "term_id", "subject_id", "user_id"],
    curricula: ["career_id", "subject_id"],
    schedules: ["course_id", "teacher_id", "classroom_id", "term_id", "subject_id", "user_id"],
    assignments: ["teacher_id", "course_id", "term_id", "subject_id", "user_id"],
  };

  const DEFS = {
    careers: {
      path: "/careers",
      cols: ["id", "code", "name", "modality", "duration_semesters", "status"],
      statusPath: (id) => "/careers/" + id + "/status",
      create: (f) => ({
        code: f.code,
        name: f.name,
        modality: f.modality || "PRESENCIAL",
        duration_semesters: Number(f.duration_semesters || 10),
      }),
    },
    subjects: {
      path: "/subjects",
      cols: ["id", "code", "name", "credits", "hours", "type", "status"],
      statusPath: (id) => "/subjects/" + id + "/status",
      create: (f) => ({
        code: f.code,
        name: f.name,
        credits: f.credits === "" ? "0" : String(f.credits),
        hours: Number(f.hours || 0),
        type: f.type || "OBLIGATORIA",
      }),
    },
    terms: {
      path: "/terms",
      cols: ["id", "code", "name", "start_date", "end_date", "status", "is_current"],
      statusPath: (id) => "/terms/" + id + "/status",
      statuses: ["PLANNED", "ACTIVE", "CLOSED", "CANCELLED"],
      create: (f) => ({
        code: f.code,
        name: f.name,
        start_date: f.start_date,
        end_date: f.end_date,
        status: f.status || "PLANNED",
        is_current: false,
      }),
    },
    students: {
      path: "/students",
      cols: ["id", "user", "student_code", "career", "level", "status"],
      statusPath: (id) => "/students/" + id + "/status",
      create: (f) => ({
        user_id: Number(f.user_id),
        student_code: f.student_code,
        career_id: f.career_id ? Number(f.career_id) : null,
        level: f.level || null,
      }),
      mapRow: (row) => ({
        ...row,
        user: labelUser(row.user_id),
        career: labelCareer(row.career_id),
      }),
    },
    teachers: {
      path: "/teachers",
      cols: ["id", "user", "teacher_code", "specialty", "status"],
      statusPath: (id) => "/teachers/" + id + "/status",
      create: (f) => ({
        user_id: Number(f.user_id),
        teacher_code: f.teacher_code,
        specialty: f.specialty || null,
      }),
      mapRow: (row) => ({
        ...row,
        user: labelUser(row.user_id),
      }),
    },
    courses: {
      path: "/courses",
      cols: ["id", "code", "course", "teacher", "term", "hours", "status"],
      statusPath: (id) => "/courses/" + id + "/status",
      updatePath: (id) => "/courses/" + id,
      create: (f) => ({
        subject_id: Number(f.subject_id),
        term_id: Number(f.term_id),
        parallel_code: f.parallel_code || "A",
        capacity: Number(f.capacity || 40),
        hours_theory: Number(f.hours_theory || 0),
        hours_practical: Number(f.hours_practical || 0),
        hours_autonomous: Number(f.hours_autonomous || 0),
        teacher_id: f.teacher_id ? Number(f.teacher_id) : undefined,
      }),
      update: (f) => ({
        parallel_code: f.parallel_code || "A",
        capacity: Number(f.capacity || 40),
        hours_theory: Number(f.hours_theory || 0),
        hours_practical: Number(f.hours_practical || 0),
        hours_autonomous: Number(f.hours_autonomous || 0),
        teacher_id: f.teacher_id ? Number(f.teacher_id) : null,
        status: f.status || undefined,
      }),
      mapRow: (row) => {
        const hours = (row.hours_theory || 0) + (row.hours_practical || 0) + (row.hours_autonomous || 0);
        return {
          ...row,
          code: row.subject_code || row.parallel_code || "",
          course: visibleName(row.course_name || row.parallel_code, row.subject_name),
          teacher: row.teacher_name || labelTeacher(row.teacher_id),
          term: row.term_name || labelTerm(row.term_id),
          hours: hours + " h",
        };
      },
    },
    enrollments: {
      path: "/enrollments",
      cols: ["id", "student", "course", "term", "enrolled_at", "status"],
      delete: (id) => api("POST", "/enrollments/" + id + "/cancel"),
      create: (f) => ({
        student_id: Number(f.student_id),
        course_id: Number(f.course_id),
        term_id: Number(f.term_id),
      }),
      mapRow: (row) => ({
        ...row,
        student: row.student_name || labelStudent(row.student_id),
        course: visibleName(row.course_name, row.subject_name) || labelCourse(row.course_id),
        term: row.term_name || labelTerm(row.term_id),
        enrolled_at: row.enrolled_at ? String(row.enrolled_at).replace("T", " ").slice(0, 16) : "",
      }),
    },
    curricula: {
      path: "/curricula",
      cols: ["id", "career", "version", "status", "subjects"],
      statusPath: (id) => "/curricula/" + id + "/status",
      create: (f) => ({
        career_id: Number(f.career_id),
        version: f.version,
      }),
      mapRow: (row) => ({
        ...row,
        career: labelCareer(row.career_id),
        subjects: labelSubjects(row.subject_ids),
      }),
    },
    classrooms: {
      path: "/classrooms",
      cols: ["id", "code", "name", "capacity"],
      create: (f) => ({
        code: f.code,
        name: f.name,
        capacity: Number(f.capacity || 40),
      }),
    },
    schedules: {
      path: "/schedules",
      cols: ["id", "course", "teacher", "classroom", "term", "day_of_week", "start_time", "end_time"],
      delete: (id) => api("DELETE", "/schedules/" + Number(id)),
      create: (f) => ({
        course_id: Number(f.course_id),
        teacher_id: Number(f.teacher_id),
        classroom_id: Number(f.classroom_id),
        term_id: Number(f.term_id),
        day_of_week: f.day_of_week || "MON",
        start_time: f.start_time,
        end_time: f.end_time,
      }),
      mapRow: (row) => {
        const days = {
          MON: "Lunes",
          TUE: "Martes",
          WED: "Miércoles",
          THU: "Jueves",
          FRI: "Viernes",
          SAT: "Sábado",
          SUN: "Domingo",
        };
        return {
          ...row,
          course: labelCourse(row.course_id),
          teacher: labelTeacher(row.teacher_id),
          classroom: labelClassroom(row.classroom_id),
          term: labelTerm(row.term_id),
          day_of_week: days[row.day_of_week] || row.day_of_week,
          start_time: String(row.start_time || "").slice(0, 5),
          end_time: String(row.end_time || "").slice(0, 5),
        };
      },
    },
    assignments: {
      path: "/teaching-assignments",
      cols: ["id", "teacher", "course", "term", "status"],
      statusPath: (id) => "/teaching-assignments/" + id + "/status",
      create: (f) => ({
        teacher_id: Number(f.teacher_id),
        course_id: Number(f.course_id),
        term_id: Number(f.term_id),
      }),
      mapRow: (row) => ({
        ...row,
        teacher: labelTeacher(row.teacher_id),
        course: labelCourse(row.course_id),
        term: labelTerm(row.term_id),
      }),
    },
  };

  const key = document.body.getAttribute("data-entity");
  const def = DEFS[key];
  if (!def) return;

  const el = (id) => document.getElementById(id);
  const labels = SigaTable.COL_LABEL;
  const extraActs = key === "courses" ? ["view", "edit", "roster", "del"] : ["view", "edit", "del"];
  const table = SigaAdminTable.bind({
    tbody: el("catalog-tbody"),
    columns: def.cols,
    searchInput: el("admin-search"),
    filterInput: el("admin-filter"),
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(extraActs),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") openView(row);
      if (act === "edit") openEdit(row);
      if (act === "del") openDelete(row);
      if (act === "roster") openRoster(row);
    },
  });

  function readForm() {
    const out = {};
    document.querySelectorAll("#catalog-create-form [data-field]").forEach((input) => {
      out[input.getAttribute("data-field")] = (input.value || "").trim();
    });
    return out;
  }

  function setForm(values) {
    document.querySelectorAll("#catalog-create-form [data-field]").forEach((input) => {
      const field = input.getAttribute("data-field");
      if (values[field] == null || values[field] === "") return;
      input.value = String(values[field]);
    });
  }

  function viewBody(row) {
    const keys = (def.cols || Object.keys(row)).filter((k) => k !== "_raw");
    const rows = keys
      .map((k) => {
        const lab = labels[k] || k;
        const val = Array.isArray(row[k]) ? row[k].join(", ") : row[k];
        return "<dt>" + SigaModal.escapeHtml(lab) + "</dt><dd>" + SigaModal.escapeHtml(val ?? "—") + "</dd>";
      })
      .join("");
    return "<dl class='view-dl'>" + rows + "</dl>";
  }

  function openView(row) {
    SigaModal.open({
      title: "Consulta de registro",
      body: viewBody(row),
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
    });
  }

  async function openRoster(row) {
    const { ok, data } = await api("GET", "/courses/" + row.id + "/roster");
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    const list = Array.isArray(data) ? data : [];
    const body = list.length
      ? "<table class='table table-sm'><thead><tr><th>Nº</th><th>Código</th><th>Estudiante</th><th>Estado</th></tr></thead><tbody>" +
        list
          .map(
            (s, i) =>
              "<tr><td>" +
              (i + 1) +
              "</td><td>" +
              SigaModal.escapeHtml(s.student_code) +
              "</td><td>" +
              SigaModal.escapeHtml(s.name) +
              "</td><td>" +
              SigaModal.escapeHtml(s.status) +
              "</td></tr>"
          )
          .join("") +
        "</tbody></table>"
      : "<p class='hint mb-0'>No hay estudiantes matriculados en este curso.</p>";
    SigaModal.open({
      title: "Estudiantes matriculados",
      body,
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      wide: true,
    });
  }

  function openCreate() {
    const form = el("catalog-create-form");
    const wrap = el("catalog-create-wrap") || form;
    if (!form || !wrap) return;
    form.reset();
    form.dataset.mode = "create";
    form.dataset.editId = "";
    const dlg = SigaModal.openParked({
      title: "Nuevo registro",
      node: wrap,
      footer: SigaModal.footerCancelSave("Guardar", "catalog-create-form"),
      wide: true,
    });
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      await createItem(ev);
      if (el("create-out")?.textContent?.includes("creado")) dlg.close();
    };
  }

  function openEdit(row) {
    if (def.update && el("catalog-create-form")) {
      const form = el("catalog-create-form");
      const wrap = el("catalog-create-wrap") || form;
      setForm(row);
      form.dataset.mode = "edit";
      form.dataset.editId = String(row.id);
      const dlg = SigaModal.openParked({
        title: "Editar registro · ID " + row.id,
        node: wrap,
        footer: SigaModal.footerCancelSave("Guardar cambios", "catalog-create-form"),
        wide: true,
      });
      form.onsubmit = async (ev) => {
        ev.preventDefault();
        await updateItem(row.id);
        if (el("create-out")?.textContent?.includes("actualizado")) dlg.close();
      };
      return;
    }
    if (!def.statusPath) {
      SigaModal.open({
        title: "Editar registro",
        body:
          viewBody(row) +
          "<p class='hint mt-3 mb-0'>Este catálogo no admite cambio de campos. Use Nueva alta si necesita otro registro.</p>",
        footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      });
      return;
    }
    const statuses = def.statuses || ["ACTIVE", "INACTIVE"];
    const opts = statuses
      .map(
        (s) =>
          "<option value='" +
          s +
          "'" +
          (String(row.status) === s ? " selected" : "") +
          ">" +
          s +
          "</option>"
      )
      .join("");
    const body =
      "<p class='hint'>ID " +
      row.id +
      " (solo lectura)</p>" +
      viewBody(row) +
      "<form id='siga-modal-form' class='mt-3'>" +
      "<label class='form-label req' for='edit-status'>Estado</label>" +
      "<select id='edit-status' class='form-select' required>" +
      opts +
      "</select></form>";
    const dlg = SigaModal.open({
      title: "Editar registro",
      body,
      footer: SigaModal.footerCancelSave("Guardar cambios"),
    });
    document.getElementById("siga-modal-form")?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const statusVal = document.getElementById("edit-status")?.value;
      if (el("term-id")) el("term-id").value = row.id;
      if (el("term-status")) el("term-status").value = statusVal;
      const { ok, data } = await api("PATCH", def.statusPath(row.id), { status: statusVal });
      toast(ok ? "Registro actualizado correctamente." : formatError(data), ok ? "ok" : "bad");
      if (ok) {
        dlg.close();
        await loadList();
      }
    });
  }

  function openDelete(row) {
    SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
      const recordId = row && (row.id ?? row[def.cols?.[0]]);
      if (def.delete) {
        if (recordId == null || recordId === "") {
          toast("No se pudo identificar el registro a eliminar.", "bad");
          return;
        }
        const { ok, data } = await def.delete(recordId);
        toast(ok ? "Registro eliminado correctamente." : formatError(data), ok ? "ok" : "bad");
        if (ok) await loadList();
        return;
      }
      if (def.statusPath) {
        const { ok, data } = await api("PATCH", def.statusPath(row.id), { status: "INACTIVE" });
        toast(
          ok
            ? "Registro eliminado correctamente."
            : formatError(data) || "No fue posible completar la operación.",
          ok ? "ok" : "bad"
        );
        if (ok) await loadList();
        return;
      }
      toast("Este registro no puede eliminarse porque tiene información asociada.", "bad");
    });
  }

  async function loadLookups() {
    const needed = new Set();
    document.querySelectorAll("[data-field]").forEach((node) => {
      const field = node.getAttribute("data-field");
      if (LOOKUPS[field]) needed.add(field);
    });
    ["term-id", "enroll-cancel-id", "cur-id", "cur-subject-id"].forEach((id) => {
      if (el(id)) {
        if (id === "term-id") needed.add("term_id");
        if (id === "enroll-cancel-id") needed.add("enrollment_id");
        if (id === "cur-id") needed.add("curriculum_id");
        if (id === "cur-subject-id") needed.add("subject_id");
      }
    });
    (DISPLAY_NEEDED[key] || []).forEach((field) => needed.add(field));
    if (key === "courses" || key === "enrollments") {
      needed.add("subject_id");
      needed.add("term_id");
      needed.add("teacher_id");
      needed.add("student_id");
    }
    const loads = {};
    if (needed.has("user_id")) loads.users = api("GET", "/users");
    if (needed.has("career_id")) loads.careers = api("GET", "/careers");
    if (needed.has("subject_id")) loads.subjects = api("GET", "/subjects");
    if (needed.has("term_id")) loads.terms = api("GET", "/terms");
    if (needed.has("student_id")) loads.students = api("GET", "/students");
    if (needed.has("course_id")) loads.courses = api("GET", "/courses");
    if (needed.has("teacher_id")) loads.teachers = api("GET", "/teachers");
    if (needed.has("classroom_id")) loads.classrooms = api("GET", "/classrooms");
    if (needed.has("enrollment_id")) loads.enrollments = api("GET", "/enrollments");
    if (needed.has("curriculum_id")) loads.curricula = api("GET", "/curricula");
    const keys = Object.keys(loads);
    const results = await Promise.all(keys.map((k) => loads[k]));
    const bags = {};
    keys.forEach((k, i) => {
      bags[k] = results[i].ok && Array.isArray(results[i].data) ? results[i].data : [];
    });
    ctx.subjects = bags.subjects || ctx.subjects;
    ctx.terms = bags.terms || ctx.terms;
    ctx.teachers = bags.teachers || ctx.teachers;
    ctx.students = bags.students || ctx.students;
    ctx.users = bags.users || ctx.users;
    ctx.courses = bags.courses || ctx.courses;
    ctx.careers = bags.careers || ctx.careers;
    ctx.classrooms = bags.classrooms || ctx.classrooms;

    const map = {
      user_id: bags.users,
      career_id: bags.careers,
      subject_id: bags.subjects,
      term_id: bags.terms,
      student_id: bags.students,
      course_id: bags.courses,
      teacher_id: bags.teachers,
      classroom_id: bags.classrooms,
    };
    document.querySelectorAll("#catalog-create-form [data-field]").forEach((node) => {
      const field = node.getAttribute("data-field");
      if (node.tagName !== "SELECT" || !LOOKUPS[field]) return;
      fillLookup(node, map[field] || [], LOOKUPS[field].label);
    });
    if (el("term-id") && el("term-id").tagName === "SELECT") {
      fillLookup(el("term-id"), bags.terms || [], LOOKUPS.term_id.label);
    }
    if (el("enroll-cancel-id") && el("enroll-cancel-id").tagName === "SELECT") {
      fillLookup(el("enroll-cancel-id"), bags.enrollments || [], (e) => {
        const st = byId(ctx.students, e.student_id);
        const name = userName(byId(ctx.users, st && st.user_id)) || (st && st.student_code) || "Matrícula";
        return name;
      });
    }
    if (el("cur-id") && el("cur-id").tagName === "SELECT") {
      fillLookup(el("cur-id"), bags.curricula || [], (c) => {
        const career = byId(ctx.careers, c.career_id);
        return visibleName(career && career.name, "v" + (c.version || ""));
      });
    }
    if (el("cur-subject-id") && el("cur-subject-id").tagName === "SELECT") {
      fillLookup(el("cur-subject-id"), bags.subjects || [], LOOKUPS.subject_id.label);
    }
    applyDependentFilters();
  }

  function applyDependentFilters() {
    const termSel = el("f-term_id");
    const courseSel = el("f-course_id");
    if (!termSel || !courseSel || !ctx.courses.length) return;
    const termId = Number(termSel.value || 0);
    const current = courseSel.value;
    const items = termId ? ctx.courses.filter((c) => Number(c.term_id) === termId) : ctx.courses;
    fillLookup(courseSel, items, LOOKUPS.course_id.label);
    if (current && [...courseSel.options].some((o) => o.value === current)) courseSel.value = current;
  }

  function fillLookup(sel, items, labelFn) {
    if (!sel) return;
    if (SigaTable.fillSelect) {
      SigaTable.fillSelect(sel, items || [], labelFn, (item) => item.id, "Seleccionar…");
      return;
    }
    const current = sel.value;
    sel.innerHTML = "";
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Seleccionar…";
    sel.appendChild(empty);
    (items || []).forEach((item) => {
      const opt = document.createElement("option");
      opt.value = String(item.id);
      opt.textContent = labelFn(item);
      sel.appendChild(opt);
    });
    if (current && [...sel.options].some((o) => o.value === current)) sel.value = current;
  }

  async function loadList() {
    const { ok, data } = await api("GET", def.path);
    if (!ok) {
      toast(formatError(data), "bad");
      table.setRows([]);
      return;
    }
    const raw = Array.isArray(data) ? data : [data];
    table.setRows(def.mapRow ? raw.map((r) => def.mapRow(r)) : raw);
  }

  function selectedDays() {
    return [...document.querySelectorAll("#day-boxes [data-day]:checked")].map((box) =>
      box.getAttribute("data-day")
    );
  }

  function selectedStudents() {
    return [...document.querySelectorAll("#enroll-students [data-student]:checked")].map((box) =>
      Number(box.getAttribute("data-student"))
    );
  }

  function paintEnrollStudents(selected) {
    const host = el("enroll-students");
    if (!host) return;
    const picked = new Set((selected || []).map((id) => String(id)));
    host.innerHTML = "";
    (ctx.students || []).forEach((st) => {
      const id = String(st.id);
      const label = document.createElement("label");
      label.className = "form-check d-block mb-1";
      const box = document.createElement("input");
      box.type = "checkbox";
      box.className = "form-check-input";
      box.setAttribute("data-student", id);
      box.checked = picked.has(id);
      const span = document.createElement("span");
      span.className = "form-check-label ms-2";
      span.textContent = labelStudent(st.id);
      label.appendChild(box);
      label.appendChild(span);
      host.appendChild(label);
    });
    if (!host.children.length) {
      host.textContent = "No hay estudiantes para matricular.";
    }
  }

  async function syncEnrollChecks() {
    const courseId = Number(el("f-course_id")?.value || 0);
    const course = byId(ctx.courses, courseId);
    if (el("f-term_id") && course) el("f-term_id").value = String(course.term_id);
    if (!courseId) {
      paintEnrollStudents([]);
      return;
    }
    const { ok, data } = await api("GET", "/enrollments?course_id=" + courseId);
    const enrolled = ok && Array.isArray(data) ? data.filter((r) => r.status === "ACTIVE").map((r) => r.student_id) : [];
    paintEnrollStudents(enrolled);
  }

  async function createItem(ev) {
    ev.preventDefault();
    const form = ev.target;
    if (form.dataset.mode === "edit" && form.dataset.editId) {
      await updateItem(Number(form.dataset.editId));
      return;
    }
    const fields = readForm();
    const out = el("create-out");
    if (key === "enrollments" && el("enroll-students")) {
      const courseId = Number(fields.course_id || 0);
      const course = byId(ctx.courses, courseId);
      const termId = Number(fields.term_id || (course && course.term_id) || 0);
      if (!courseId || !termId) {
        const msg = "Seleccione el curso.";
        if (out) out.textContent = msg;
        toast(msg, "bad");
        return;
      }
      const { ok, status, data } = await api("POST", "/enrollments/bulk", {
        course_id: courseId,
        term_id: termId,
        student_ids: selectedStudents(),
      });
      if (!ok) {
        const msg =
          status === 403
            ? "DENY: sin permiso para matricular estudiantes."
            : formatError(data);
        if (out) out.textContent = msg;
        toast(msg, "bad");
        return;
      }
      if (out) out.textContent = "Matrícula guardada correctamente.";
      toast("Matrícula guardada correctamente.", "ok");
      await loadLookups();
      await loadList();
      return;
    }
    const days = key === "schedules" ? selectedDays() : [];
    if (key === "schedules") {
      if (!days.length) {
        const msg = "Seleccione al menos un día de clase.";
        if (out) out.textContent = msg;
        toast(msg, "bad");
        return;
      }
      if (!fields.start_time || !fields.end_time) {
        const msg = "Indique hora de inicio y hora de fin.";
        if (out) out.textContent = msg;
        toast(msg, "bad");
        return;
      }
      let created = 0;
      let lastId = "";
      for (const day of days) {
        const body = def.create({ ...fields, day_of_week: day });
        const { ok, status, data } = await api("POST", def.path, body);
        if (!ok) {
          const msg =
            status === 403
              ? "DENY: sin permiso para crear en este catálogo."
              : formatError(data);
          if (out) out.textContent = created ? created + " creado(s). Error: " + msg : msg;
          toast(msg, "bad");
          await loadList();
          return;
        }
        created += 1;
        lastId = data && data.id ? data.id : lastId;
      }
      if (out) out.textContent = "Registro creado correctamente (id " + (lastId || "?") + ").";
      toast(
        created > 1
          ? "Horarios creados correctamente (" + created + " días)."
          : "Registro creado correctamente.",
        "ok"
      );
      ev.target.reset();
      document.querySelectorAll("#day-boxes [data-day]").forEach((box) => {
        box.checked = false;
      });
      await loadLookups();
      await loadList();
      return;
    }
    const body = def.create(fields);
    const { ok, status, data } = await api("POST", def.path, body);
    if (!ok) {
      const msg =
        status === 403
          ? "DENY: sin permiso para crear en este catálogo."
          : formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) out.textContent = "Registro creado correctamente (id " + (data.id || "?") + ").";
    toast("Registro creado correctamente.", "ok");
    ev.target.reset();
    await loadLookups();
    await loadList();
  }

  async function updateItem(id) {
    const out = el("create-out");
    if (!def.updatePath || !def.update) {
      toast("Este registro no admite edición de campos.", "bad");
      return;
    }
    const body = def.update(readForm());
    const { ok, data } = await api("PATCH", def.updatePath(id), body);
    const msg = ok ? "Registro actualizado correctamente." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  async function patchTermStatus() {
    const id = Number(el("term-id")?.value || 0);
    const statusVal = el("term-status")?.value;
    if (!id || !statusVal) {
      toast("Indica periodo y estado.", "bad");
      return;
    }
    const { ok, data } = await api("PATCH", `/terms/${id}/status`, { status: statusVal });
    toast(ok ? "Registro actualizado correctamente." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  async function cancelEnrollment() {
    const id = Number(el("enroll-cancel-id")?.value || 0);
    if (!id) {
      toast("Seleccione una matrícula.", "bad");
      return;
    }
    const { ok, data } = await api("POST", `/enrollments/${id}/cancel`);
    toast(ok ? "Registro eliminado correctamente." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  async function addCurriculumSubject() {
    const id = Number(el("cur-id")?.value || 0);
    const subjectId = Number(el("cur-subject-id")?.value || 0);
    if (!id || !subjectId) {
      toast("Seleccione malla y asignatura.", "bad");
      return;
    }
    const { ok, data } = await api("POST", "/curricula/" + id + "/subjects", {
      subject_id: subjectId,
      level: Number(el("cur-level")?.value || 1),
      semester: Number(el("cur-semester")?.value || 1),
    });
    toast(ok ? "Registro actualizado correctamente." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  el("catalog-create-form")?.addEventListener("submit", (e) => createItem(e));
  el("btn-refresh-catalog")?.addEventListener("click", () => loadList());
  el("btn-new-record")?.addEventListener("click", () => openCreate());
  el("f-hour-preset")?.addEventListener("change", () => {
    const val = el("f-hour-preset")?.value || "";
    if (!val || !val.includes("-")) return;
    const [start, end] = val.split("-");
    if (el("f-start_time")) el("f-start_time").value = start;
    if (el("f-end_time")) el("f-end_time").value = end;
  });
  el("f-term_id")?.addEventListener("change", () => applyDependentFilters());
  el("f-course_id")?.addEventListener("change", () => {
    const courseId = Number(el("f-course_id")?.value || 0);
    const course = byId(ctx.courses, courseId);
    if (course && el("f-term_id") && course.term_id) {
      el("f-term_id").value = String(course.term_id);
    }
    if (key === "enrollments") syncEnrollChecks();
  });
  el("btn-term-status")?.addEventListener("click", () => patchTermStatus());
  el("btn-enroll-cancel")?.addEventListener("click", () => cancelEnrollment());
  el("btn-cur-subject")?.addEventListener("click", () => addCurriculumSubject());

  await loadLookups();
  if (key === "enrollments") paintEnrollStudents([]);
  await loadList();
})();
