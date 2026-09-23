// Sidebar mobile toggle + admin Usuarios + a11y helpers (FASE 10).
function ensureSkipLink() {
  if (document.querySelector(".skip-link")) return;
  const main = document.querySelector("main.app-content, main, #main");
  if (!main) return;
  if (!main.id) main.id = "main-content";
  const a = document.createElement("a");
  a.href = "#" + main.id;
  a.className = "skip-link";
  a.textContent = "Saltar al contenido";
  document.body.insertBefore(a, document.body.firstChild);
}

function ensureBackdrop(frame) {
  let backdrop = frame.querySelector(".nav-backdrop");
  if (!backdrop) {
    backdrop = document.createElement("button");
    backdrop.type = "button";
    backdrop.className = "nav-backdrop";
    backdrop.setAttribute("aria-label", "Cerrar menú");
    frame.appendChild(backdrop);
  }
  return backdrop;
}

function setNavOpen(frame, btn, open) {
  frame.classList.toggle("nav-open", open);
  if (btn) {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
  }
  document.body.style.overflow = open && window.matchMedia("(max-width: 900px)").matches ? "hidden" : "";
}

function wire() {
  ensureSkipLink();
  const frame = document.querySelector(".app-frame");
  const btn = document.getElementById("btn-sidebar");
  if (!frame || !btn) return;

  const backdrop = ensureBackdrop(frame);
  btn.addEventListener("click", () => {
    const open = !frame.classList.contains("nav-open");
    setNavOpen(frame, btn, open);
  });
  backdrop.addEventListener("click", () => setNavOpen(frame, btn, false));

  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && frame.classList.contains("nav-open")) {
      setNavOpen(frame, btn, false);
      btn.focus();
    }
  });

  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 901px)").matches) {
      setNavOpen(frame, btn, false);
    }
  });
}

function ensureCatalogExtras() {
  const sub = document.querySelector(".side-nav-sub");
  if (!sub) return;
  const extras = [
    ["/ui/pages/catalogos/mallas.html", "Mallas"],
    ["/ui/pages/catalogos/aulas.html", "Aulas"],
    ["/ui/pages/catalogos/horarios.html", "Horarios"],
    ["/ui/pages/catalogos/asignaciones.html", "Asignaciones"],
  ];
  extras.forEach(([href, label]) => {
    if (sub.querySelector('a[href="' + href + '"]')) return;
    const a = document.createElement("a");
    a.className = "side-link";
    a.href = href;
    a.textContent = label;
    if (String(location.pathname || "").includes(href.split("/").pop())) {
      a.classList.add("active");
    }
    sub.appendChild(a);
  });
}

function ensureSeguridadNav(user) {
  const roles = (user && user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) return;
  const nav = document.querySelector(".app-sidebar .side-nav");
  if (!nav || nav.querySelector('[data-nav="seguridad"]')) return;
  const link = document.createElement("a");
  link.className = "side-link";
  link.href = "/ui/pages/seguridad/seguridad.html";
  link.dataset.nav = "seguridad";
  link.dataset.roles = "ADMINISTRATOR";
  link.textContent = "Seguridad";
  if (String(location.pathname || "").includes("/seguridad/")) {
    link.classList.add("active");
  }
  const perfil = nav.querySelector('a[href*="/cuenta/perfil"]');
  if (perfil) perfil.insertAdjacentElement("beforebegin", link);
  else nav.appendChild(link);
}

function ensureAdminNav(user) {
  const roles = (user && user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) return;
  const nav = document.querySelector(".app-sidebar .side-nav");
  if (!nav || nav.querySelector('[data-nav="usuarios"]')) return;
  const link = document.createElement("a");
  link.className = "side-link";
  link.href = "/ui/pages/usuarios/usuarios.html";
  link.dataset.nav = "usuarios";
  link.dataset.roles = "ADMINISTRATOR";
  link.textContent = "Usuarios";
  if (String(location.pathname || "").includes("/usuarios/")) {
    link.classList.add("active");
  }
  const catalogos = nav.querySelector('a[href*="/catalogos/"]');
  if (catalogos && catalogos.parentNode === nav) {
    catalogos.insertAdjacentElement("afterend", link);
  } else {
    const reportes = nav.querySelector('a[href*="/reportes/"]');
    if (reportes) reportes.insertAdjacentElement("beforebegin", link);
    else nav.appendChild(link);
  }
}

window.SigaNav = { wire, ensureAdminNav, ensureSkipLink, ensureCatalogExtras, ensureSeguridadNav };
