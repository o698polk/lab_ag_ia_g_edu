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
      cols: ["id", "user_id", "student_code", "career_id", "level", "status"],
      statusPath: (id) => "/students/" + id + "/status",
      create: (f) => ({
        user_id: Number(f.user_id),
        student_code: f.student_code,
        career_id: f.career_id ? Number(f.career_id) : null,
        level: f.level || null,
      }),
    },
    teachers: {
      path: "/teachers",
      cols: ["id", "user_id", "teacher_code", "specialty", "status"],
      statusPath: (id) => "/teachers/" + id + "/status",
      create: (f) => ({
        user_id: Number(f.user_id),
        teacher_code: f.teacher_code,
        specialty: f.specialty || null,
      }),
    },
    courses: {
      path: "/courses",
      cols: ["id", "subject_id", "term_id", "parallel_code", "capacity", "status"],
      statusPath: (id) => "/courses/" + id + "/status",
      create: (f) => ({
        subject_id: Number(f.subject_id),
        term_id: Number(f.term_id),
        parallel_code: f.parallel_code || "A",
        capacity: Number(f.capacity || 40),
      }),
    },
    enrollments: {
      path: "/enrollments",
      cols: ["id", "student_id", "course_id", "term_id", "status"],
      delete: (id) => api("POST", "/enrollments/" + id + "/cancel"),
      create: (f) => ({
        student_id: Number(f.student_id),
        course_id: Number(f.course_id),
        term_id: Number(f.term_id),
      }),
    },
    curricula: {
      path: "/curricula",
      cols: ["id", "career_id", "version", "status", "subject_ids"],
      statusPath: (id) => "/curricula/" + id + "/status",
      create: (f) => ({
        career_id: Number(f.career_id),
        version: f.version,
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
      cols: ["id", "course_id", "teacher_id", "classroom_id", "term_id", "day_of_week", "start_time", "end_time"],
      create: (f) => ({
        course_id: Number(f.course_id),
        teacher_id: Number(f.teacher_id),
        classroom_id: Number(f.classroom_id),
        term_id: Number(f.term_id),
        day_of_week: f.day_of_week || "MON",
        start_time: f.start_time,
        end_time: f.end_time,
      }),
    },
    assignments: {
      path: "/teaching-assignments",
      cols: ["id", "teacher_id", "course_id", "term_id", "status"],
      statusPath: (id) => "/teaching-assignments/" + id + "/status",
      create: (f) => ({
        teacher_id: Number(f.teacher_id),
        course_id: Number(f.course_id),
        term_id: Number(f.term_id),
      }),
    },
  };

  const key = document.body.getAttribute("data-entity");
  const def = DEFS[key];
  if (!def) return;

  const el = (id) => document.getElementById(id);
  const labels = SigaTable.COL_LABEL;
  const table = SigaAdminTable.bind({
    tbody: el("catalog-tbody"),
    columns: def.cols,
    searchInput: el("admin-search"),
    filterInput: el("admin-filter"),
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "del"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") openView(row);
      if (act === "edit") openEdit(row);
      if (act === "del") openDelete(row);
    },
  });

  function readForm() {
    const out = {};
    document.querySelectorAll("#catalog-create-form [data-field]").forEach((input) => {
      out[input.getAttribute("data-field")] = (input.value || "").trim();
    });
    return out;
  }

  function viewBody(row) {
    const rows = def.cols
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

  function openCreate() {
    const form = el("catalog-create-form");
    const wrap = el("catalog-create-wrap") || form;
    if (!form || !wrap) return;
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
      if (def.delete) {
        const { ok, data } = await def.delete(row.id);
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

  async function loadList() {
    const { ok, data } = await api("GET", def.path);
    if (!ok) {
      toast(formatError(data), "bad");
      table.setRows([]);
      return;
    }
    table.setRows(Array.isArray(data) ? data : [data]);
  }

  async function createItem(ev) {
    ev.preventDefault();
    const fields = readForm();
    const body = def.create(fields);
    const out = el("create-out");
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
    await loadList();
  }

  async function patchTermStatus() {
    const id = Number(el("term-id")?.value || 0);
    const statusVal = el("term-status")?.value;
    if (!id || !statusVal) {
      toast("Indica id y estado del periodo.", "bad");
      return;
    }
    const { ok, data } = await api("PATCH", `/terms/${id}/status`, { status: statusVal });
    toast(ok ? "Registro actualizado correctamente." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  async function cancelEnrollment() {
    const id = Number(el("enroll-cancel-id")?.value || 0);
    if (!id) {
      toast("Indica id de matrícula.", "bad");
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
      toast("Indica malla y asignatura.", "bad");
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
  el("btn-term-status")?.addEventListener("click", () => patchTermStatus());
  el("btn-enroll-cancel")?.addEventListener("click", () => cancelEnrollment());
  el("btn-cur-subject")?.addEventListener("click", () => addCurriculumSubject());

  await loadList();
})();
