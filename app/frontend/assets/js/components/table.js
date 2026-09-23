// Fill existing <tbody> only — table/thead must exist in HTML.
const COL_LABEL = {
  id: "Id", score: "Nota", comment: "Comentario", evaluation_id: "Evaluación",
  student_id: "Estudiante", graded_by_teacher_id: "Docente", graded_at: "Fecha",
  academic_status: "Estado académico", final_grade: "Nota final", credits: "Créditos",
  term_id: "Periodo", subject_id: "Materia", course_id: "Curso", code: "Código",
  name: "Nombre", status: "Estado", parallel_code: "Paralelo", capacity: "Cupo",
  title: "Título", body: "Mensaje", type: "Tipo", student_code: "Código estudiante",
  teacher_code: "Código docente", specialty: "Especialidad", level: "Nivel",
  username: "Usuario", email: "Correo",
  user: "Usuario", course: "Curso", teacher: "Docente", classroom: "Aula",
  term: "Periodo", student: "Estudiante", career: "Carrera", subjects: "Asignaturas",
  evaluation: "Evaluación", session: "Sesión", enrolled_at: "Fecha matrícula",
};

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function personName(item) {
  if (!item) return "";
  return (
    [item.first_name, item.last_name].filter(Boolean).join(" ").trim() ||
    item.full_name ||
    item.name ||
    item.username ||
    item.student_code ||
    item.teacher_code ||
    ""
  );
}

function formatRef(id, text) {
  if (id == null || id === "") return text || "—";
  const name = String(text || "").trim();
  return name ? id + " - " + name : String(id);
}

function fillTbody(tbody, rows, columns) {
  if (!tbody) return;
  if (!rows || !rows.length) {
    tbody.innerHTML = "";
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (empty) empty.classList.remove("d-none");
    return;
  }
  const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
  if (empty) empty.classList.add("d-none");
  const keys = columns && columns.length ? columns : Object.keys(rows[0]);
  tbody.innerHTML = rows
    .map((row) => `<tr>${keys.map((k) => `<td>${escapeHtml(row[k] ?? "")}</td>`).join("")}</tr>`)
    .join("");
}

function makeSearchable(select) {
  if (!select || select.tagName !== "SELECT") return select;
  if (select.dataset.searchable === "1") {
    const box = select.parentElement?.querySelector(".siga-lookup-search");
    if (box) box.classList.toggle("d-none", select.options.length < 8);
    return select;
  }
  const parent = select.parentNode;
  if (!parent) return select;
  const wrap = document.createElement("div");
  wrap.className = "siga-lookup";
  parent.insertBefore(wrap, select);
  const search = document.createElement("input");
  search.type = "search";
  search.className = "form-control form-control-sm siga-lookup-search";
  search.placeholder = "Buscar…";
  search.setAttribute("aria-label", "Buscar opción");
  wrap.appendChild(search);
  wrap.appendChild(select);
  select.dataset.searchable = "1";
  search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    [...select.options].forEach((opt) => {
      if (!opt.value) {
        opt.hidden = false;
        return;
      }
      opt.hidden = q ? !String(opt.textContent || "").toLowerCase().includes(q) : false;
    });
  });
  search.classList.toggle("d-none", select.options.length < 8);
  return select;
}

function fillSelect(node, items, labelFn, valueFn, emptyLabel) {
  if (!node) return;
  const current = node.value;
  const empty = emptyLabel == null ? "Seleccionar…" : emptyLabel;
  if (!items || !items.length) {
    node.innerHTML = '<option value="">' + escapeHtml(empty === "" ? "Sin datos" : empty) + "</option>";
    makeSearchable(node);
    return;
  }
  const opts = ['<option value="">' + escapeHtml(empty) + "</option>"].concat(
    items.map((item) => {
      const value = valueFn ? valueFn(item) : item.id;
      const label = labelFn ? labelFn(item) : formatRef(item.id, personName(item) || item.code || item.name);
      return '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + "</option>";
    })
  );
  node.innerHTML = opts.join("");
  if (current && [...node.options].some((o) => o.value === current)) node.value = current;
  makeSearchable(node);
}

window.SigaTable = {
  fillTbody,
  fillSelect,
  escapeHtml,
  COL_LABEL,
  formatRef,
  personName,
  makeSearchable,
};
