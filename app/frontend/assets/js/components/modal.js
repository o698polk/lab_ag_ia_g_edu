/* Classic admin modal — no Bootstrap JS required */
(function () {
  const escapeHtml = (s) =>
    String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

  function host() {
    let el = document.getElementById("siga-modal-host");
    if (el) return el;
    el = document.createElement("div");
    el.id = "siga-modal-host";
    document.body.appendChild(el);
    return el;
  }

  let restoreFn = null;

  function close() {
    if (typeof restoreFn === "function") {
      try {
        restoreFn();
      } catch (err) {
        /* keep closing */
      }
      restoreFn = null;
    }
    const backdrop = document.getElementById("siga-modal-backdrop");
    if (!backdrop) return;
    backdrop.classList.remove("show");
    backdrop.setAttribute("hidden", "");
    document.body.style.overflow = "";
  }

  function openParked(opts) {
    const o = opts || {};
    const node = o.node;
    if (!node) return open(o);
    const home = node.parentElement;
    node.classList.remove("d-none");
    const wrap = document.createElement("div");
    wrap.appendChild(node);
    return open({
      title: o.title,
      body: wrap,
      footer: o.footer,
      wide: o.wide,
      onClose: () => {
        if (home) {
          node.classList.add("d-none");
          home.appendChild(node);
        }
        if (typeof o.onClose === "function") o.onClose();
      },
    });
  }

  function open(opts) {
    close();
    const o = opts || {};
    restoreFn = typeof o.onClose === "function" ? o.onClose : null;
    const root = host();
    root.innerHTML =
      '<div id="siga-modal-backdrop" class="siga-modal-backdrop show" role="dialog" aria-modal="true">' +
      '<div class="siga-modal' +
      (o.wide ? " wide" : "") +
      '">' +
      '<div class="siga-modal-head">' +
      "<h3>" +
      escapeHtml(o.title || "Diálogo") +
      "</h3>" +
      '<button type="button" class="btn btn-sm btn-outline-secondary" data-modal-close>Cerrar</button>' +
      "</div>" +
      '<div class="siga-modal-body" id="siga-modal-body"></div>' +
      '<div class="siga-modal-foot" id="siga-modal-foot"></div>' +
      "</div></div>";
    const body = document.getElementById("siga-modal-body");
    const foot = document.getElementById("siga-modal-foot");
    if (typeof o.body === "string") body.innerHTML = o.body;
    else if (o.body) body.appendChild(o.body);
    if (typeof o.footer === "string") foot.innerHTML = o.footer;
    else if (o.footer) foot.appendChild(o.footer);
    document.body.style.overflow = "hidden";
    const backdrop = document.getElementById("siga-modal-backdrop");
    backdrop.addEventListener("click", (ev) => {
      if (ev.target === backdrop) close();
    });
    backdrop.querySelectorAll("[data-modal-close]").forEach((btn) => {
      btn.addEventListener("click", () => close());
    });
    document.addEventListener(
      "keydown",
      function onEsc(ev) {
        if (ev.key === "Escape") {
          close();
          document.removeEventListener("keydown", onEsc);
        }
      },
      { once: true }
    );
    return { body, foot, close };
  }

  function confirmDelete(message, onYes) {
    const foot = document.createElement("div");
    foot.className = "d-flex gap-2 justify-content-end";
    foot.innerHTML =
      '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
      '<button type="button" class="btn btn-danger-admin" id="btn-modal-delete">Eliminar</button>';
    const dlg = open({
      title: "Confirmar eliminación",
      body:
        "<p class='mb-0'>" +
        escapeHtml(message || "¿Está seguro de que desea eliminar este registro?") +
        "</p>",
      footer: foot,
    });
    foot.querySelector("#btn-modal-delete")?.addEventListener("click", async () => {
      await onYes();
      dlg.close();
    });
    return dlg;
  }

  function footerCancelSave(saveLabel, formId) {
    const wrap = document.createElement("div");
    wrap.className = "d-flex gap-2 justify-content-end";
    wrap.innerHTML =
      '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cancelar</button>' +
      '<button type="submit" class="btn btn-siga" form="' +
      escapeHtml(formId || "siga-modal-form") +
      '">' +
      escapeHtml(saveLabel || "Guardar") +
      "</button>";
    return wrap;
  }

  function viewDl(pairs) {
    const rows = (pairs || [])
      .map(
        ([k, v]) =>
          "<dt>" +
          escapeHtml(k) +
          "</dt><dd>" +
          escapeHtml(v == null || v === "" ? "—" : v) +
          "</dd>"
      )
      .join("");
    return "<dl class='view-dl'>" + rows + "</dl>";
  }

  window.SigaModal = { open, close, openParked, confirmDelete, footerCancelSave, escapeHtml, viewDl };
})();
