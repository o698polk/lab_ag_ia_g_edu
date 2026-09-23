/* global SigaApi, SigaAuth, SigaToast, SigaModal, SigaAdminTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const el = (id) => document.getElementById(id);
  const search = el("admin-search");

  function viewRow(title, pairs) {
    SigaModal.open({
      title,
      body: SigaModal.viewDl(pairs),
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
    });
  }

  function bindView(tbody, columns, pager, idKey) {
    return SigaAdminTable.bind({
      tbody,
      columns,
      searchInput: search,
      pager,
      idKey,
      actions: () => SigaAdminTable.actionButtons(["view"]),
      onAction: (act, row) => {
        if (act !== "view" || !row) return;
        viewRow(
          "Consulta de registro",
          columns.map((k) => [k, row[k]])
        );
      },
    });
  }

  const polTable = bindView(
    el("policies-tbody"),
    ["policy_id", "version", "module", "effect_default", "rules_count"],
    el("pager-policies"),
    "policy_id"
  );
  const toolTable = bindView(
    el("tools-tbody"),
    ["tool_name", "risk_level", "required_permissions", "allowed_roles", "resource_type"],
    el("pager-tools"),
    "tool_name"
  );
  const auditTable = bindView(
    el("audit-tbody"),
    ["id", "request_id", "user_id", "action", "module", "status", "reason", "created_at"],
    el("pager-audit"),
    "id"
  );
  const secTable = bindView(
    el("security-tbody"),
    ["id", "request_id", "user_id", "event_type", "severity", "created_at"],
    el("pager-security"),
    "id"
  );

  function fmtDate(v) {
    return v ? String(v).replace("T", " ").slice(0, 19) : "";
  }

  async function loadPolicies() {
    const { ok, data } = await api("GET", "/policies");
    if (!ok) {
      toast(formatError(data), "bad");
      polTable.setRows([]);
      return;
    }
    polTable.setRows(Array.isArray(data) ? data : []);
  }

  async function loadTools() {
    const { ok, data } = await api("GET", "/tools");
    if (!ok) {
      toast(formatError(data), "bad");
      toolTable.setRows([]);
      return;
    }
    const rows = (Array.isArray(data) ? data : []).map((t) => ({
      tool_name: t.tool_name,
      risk_level: t.risk_level,
      required_permissions: (t.required_permissions || []).join(", "),
      allowed_roles: (t.allowed_roles || []).join(", "),
      resource_type: t.resource_type,
    }));
    toolTable.setRows(rows);
  }

  async function loadAudit() {
    const { ok, data } = await api("GET", "/audit/events");
    if (!ok) {
      toast(formatError(data), "bad");
      auditTable.setRows([]);
      return;
    }
    const rows = (Array.isArray(data) ? data : []).map((r) => ({
      id: r.id,
      request_id: r.request_id,
      user_id: r.user_id,
      action: r.action,
      module: r.module,
      status: r.status,
      reason: r.reason,
      created_at: fmtDate(r.created_at),
    }));
    auditTable.setRows(rows);
  }

  async function loadSecurity() {
    const { ok, data } = await api("GET", "/security/events");
    if (!ok) {
      toast(formatError(data), "bad");
      secTable.setRows([]);
      return;
    }
    const rows = (Array.isArray(data) ? data : []).map((r) => ({
      id: r.id,
      request_id: r.request_id,
      user_id: r.user_id,
      event_type: r.event_type,
      severity: r.severity,
      created_at: fmtDate(r.created_at),
    }));
    secTable.setRows(rows);
  }

  async function refreshAll() {
    await Promise.all([loadPolicies(), loadTools(), loadAudit(), loadSecurity()]);
  }

  el("btn-sec-refresh")?.addEventListener("click", () => refreshAll());
  await refreshAll();
})();
