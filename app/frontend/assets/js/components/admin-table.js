/* DataTable: search, filter, sort, pagination, status, actions. thead stays in HTML. */
/* global SigaTable */
(function () {
  const escapeHtml = (s) =>
    window.SigaTable ? SigaTable.escapeHtml(s) : String(s ?? "").replaceAll("<", "&lt;");

  function badgeClass(value) {
    const v = String(value || "").toUpperCase();
    if (["ACTIVE", "ACTIVO", "SÍ", "SI", "PRESENT", "SUCCESS", "ALLOW", "APPROVED"].includes(v)) {
      return "is-active";
    }
    if (["INACTIVE", "INACTIVO", "DELETED", "LOCKED", "CANCELLED", "FAILED", "ABSENT", "DENY"].includes(v)) {
      return "is-off";
    }
    if (["PLANNED", "LATE", "JUSTIFIED", "WARNING", "IN_PROGRESS"].includes(v)) return "is-warn";
    return "";
  }

  function statusHtml(value) {
    const text = value == null || value === "" ? "—" : String(value);
    return '<span class="status-badge ' + badgeClass(text) + '">' + escapeHtml(text) + "</span>";
  }

  function bind(opts) {
    const cfg = Object.assign(
      {
        tbody: null,
        columns: [],
        statusKeys: ["status", "is_active", "academic_status", "result_status"],
        pageSize: 10,
        searchInput: null,
        filterInput: null,
        filterKey: "status",
        pager: null,
        idKey: "id",
        actions: null,
      },
      opts || {}
    );
    let all = [];
    let page = 1;
    let sortKey = null;
    let sortDir = 1;

    function filtered() {
      const q = String(cfg.searchInput?.value || "")
        .trim()
        .toLowerCase();
      const fv = String(cfg.filterInput?.value || "").trim();
      let rows = all.slice();
      if (fv) rows = rows.filter((r) => String(r[cfg.filterKey] ?? "") === fv);
      if (q) {
        rows = rows.filter((r) =>
          cfg.columns.some((k) => String(r[k] ?? "").toLowerCase().includes(q))
        );
      }
      if (sortKey) {
        rows.sort((a, b) => {
          const av = a[sortKey] ?? "";
          const bv = b[sortKey] ?? "";
          if (av < bv) return -1 * sortDir;
          if (av > bv) return 1 * sortDir;
          return 0;
        });
      }
      return rows;
    }

    function paint() {
      const tbody = cfg.tbody;
      if (!tbody) return;
      const rows = filtered();
      const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
      const pages = Math.max(1, Math.ceil(rows.length / cfg.pageSize));
      if (page > pages) page = pages;
      const start = (page - 1) * cfg.pageSize;
      const slice = rows.slice(start, start + cfg.pageSize);
      if (!slice.length) {
        tbody.innerHTML = "";
        if (empty) {
          empty.classList.remove("d-none");
          empty.textContent = all.length ? "Sin resultados para la búsqueda." : "Sin registros.";
        }
      } else {
        if (empty) empty.classList.add("d-none");
        tbody.innerHTML = slice
          .map((row) => {
            const cells = cfg.columns
              .map((k) => {
                const val = row[k];
                const cell = cfg.statusKeys.includes(k)
                  ? statusHtml(val)
                  : escapeHtml(val ?? "");
                return "<td>" + cell + "</td>";
              })
              .join("");
            const acts = cfg.actions
              ? '<td class="col-actions"><span class="action-btns">' +
                cfg.actions(row) +
                "</span></td>"
              : "";
            const rid = row[cfg.idKey] ?? row.id ?? "";
            return '<tr data-row-id="' + escapeHtml(rid) + '">' + cells + acts + "</tr>";
          })
          .join("");
        if (cfg.actions) {
          tbody.querySelectorAll("[data-act]").forEach((btn) => {
            btn.addEventListener("click", () => {
              const id = btn.closest("tr")?.getAttribute("data-row-id");
              const row = all.find((r) => String(r[cfg.idKey] ?? r.id) === String(id));
              cfg.onAction?.(btn.getAttribute("data-act"), row);
            });
          });
        }
      }
      if (cfg.pager) {
        const from = rows.length ? start + 1 : 0;
        const to = start + slice.length;
        cfg.pager.innerHTML =
          "<span>" +
          from +
          "–" +
          to +
          " de " +
          rows.length +
          "</span>" +
          '<span class="d-flex gap-1">' +
          '<button type="button" class="btn btn-outline-secondary" data-page="-1"' +
          (page <= 1 ? " disabled" : "") +
          ">Anterior</button>" +
          '<button type="button" class="btn btn-outline-secondary" data-page="1"' +
          (page >= pages ? " disabled" : "") +
          ">Siguiente</button></span>";
        cfg.pager.querySelectorAll("[data-page]").forEach((b) => {
          b.addEventListener("click", () => {
            page += Number(b.getAttribute("data-page"));
            paint();
          });
        });
      }
    }

    function setRows(rows) {
      all = Array.isArray(rows) ? rows : [];
      page = 1;
      paint();
    }

    cfg.searchInput?.addEventListener("input", () => {
      page = 1;
      paint();
    });
    cfg.filterInput?.addEventListener("change", () => {
      page = 1;
      paint();
    });

    const table = cfg.tbody?.closest("table");
    table?.querySelectorAll("thead th[data-sort]").forEach((th) => {
      th.style.cursor = "pointer";
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-sort");
        if (sortKey === key) sortDir *= -1;
        else {
          sortKey = key;
          sortDir = 1;
        }
        paint();
      });
    });

    return { setRows, paint, getRows: () => all };
  }

  function actionButtons(kinds) {
    const map = {
      view: '<button type="button" class="btn btn-outline-secondary" data-act="view">Ver</button>',
      edit: '<button type="button" class="btn btn-outline-secondary" data-act="edit">Editar</button>',
      del: '<button type="button" class="btn btn-outline-secondary" data-act="del">Eliminar</button>',
    };
    return (kinds || ["view", "edit", "del"]).map((k) => map[k] || "").join("");
  }

  window.SigaAdminTable = { bind, statusHtml, actionButtons, badgeClass };
})();
