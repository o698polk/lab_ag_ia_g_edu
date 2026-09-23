/* global SigaApi, SigaAuth, SigaToast, SigaTable, SigaModal, SigaAdminTable */
// Ref: PromptMaster FASE 8 | GET /reports/catalog · POST /reports · GET /reports/logs
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody, escapeHtml, COL_LABEL } = SigaTable;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("TEACHER") && !roles.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const GROUPS = {
    people: ["students", "teachers", "career"],
    academic: ["grades", "averages", "failure", "kardex", "attendance", "term_academic"],
    ops: ["enrollments", "teacher_load"],
  };

  const LOG_COLS = ["id", "user_id", "report_type", "format", "result_status", "row_count", "created_at"];
  const el = (id) => document.getElementById(id);
  let catalog = [];
  const catalogTable = SigaAdminTable.bind({
    tbody: el("report-catalog-tbody"),
    columns: ["code", "name", "group", "description"],
    searchInput: el("admin-search"),
    pager: el("pager-catalog"),
    idKey: "code",
    actions: () => SigaAdminTable.actionButtons(["view", "edit"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de reporte",
          body: SigaModal.viewDl([
            ["Código", row.code],
            ["Nombre", row.name],
            ["Grupo", row.group],
            ["Descripción", row.description],
          ]),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") openGenerate(row.code);
    },
  });
  const logsTable = SigaAdminTable.bind({
    tbody: el("logs-tbody"),
    columns: LOG_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-logs"),
    statusKeys: ["result_status"],
    actions: () => SigaAdminTable.actionButtons(["view"]),
    onAction: (act, row) => {
      if (act !== "view" || !row) return;
      SigaModal.open({
        title: "Consulta de historial",
        body: SigaModal.viewDl(LOG_COLS.map((k) => [k, row[k]])),
        footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      });
    },
  });

  function openGenerate(code) {
    if (code) selectType(code);
    const wrap = el("report-generate-wrap");
    if (!wrap) return;
    SigaModal.openParked({
      title: "Generar reporte",
      node: wrap,
      footer:
        '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
        '<button type="button" class="btn btn-siga" id="btn-modal-generate">Guardar</button>',
      wide: true,
    });
    document.getElementById("btn-modal-generate")?.addEventListener("click", () => generateReport());
  }

  function groupOf(code) {
    for (const [g, codes] of Object.entries(GROUPS)) {
      if (codes.includes(code)) return g;
    }
    return "ops";
  }

  function syncParamVisibility() {
    const type = el("report-type")?.value || "";
    const termWrap = el("param-term-wrap");
    const studentWrap = el("param-student-wrap");
    if (termWrap) termWrap.classList.toggle("d-none", type !== "term_academic");
    if (studentWrap) studentWrap.classList.toggle("d-none", type !== "kardex");
  }

  function selectType(code) {
    const sel = el("report-type");
    if (sel) sel.value = code;
    document.querySelectorAll(".report-type-chip").forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.code === code);
    });
    const item = catalog.find((c) => c.code === code);
    const meta = el("report-meta");
    if (meta) {
      meta.textContent = item
        ? (item.description || item.name || code) + " · código `" + code + "`"
        : "Tipo: " + code;
    }
    syncParamVisibility();
  }

  function paintCatalog(items) {
    catalog = items;
    const empty = el("catalog-empty");
    Object.keys(GROUPS).forEach((g) => {
      const host = document.querySelector('[data-group="' + g + '"]');
      if (!host) return;
      host.innerHTML = "";
    });
    if (!items.length) {
      if (empty) empty.classList.remove("d-none");
      return;
    }
    if (empty) empty.classList.add("d-none");
    const sel = el("report-type");
    if (sel) {
      sel.innerHTML = items
        .map((c) => `<option value="${escapeHtml(c.code)}">${escapeHtml(c.name || c.code)}</option>`)
        .join("");
    }
    items.forEach((c) => {
      const host = document.querySelector('[data-group="' + groupOf(c.code) + '"]');
      if (!host) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-sm btn-outline-secondary report-type-chip role-chip";
      btn.dataset.code = c.code;
      btn.textContent = c.name || c.code;
      btn.title = c.description || c.code;
      btn.addEventListener("click", () => selectType(c.code));
      host.appendChild(btn);
    });
    selectType(items[0].code);
    const labels = { people: "Personas", academic: "Académico", ops: "Operación" };
    catalogTable.setRows(
      items.map((c) => ({
        code: c.code,
        name: c.name || c.code,
        group: labels[groupOf(c.code)] || groupOf(c.code),
        description: c.description || "",
      }))
    );
  }

  function buildParameters() {
    const type = el("report-type").value;
    const params = {};
    if (type === "term_academic") {
      const termId = el("param-term-id")?.value;
      if (termId) params.term_id = Number(termId);
    }
    if (type === "kardex") {
      const studentId = el("param-student-id")?.value;
      if (studentId) params.student_id = Number(studentId);
    }
    return params;
  }

  function showPreview(format, content, rowCount) {
    const badge = el("preview-badge");
    const pre = el("report-out");
    const htmlBox = el("report-preview-html");
    const tableWrap = el("preview-table-wrap");
    if (badge) {
      badge.textContent = format + " · " + rowCount + " fila(s)";
      badge.classList.remove("muted");
      badge.classList.add("ok");
    }
    htmlBox?.classList.add("d-none");
    tableWrap?.classList.add("d-none");
    if (pre) pre.classList.remove("d-none");

    if (format === "HTML") {
      if (pre) pre.classList.add("d-none");
      if (htmlBox) {
        htmlBox.classList.remove("d-none");
        htmlBox.innerHTML = content;
      }
      return;
    }

    if (format === "PDF") {
      if (pre) pre.textContent = "PDF generado (" + (content ? content.length : 0) + " bytes). Usa Descargar.";
      let btn = document.getElementById("btn-download-pdf");
      if (!btn) {
        btn = document.createElement("button");
        btn.id = "btn-download-pdf";
        btn.type = "button";
        btn.className = "btn btn-sm btn-outline-secondary mt-2";
        btn.textContent = "Descargar PDF";
        pre?.insertAdjacentElement("afterend", btn);
      }
      btn.onclick = () => {
        const bytes = new Uint8Array(content.length);
        for (let i = 0; i < content.length; i += 1) bytes[i] = content.charCodeAt(i) & 0xff;
        const blob = new Blob([bytes], { type: "application/pdf" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "reporte-siga.pdf";
        a.click();
      };
      return;
    }

    if (format === "JSON") {
      if (pre) pre.textContent = content;
      try {
        const rows = JSON.parse(content);
        if (Array.isArray(rows) && rows.length) {
          const keys = Object.keys(rows[0]);
          const thead = el("preview-thead-row");
          if (thead) {
            thead.innerHTML = keys
              .map((k) => "<th>" + escapeHtml(COL_LABEL[k] || k) + "</th>")
              .join("");
          }
          fillTbody(el("preview-tbody"), rows, keys);
          tableWrap?.classList.remove("d-none");
        }
      } catch (e) {
        /* keep raw pre */
      }
      return;
    }

    if (pre) pre.textContent = content;
  }

  async function loadCatalog() {
    const { ok, data } = await api("GET", "/reports/catalog");
    if (!ok || !Array.isArray(data)) {
      paintCatalog([]);
      toast(ok ? "Catálogo vacío" : formatError(data), "bad");
      return;
    }
    paintCatalog(data);
  }

  async function generateReport() {
    const type = el("report-type")?.value;
    const format = el("report-format")?.value || "JSON";
    if (!type) {
      toast("Selecciona un tipo de reporte.", "bad");
      return;
    }
    const body = {
      report_type: type,
      format: format,
      parameters: buildParameters(),
    };
    const { ok, data } = await api("POST", "/reports", body);
    if (!ok) {
      if (el("report-out")) el("report-out").textContent = formatError(data);
      toast(formatError(data), "bad");
      return;
    }
    showPreview(data.format || format, data.content || "", data.row_count || 0);
    toast("Reporte generado (log " + data.log_id + ").", "ok");
    await loadReportLogs();
  }

  async function loadReportLogs() {
    const { ok, data } = await api("GET", "/reports/logs");
    const tbody = el("logs-tbody");
    if (!ok) {
      toast(formatError(data), "bad");
      logsTable.setRows([]);
      return;
    }
    const rows = (Array.isArray(data) ? data : []).map((r) => ({
      id: r.id,
      user_id: r.user_id,
      report_type: r.report_type,
      format: r.format,
      result_status: r.result_status,
      row_count: r.row_count,
      created_at: r.created_at ? String(r.created_at).replace("T", " ").slice(0, 19) : "",
    }));
    logsTable.setRows(rows);
  }

  el("btn-report")?.addEventListener("click", () => generateReport());
  el("btn-new-record")?.addEventListener("click", () => openGenerate());
  el("btn-report-logs")?.addEventListener("click", () => loadReportLogs());
  el("report-type")?.addEventListener("change", () => selectType(el("report-type").value));

  await loadCatalog();
  await loadReportLogs();
})();
