/* global SigaApi, SigaAuth, SigaToast, SigaTable */
// Ref: PromptMaster FASE 7 | una página por entidad · data-entity en <body>
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody } = SigaTable;
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
      create: (f) => ({
        user_id: Number(f.user_id),
        teacher_code: f.teacher_code,
        specialty: f.specialty || null,
      }),
    },
    courses: {
      path: "/courses",
      cols: ["id", "subject_id", "term_id", "parallel_code", "capacity", "status"],
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
      create: (f) => ({
        student_id: Number(f.student_id),
        course_id: Number(f.course_id),
        term_id: Number(f.term_id),
      }),
    },
  };

  const key = document.body.getAttribute("data-entity");
  const def = DEFS[key];
  if (!def) return;

  const el = (id) => document.getElementById(id);

  function readForm() {
    const out = {};
    document.querySelectorAll("[data-field]").forEach((input) => {
      out[input.getAttribute("data-field")] = (input.value || "").trim();
    });
    return out;
  }

  async function loadList() {
    const { ok, data } = await api("GET", def.path);
    const tbody = el("catalog-tbody");
    if (!ok) {
      toast(formatError(data), "bad");
      fillTbody(tbody, [], def.cols);
      return;
    }
    fillTbody(tbody, Array.isArray(data) ? data : [data], def.cols);
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
    if (out) out.textContent = "Registro creado (id " + (data.id || "?") + ").";
    toast("Alta correcta.", "ok");
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
    toast(ok ? "Estado actualizado." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  async function cancelEnrollment() {
    const id = Number(el("enroll-cancel-id")?.value || 0);
    if (!id) {
      toast("Indica id de matrícula.", "bad");
      return;
    }
    const { ok, data } = await api("POST", `/enrollments/${id}/cancel`);
    toast(ok ? "Matrícula cancelada." : formatError(data), ok ? "ok" : "bad");
    if (ok) await loadList();
  }

  el("catalog-create-form")?.addEventListener("submit", (e) => createItem(e));
  el("btn-refresh-catalog")?.addEventListener("click", () => loadList());
  el("btn-term-status")?.addEventListener("click", () => patchTermStatus());
  el("btn-enroll-cancel")?.addEventListener("click", () => cancelEnrollment());

  await loadList();
})();
