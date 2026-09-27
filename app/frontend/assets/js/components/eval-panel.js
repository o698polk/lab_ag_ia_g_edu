/* global SigaApi, SigaToast */
(function () {
  if (window.SigaEval) return;

  var state = {
    cases: [],
    lastA: null,
    lastB: null,
    observed: {},
    running: false,
  };

  function el(id) {
    return document.getElementById(id);
  }

  function toast(msg, kind) {
    if (window.SigaToast && SigaToast.toast) SigaToast.toast(msg, kind);
  }

  function currentRole() {
    var user = window.SigaApi && SigaApi.state && SigaApi.state.user;
    return ((user && user.roles) || [])[0] || "";
  }

  function currentUserName() {
    var user = window.SigaApi && SigaApi.state && SigaApi.state.user;
    return (user && user.username) || "";
  }

  async function loadCases(query) {
    if (!window.SigaApi) return;
    var q = query ? "&q=" + encodeURIComponent(query) : "";
    var res = await SigaApi.api("GET", "/ai/eval/cases?mine=true" + q);
    if (!res.ok) return;
    state.cases = (res.data && res.data.cases) || [];
    paintHints();
    paintTable();
  }

  function paintHints() {
    var hosts = [el("ai-role-hints"), el("siga-eval-hints")].filter(Boolean);
    if (!hosts.length) return;
    var picked = [];
    state.cases.forEach(function (c) {
      if (c.category === "L" && picked.length < 3) picked.push(c);
    });
    state.cases.forEach(function (c) {
      if (c.category !== "L" && picked.length < 8) picked.push(c);
    });
    hosts.forEach(function (host) {
      host.innerHTML = "";
      picked.forEach(function (c) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm " + (c.expected_scenario_b === "DENY" ? "btn-outline-danger" : "btn-outline-secondary");
        btn.textContent = c.question;
        btn.title = c.case_id + " · B espera " + c.expected_scenario_b;
        btn.addEventListener("click", function () {
          if (typeof window.sigaSendEvalQuestion === "function") {
            window.sigaSendEvalQuestion(c.question, c.case_id);
            return;
          }
          runOne(c.case_id);
        });
        host.appendChild(btn);
      });
    });
  }

  function paintTable() {
    var body = el("eval-tbody");
    if (!body) return;
    var q = String((el("eval-search") && el("eval-search").value) || "").toLowerCase();
    var cat = (el("eval-filter-cat") && el("eval-filter-cat").value) || "";
    var exp = (el("eval-filter-exp") && el("eval-filter-exp").value) || "";
    var rows = state.cases.filter(function (c) {
      if (cat && c.category !== cat) return false;
      if (exp && c.expected_scenario_b !== exp) return false;
      if (q && c.question.toLowerCase().indexOf(q) < 0 && c.case_id.toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    body.innerHTML = rows
      .map(function (c) {
        return (
          "<tr data-case='" +
          c.case_id +
          "'><td>" +
          c.case_id +
          "</td><td>" +
          c.category +
          "</td><td>" +
          escapeHtml(c.question) +
          "</td><td>" +
          c.expected_scenario_b +
          "</td><td>" +
          c.expected_tool +
          "</td><td>" +
          escapeHtml(state.observed[c.case_id] || "—") +
          "</td><td><button type='button' class='btn btn-sm btn-outline-secondary' data-run='" +
          c.case_id +
          "'>Ejecutar</button></td></tr>"
        );
      })
      .join("");
    body.querySelectorAll("[data-run]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        runOne(btn.getAttribute("data-run"));
      });
    });
    var count = el("eval-count");
    if (count) count.textContent = String(rows.length);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function paintCompare() {
    var box = el("eval-compare");
    if (!box) return;
    function line(label, run) {
      if (!run || !run.indicators) return label + ": sin ejecución";
      var i = run.indicators;
      return (
        label +
        " · exec " +
        i.executed +
        " · ALLOW " +
        i.authorized +
        " · DENY " +
        i.denied +
        " · adv bloqueadas " +
        i.adversarial_blocked +
        " · adv ejecutadas " +
        i.adversarial_executed_in_open
      );
    }
    box.textContent = line("A (políticas off)", state.lastA) + "  |  " + line("B (políticas on)", state.lastB);
  }

  function appendLive(text) {
    var live = el("eval-live");
    if (!live) return;
    live.textContent = text;
  }

  async function runOne(caseId) {
    if (state.running || !window.SigaApi) return;
    state.running = true;
    appendLive("Ejecutando " + caseId + "…");
    var res = await SigaApi.api("POST", "/ai/eval/run", { case_id: caseId });
    state.running = false;
    if (!res.ok) {
      toast(SigaApi.formatError(res.data), "bad");
      appendLive("Error: " + SigaApi.formatError(res.data));
      return;
    }
    var row = res.data.result || {};
    state.observed[caseId] = (res.data.scenario || "") + " " + (row.observed_decision || "");
    paintTable();
    appendLive(
      caseId +
        " · " +
        res.data.scenario +
        " · " +
        row.observed_decision +
        " · " +
        (row.reason_code || "")
    );
    toast(row.observed_decision === "DENY" ? "DENY (políticas)" : "ALLOW", row.observed_decision === "DENY" ? "bad" : "ok");
  }

  async function runBattery() {
    if (state.running || !window.SigaApi) return;
    if (!window.confirm("¿Ejecutar la batería del rol autenticado contra el escenario activo?")) return;
    state.running = true;
    appendLive("Ejecutando batería…");
    var res = await SigaApi.api("POST", "/ai/eval/battery", {});
    state.running = false;
    if (!res.ok) {
      toast(SigaApi.formatError(res.data), "bad");
      appendLive("Error: " + SigaApi.formatError(res.data));
      return;
    }
    if (res.data.scenario === "A") state.lastA = res.data;
    else state.lastB = res.data;
    (res.data.results || []).forEach(function (row) {
      state.observed[row.case_id] = (res.data.scenario || "") + " " + (row.observed_decision || "");
    });
    paintTable();
    paintCompare();
    appendLive("Batería " + res.data.scenario + " lista. run_id=" + res.data.run_id);
    var exportBtn = el("eval-export");
    if (exportBtn) exportBtn.setAttribute("data-run", res.data.run_id);
  }

  async function exportLast() {
    var btn = el("eval-export");
    var runId = btn && btn.getAttribute("data-run");
    if (!runId || !window.SigaApi) {
      toast("Ejecute una batería primero.", "bad");
      return;
    }
    downloadExport(runId, "json");
  }

  async function exportCsv() {
    var btn = el("eval-export");
    var runId = btn && btn.getAttribute("data-run");
    if (!runId) {
      toast("Ejecute una batería primero.", "bad");
      return;
    }
    downloadExport(runId, "csv");
  }

  async function downloadExport(runId, fmt) {
    if (!window.SigaApi) return;
    var res = await SigaApi.api("GET", "/ai/eval/export?run_id=" + encodeURIComponent(runId) + "&fmt=" + fmt);
    if (!res.ok) {
      toast(SigaApi.formatError(res.data), "bad");
      return;
    }
    var payload = fmt === "csv" ? res.data : JSON.stringify(res.data, null, 2);
    if (fmt === "csv" && typeof payload !== "string") payload = JSON.stringify(payload);
    var blob = new Blob([payload], { type: fmt === "csv" ? "text/csv" : "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "eval-" + runId + "." + fmt;
    a.click();
  }

  function resetBattery() {
    state.lastA = null;
    state.lastB = null;
    state.observed = {};
    var exportBtn = el("eval-export");
    if (exportBtn) exportBtn.removeAttribute("data-run");
    paintTable();
    paintCompare();
    appendLive("Batería reiniciada en la interfaz. El escenario activo no cambia.");
  }

  function html() {
    var role = currentRole();
    return (
      '<div class="eval-lab">' +
      "<h3>Evaluación experimental Zero Trust</h3>" +
      "<p class='hint'>Las mismas preguntas se ejecutan en A (políticas off) y B (políticas on). El rol es el de la sesión autenticada: <strong>" +
      escapeHtml(currentUserName()) +
      "</strong> · " +
      escapeHtml(role) +
      ".</p>" +
      '<p class="siga-chat-banner" data-guard-banner>El agente aplica políticas de mínimo privilegio y autorizaciones.</p>' +
      '<div class="eval-filters">' +
      '<input id="eval-search" class="form-control form-control-sm" placeholder="Buscar caso" />' +
      '<select id="eval-filter-cat" class="form-select form-select-sm"><option value="">Categoría</option><option value="L">L legítima</option><option value="N">N no autorizada</option><option value="Ab">Ab abuso</option><option value="Esc">Esc escalamiento</option><option value="Ev">Ev elusión</option><option value="Ctx">Ctx contexto</option></select>' +
      '<select id="eval-filter-exp" class="form-select form-select-sm"><option value="">Esperado en B</option><option value="ALLOW">ALLOW</option><option value="DENY">DENY</option></select>' +
      "<span id='eval-count' class='hint'>0</span></div>" +
      '<div class="table-wrap eval-table"><table class="table table-sm"><thead><tr><th>ID</th><th>Cat</th><th>Pregunta</th><th>B</th><th>Tool</th><th>Obs.</th><th></th></tr></thead><tbody id="eval-tbody"></tbody></table></div>' +
      '<div class="eval-actions">' +
      '<button type="button" class="btn btn-sm btn-siga" id="eval-run-all">Ejecutar batería del rol</button>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary" id="eval-reset">Reiniciar batería</button>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary" id="eval-export">Exportar JSON</button>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary" id="eval-export-csv">Exportar CSV</button>' +
      "</div>" +
      '<p id="eval-live" class="hint" role="status"></p>' +
      '<p id="eval-compare" class="eval-compare">A vs B: ejecute la batería con políticas off y luego on.</p>' +
      "</div>"
    );
  }

  function wire(root) {
    if (!root || root.getAttribute("data-wired")) return;
    root.setAttribute("data-wired", "1");
    root.innerHTML = html();
    el("eval-search") && el("eval-search").addEventListener("input", paintTable);
    el("eval-filter-cat") && el("eval-filter-cat").addEventListener("change", paintTable);
    el("eval-filter-exp") && el("eval-filter-exp").addEventListener("change", paintTable);
    el("eval-run-all") && el("eval-run-all").addEventListener("click", runBattery);
    el("eval-reset") && el("eval-reset").addEventListener("click", resetBattery);
    el("eval-export") && el("eval-export").addEventListener("click", exportLast);
    el("eval-export-csv") && el("eval-export-csv").addEventListener("click", exportCsv);
    loadCases();
  }

  function mount() {
    var page = el("eval-root");
    var dock = el("siga-eval-root");
    if (page) {
      wire(page);
      return;
    }
    if (dock) {
      wire(dock);
      return;
    }
    loadCases();
  }

  window.SigaEval = { mount: mount, loadCases: loadCases, paintHints: paintHints };
})();
