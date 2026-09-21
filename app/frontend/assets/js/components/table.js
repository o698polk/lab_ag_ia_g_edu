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
};

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
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

function fillSelect(el, items, labelFn, valueFn) {
  if (!el) return;
  const current = el.value;
  if (!items || !items.length) {
    el.innerHTML = '<option value="">Sin datos</option>';
    return;
  }
  el.innerHTML = items
    .map((item) => `<option value="${valueFn(item)}">${escapeHtml(labelFn(item))}</option>`)
    .join("");
  if (current && [...el.options].some((o) => o.value === current)) el.value = current;
}

window.SigaTable = { fillTbody, fillSelect, escapeHtml, COL_LABEL };
