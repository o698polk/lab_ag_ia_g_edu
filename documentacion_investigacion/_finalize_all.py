# -*- coding: utf-8 -*-
"""Finaliza entregables: expande MD, corrige refs, DOCX, auditoría, matriz, registro, maestro."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Pt, Inches, Cm

DOC = Path(r"D:\PROYECTOS\lab_ag_ia_g_edu\documentacion_investigacion")
MD = DOC / "proyecto_investigacion_lab_ag_ia_g_edu.md"
EXPAND = DOC / "_expand_final.md"
DOCX = DOC / "proyecto_investigacion_lab_ag_ia_g_edu.docx"
AUDIT = DOC / "informe_auditoria_proyecto.md"
MATRIX = DOC / "matriz_trazabilidad.md"
REFS = DOC / "registro_referencias.md"
WC = DOC / "_wordcount.txt"
MASTER_SRC = Path(
    r"d:\Docente_istae_info_plk\MAESTRIA-CIBERSEGURIDAD_UIDE\MODULOS\ANTEPROYECTO\ENTREGA_3\Actualizacion_AG\promptmasterskillblut.md"
)
MASTER_OUT_PROJ = DOC / "promptmasterskillblut.md"
MASTER_OUT_AG = MASTER_SRC  # actualizar en Actualizacion_AG también
BACKUP = DOC / "promptmasterskillblut_BACKUP_ORIGINAL.md"

CORRECT_REFS = """
# Referencias

Adahman, Z., Malik, A. W., & Anwar, Z. (2022). An analysis of zero-trust architecture and its cost-effectiveness for organizational security. *Computers & Security*, *122*, Article 102911. https://doi.org/10.1016/j.cose.2022.102911

Awan, S. M., Azad, M. A., Arshad, J., Waheed, U., & Sharif, T. (2023). A blockchain-inspired attribute-based zero-trust access control model for IoT. *Information*, *14*(2), Article 129. https://doi.org/10.3390/info14020129

Azad, M. A., Abdullah, S., Arshad, J., Lallie, H., & Ahmed, Y. H. (2024). Verify and trust: A multidimensional survey of zero-trust security in the age of IoT. *Internet of Things*, *27*, Article 101227. https://doi.org/10.1016/j.iot.2024.101227

Buck, C., Olenberger, C., Schweizer, A., Völter, F., & Eymann, T. (2021). Never trust, always verify: A multivocal literature review on current knowledge and research gaps of zero-trust. *Computers & Security*, *110*, Article 102436. https://doi.org/10.1016/j.cose.2021.102436

Deng, Z., Guo, Y., Han, C., Ma, W., Xiong, J., Wen, S., & Xiang, Y. (2025). AI agents under threat: A survey of key security challenges and future pathways. *ACM Computing Surveys*, *57*(7), Article 182. https://doi.org/10.1145/3716628

Geng, T., Xu, Z., Qu, Y., & Wong, W. (2026). Prompt injection attacks on large language models: A survey of attack methods, root causes, and defense strategies. *Computers, Materials & Continua*, *87*(1). https://doi.org/10.32604/cmc.2025.074081

Gulyamov, S., Gulyamov, S., Rodionov, A., Khursanov, R., Mekhmonov, K., Babaev, D., & Rakhimjonov, A. (2026). Prompt injection attacks in large language models and AI agent systems: A comprehensive review of vulnerabilities, attack vectors, and defense mechanisms. *Information*, *17*(1), Article 54. https://doi.org/10.3390/info17010054

Jeong, E., & Yang, D. (2025). A trust score-based access control model for zero trust architecture: Design, sensitivity analysis, and real-world performance evaluation. *Applied Sciences*, *15*(17), Article 9551. https://doi.org/10.3390/app15179551

Kanaker, H., Fakhouri, H., Karim, N. A., Abuhamdeh, M., Ismail, N. H. A., & Fakhouri, S. (2026). Securing tool-using AI agents against injection and authority misuse. *Computation*, *14*(5), Article 98. https://doi.org/10.3390/computation14050098

Kang, H., Liu, G., Wang, Q., Meng, L., & Liu, J. (2023). Theory and application of zero trust security: A brief survey. *Entropy*, *25*(12), Article 1595. https://doi.org/10.3390/e25121595

Mawgoud, A. A., Taha, M. H. N., Loey, M., Hussain Malik, M., & Khalifa, N. E. (2025). Enhancing data privacy and trust in e-learning: A blockchain-based access control protocol for cloud educational systems. *Concurrency and Computation: Practice and Experience*, *37*(18-20), Article e70185. https://doi.org/10.1002/cpe.70185

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero trust architecture* (NIST Special Publication 800-207). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-207

Shostack, A. (2014). *Threat modeling: Designing for security*. John Wiley & Sons.

Syed, N. F., Shah, S. W. A., Shaghaghi, A., Anwar, A., Baig, Z., & Doss, R. (2022). Zero Trust Architecture (ZTA): A comprehensive survey. *IEEE Access*, *10*, 57143–57179. https://doi.org/10.1109/ACCESS.2022.3174679

Vasović, D., Janaćković, G., Vranjanac, Ž., Stamenković, S., & Vasović, B. (2026). Enhancing CIA triad—confidentiality, integrity and availability in educational information systems through next-generation ISO/IEC 27001:2022-aligned security model. *Applied Sciences*, *16*(12), Article 6260. https://doi.org/10.3390/app16126260

Xu, D., Gondal, I., Yi, X., Susnjak, T., Watters, P., & McIntosh, T. R. (2025). The erosion of cybersecurity zero-trust principles through generative AI: A survey on the challenges and future directions. *Journal of Cybersecurity and Privacy*, *5*(4), Article 87. https://doi.org/10.3390/jcp5040087
"""


def update_main_md() -> int:
    text = MD.read_text(encoding="utf-8")
    expand = EXPAND.read_text(encoding="utf-8") if EXPAND.exists() else ""
    # insert expansion before Referencias if not already present
    if "2.8 Ampliación analítica" not in text and expand.strip():
        text = text.replace("\n# Referencias\n", "\n" + expand.strip() + "\n\n# Referencias\n", 1)
    # replace references block through Anexos
    m = re.search(r"\n# Referencias\n", text)
    a = re.search(r"\n# Anexos\n", text)
    if m and a and m.start() < a.start():
        text = text[: m.start()] + "\n" + CORRECT_REFS.strip() + "\n\n" + text[a.start() + 1 :]
    MD.write_text(text, encoding="utf-8")
    words = len(re.findall(r"\S+", text))
    WC.write_text(
        f"word_count={words}\napprox_pages_double_spaced_250w={words/250:.1f}\npath={MD}\n",
        encoding="utf-8",
    )
    return words


def md_to_docx() -> None:
    text = MD.read_text(encoding="utf-8")
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(1.27)

    for style_name in ("Heading 1", "Heading 2", "Heading 3"):
        try:
            hs = doc.styles[style_name]
            hs.font.name = "Times New Roman"
            hs.font.color.rgb = None
            hs.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
            hs.paragraph_format.first_line_indent = Cm(0)
        except Exception:
            pass

    in_code = False
    code_buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("```"):
            if in_code:
                p = doc.add_paragraph()
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.line_spacing = 1.0
                run = p.add_run("\n".join(code_buf))
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        if not line.strip():
            continue
        if line.startswith("|") and "---" in line.replace(" ", ""):
            continue  # skip markdown separator rows; simple table handling below

        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("|"):
            # accumulate simple one-line table rows as paragraphs for robustness
            p = doc.add_paragraph(line.strip())
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.15
            for r in p.runs:
                r.font.size = Pt(10)
                r.font.name = "Times New Roman"
        elif line.startswith("- ") or line.startswith("* "):
            p = doc.add_paragraph(line[2:].strip(), style="List Bullet")
            p.paragraph_format.first_line_indent = Cm(0)
        elif re.match(r"^\d+\.\s", line):
            p = doc.add_paragraph(re.sub(r"^\d+\.\s+", "", line), style="List Number")
            p.paragraph_format.first_line_indent = Cm(0)
        elif line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            p = doc.add_paragraph()
            run = p.add_run(line.strip("*"))
            run.bold = True
            p.paragraph_format.first_line_indent = Cm(0)
        else:
            # strip light markdown bold/italic markers for readability
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            clean = re.sub(r"\*(.+?)\*", r"\1", clean)
            clean = re.sub(r"`([^`]+)`", r"\1", clean)
            p = doc.add_paragraph(clean)
            if line.startswith("**Título:**") or line.startswith("**Tipo"):
                p.paragraph_format.first_line_indent = Cm(0)

    doc.save(str(DOCX))


def write_audit() -> None:
    AUDIT.write_text(
        """# Informe de auditoría técnica y académica — lab_ag_ia_g_edu

**Fecha:** octubre 2026  
**Alcance:** `D:\\PROYECTOS\\lab_ag_ia_g_edu`  
**Documento auditado (origen):** `promptmasterskillblut.md` (sistema de reglas de redacción; no era un TFM de software)  
**Evidencia principal:** código fuente de `laboratorioIA` y `laboratorioIB`

## 1. Hallazgo sobre el documento original

`promptmasterskillblut.md` **no** contenía la investigación del laboratorio. Era un *prompt master* de redacción académica (semáforos gramaticales, muletillas, APA/Zotero, humanizer). Por ello:

- Se conservó copia íntegra: `promptmasterskillblut_BACKUP_ORIGINAL.md`
- Se generó el documento de investigación a partir del **código real**
- Se actualizó el maestro con una sección de **alcance verificado del software** para mantener coherencia Spec-as-Skill ↔ implementación

## 2. Componentes examinados

| Área | Evidencia |
| --- | --- |
| Stack | `App/backend/requirements.txt`, `run.py`, `app/__init__.py` |
| IAM/RBAC | `models/iam.py`, `auth/routes.py`, `permissions/decorators.py`, seeds |
| Dominio académico | `models/academic.py`, `services/grades.py`, `attendance.py`, `visibility.py` |
| Tool Gateway | `ai/gateway/{orchestrator,registry,executor,handlers}.py` |
| IA | `ai/provider.py`, `ai/deepseek.py`, `services/ai_agent_log.py` |
| Diferencia A/B | IA: `ai/insecure_mode.py`; IB: `services/ai_intent_guard.py` |
| Pruebas | `test_smoke.py`, `test_visibility.py`, `test_mysql.py`, `scripts/validate_*.py` |
| Docs | README.md, CHANGELOG.md |

**Excluidos del análisis indiscriminado:** `.venv`, `__pycache__`, `.git`, secretos de `.env`.

## 3. Arquitectura identificada

Dos aplicaciones Flask casi gemelas con Tool Gateway, RBAC JWT, DeepSeek, LogIA, reportes PDF/XLSX y UI Jinja/Bootstrap. Escenario experimental A (IA, modo inseguro opcional) vs B (IB, intent guard NL).

## 4. Funcionalidades verificadas (resumen)

- **Implementado:** gestión académica, RBAC, JWT, impersonación, Tool Gateway, tools en HANDLERS, auditoría, LogIA, reportes/kárdex, seeds, cabeceras/rate limit, cifrado AES de API key.
- **Parcial:** `privileges_request_elevation` (función sin registro en HANDLERS); migraciones Alembic vacías.
- **No implementado / no en disco:** PDP/PAP formales; carpetas `/Spec` y `/Skill` pese a README; suite pytest/CI.
- **No evidenciado:** despliegue productivo, encuestas, porcentajes de efectividad, pentest formal.

## 5. Inconsistencias documento↔código (corregidas en la investigación)

| Afirmación riesgosa | Tratamiento |
| --- | --- |
| “Spec as Skill con /Spec y /Skill” | Documentar como narrativa README; declarar ausencia en disco |
| “Arquitectura Zero Trust completa / PDP-PAP” | Reformular a controles *orientados* a Zero Trust vía Tool Gateway + RBAC |
| “Sistema validado en producción” | No afirmar |
| Elevación de privilegios completa | Marcar parcial |
| Resultados con % inventados | No incluir |

## 6. Correcciones realizadas

1. Creación de `proyecto_investigacion_lab_ag_ia_g_edu.md/.docx` fiel al código.
2. Matriz de trazabilidad y registro de referencias con DOI verificados.
3. Actualización del maestro `promptmasterskillblut.md` con alcance real.
4. Corrección de metadatos bibliográficos alineados a DOI conocidos.

## 7. Limitaciones detectadas

- Evaluación limitada a scripts locales (sin informe de corrida consolidado en el repo).
- Duplicación de código entre IA e IB (mantenibilidad).
- Specs no versionadas como archivos.
- Sin PDP/PAP; sin federación de identidad; sin microsegmentación de red.

## 8. Afirmaciones que requieren validación adicional

- Resultados cuantitativos de `validate_ai_chat.py` en un entorno tipificado (necesitan acta de ejecución).
- Disponibilidad/costo real de DeepSeek en el horizonte del curso.
- Transferencia pedagógica medida (no estudiada).

## 9. Conclusión de auditoría

El software **sí** constituye un laboratorio reproducible de gestión educativa con agente mediado por Tool Gateway y contraste A/B de guards. La investigación documental debe describir exactamente eso —ni más ni menos—.
""",
        encoding="utf-8",
    )


def write_matrix() -> None:
    MATRIX.write_text(
        """# Matriz de trazabilidad — lab_ag_ia_g_edu

Leyenda de estado: **I** implementado · **P** parcial · **N** no implementado · **NV** no verificable con evidencia actual

| ID | Elemento (objetivo/requisito/funcionalidad) | Evidencia técnica | Estado | Apartado documental |
| --- | --- | --- | --- | --- |
| OG | Diseñar/implementar laboratorio gestión educativa + agente + controles ZT-oriented | `laboratorioIA/App`, `laboratorioIB/App` | I | Cap. I, IV, VI |
| OE1 | Identificar arquitectura e IAM | `app/__init__.py`, `models/iam.py`, seeds | I | Cap. IV |
| OE2 | Documentar Tool Gateway y tools | `ai/gateway/*`, `HANDLERS` | I | Cap. IV, Anexo C |
| OE3 | Contrastar escenarios IA vs IB | `insecure_mode.py` vs `ai_intent_guard.py` | I | Cap. IV, V, Anexo E |
| OE4 | Evaluar con evidencias disponibles | `test_*.py`, `scripts/validate_*.py` | I/NV | Cap. V (scripts I; métricas agregadas NV) |
| RF-ACAD | CRUD académico / notas / asistencia | `api/academic.py`, services | I | Cap. IV |
| RF-RBAC | Roles y permisos granulares | `seed_data.py`, decorators | I | Cap. IV |
| RF-AI | Chat agente DeepSeek + tools | `orchestrator.py`, `provider.py` | I | Cap. IV |
| RF-AUDIT | Auditoría + LogIA | `services/audit.py`, `ai_agent_log.py` | I | Cap. IV |
| RF-REP | Reportes PDF/XLSX y kárdex | `services/reports.py`, ai_reports | I | Cap. IV |
| RF-ELEV | Elevación privilegios vía tool | `privileges_request_elevation` no en HANDLERS | P | Cap. IV, VI |
| RNF-SEC | Headers, rate limit, JWT, AES key | `create_app`, crypto, limiter | I | Cap. IV |
| RNF-ZT | Zero Trust empresarial / PDP-PAP | No hay módulos PDP/PAP | N | Cap. I, II, IV, VI |
| DOC-SPEC | Carpetas /Spec /Skill | Ausentes en disco | N | Cap. III, auditoría |
| MIG | Migraciones Alembic | Carpeta vacía; `create_all` + SQL dump | P | Cap. IV |
| TEST | Suite formal CI/pytest | Solo scripts smoke/validate | P | Cap. V |
| PROD | Despliegue productivo | Sin evidencia | N | Cap. I, V, VI |
| DATA | Datos sintéticos de laboratorio | seeds / seed_coherent | I | Cap. III, IV |

## Trazabilidad objetivo → evidencia → conclusión

| Objetivo | Evidencia suficiente para concluir | Conclusión prudente |
| --- | --- | --- |
| OE1 | Modelos + API + UI | Arquitectura Flask dual documentada |
| OE2 | Gateway + HANDLERS + logs | Mediación por tool verificable; no PDP formal |
| OE3 | Archivos diferenciales A/B | Contraste de guards reproducible en código |
| OE4 | Existencia de scripts | Estrategia de prueba local existe; no hay % generalizables |
""",
        encoding="utf-8",
    )


def write_refs_registry() -> None:
    REFS.write_text(
        """# Registro de fuentes académicas verificadas

Todas las fuentes listadas poseen DOI o ISBN verificables y se utilizaron en el documento de investigación. Fecha de consolidación: octubre 2026.

| Cita corta | DOI / ISBN | Apartados principales |
| --- | --- | --- |
| Rose et al., 2020 | 10.6028/NIST.SP.800-207 | I, II, IV, V, VI |
| Syed et al., 2022 | 10.1109/ACCESS.2022.3174679 | I, II, IV, V |
| Buck et al., 2021 | 10.1016/j.cose.2021.102436 | I, II, V |
| Adahman et al., 2022 | 10.1016/j.cose.2022.102911 | I, II, V |
| Kang et al., 2023 | 10.3390/e25121595 | I, II, IV |
| Awan et al., 2023 | 10.3390/info14020129 | II, IV |
| Azad et al., 2024 | 10.1016/j.iot.2024.101227 | I, II, IV |
| Jeong & Yang, 2025 | 10.3390/app15179551 | II, IV |
| Deng et al., 2025 | 10.1145/3716628 | I, II, V |
| Xu et al., 2025 | 10.3390/jcp5040087 | II, V |
| Mawgoud et al., 2025 | 10.1002/cpe.70185 | II, V |
| Kanaker et al., 2026 | 10.3390/computation14050098 | I, II, V |
| Gulyamov et al., 2026 | 10.3390/info17010054 | II, V |
| Geng et al., 2026 | 10.32604/cmc.2025.074081 | II, V |
| Vasović et al., 2026 | 10.3390/app16126260 | II, V |
| Shostack, 2014 | ISBN 978-1-118-80999-0 | I, II, III, VI |

## Fuentes técnicas no bibliográficas (documentación del artefacto)

| Fuente | Uso |
| --- | --- |
| README.md / CHANGELOG.md de cada App | Instalación, credenciales demo, mapa SPEC |
| Código `app/` | Evidencia primaria de funcionalidades |
| `requirements.txt` | Stack y versiones declaradas |
| Dumps SQL / seeds | Esquema y datos de laboratorio |

**Nota Zotero:** Insertar citas del manuscrito Word mediante Zotero → Add/Edit Citation (APA 7) usando estos DOI; no mantener bibliografías manuales definitivas si el flujo institucional exige campos dinámicos.
""",
        encoding="utf-8",
    )


def update_master_prompt() -> None:
    if not BACKUP.exists() and MASTER_SRC.exists():
        shutil.copy2(MASTER_SRC, BACKUP)
    original = BACKUP.read_text(encoding="utf-8") if BACKUP.exists() else MASTER_SRC.read_text(encoding="utf-8")

    addendum = """

---

# ═══════════════════════════════════════════════════════════
# ADDENDUM OBLIGATORIO — PROYECTO lab_ag_ia_g_edu (oct 2026)
# Alcance verificado por auditoría de código (Spec-as-Skill)
# ═══════════════════════════════════════════════════════════

## Principio rector del addendum

Cuando el agente redacte, corrija o amplíe documentación del proyecto `lab_ag_ia_g_edu`, **prevalece la evidencia del código** sobre cualquier afirmación del README, del CHANGELOG o de borradores previos.

**Documentar fielmente lo construido · fundamentar lo investigado · separar hechos, interpretaciones y trabajo futuro.**

## Hechos verificados (NO negociables)

1. Existen dos laboratorios Flask: `laboratorioIA` y `laboratorioIB`.
2. Stack: Flask 3, SQLAlchemy, JWT, Flask-Limiter, Jinja/Bootstrap 5, DeepSeek, MySQL/SQLite, AES para API key, reportlab/openpyxl.
3. Existe **Tool Gateway** (`orchestrator`, `registry`, `executor`, `handlers`) con chequeo de permisos, confirmación de mutaciones y logging orientado a Zero Trust / mínimo privilegio.
4. **NO** existen módulos formales llamados PDP o PAP.
5. **NO** existen carpetas `/Spec` ni `/Skill` en el repositorio (aunque el README las mencione).
6. `privileges_request_elevation` es **parcial** (función presente, no registrada en `HANDLERS`).
7. Diferencia A/B: IA tiene `AI_INSECURE_MODE` / `insecure_mode.py`; IB tiene `ai_intent_guard.py`.
8. Pruebas disponibles: scripts `test_smoke.py`, `test_visibility.py`, `test_mysql.py`, `validate_*.py`. **Prohibido inventar porcentajes de éxito.**
9. No afirmar despliegue productivo, encuestas, pentest formal ni efectividad generalizable sin evidencia.

## Verbos permitidos vs prohibidos (pirámide de evidencia)

- **Permitido con evidencia de código:** implementar, diseñar, registrar, denegar, confirmar, sembrar, exponer endpoint, persistir.
- **Permitido con evidencia de script:** ejercitar, validar localmente, comprobar en entorno de desarrollo.
- **Prohibido sin medición:** demostrar efectividad del X%, validar institucionalmente, garantizar seguridad absoluta, desplegar en producción.

## Entregables de investigación asociados

Ubicación: `D:\\PROYECTOS\\lab_ag_ia_g_edu\\documentacion_investigacion\\`

- `proyecto_investigacion_lab_ag_ia_g_edu.md` / `.docx`
- `informe_auditoria_proyecto.md`
- `matriz_trazabilidad.md`
- `registro_referencias.md`
- `promptmasterskillblut_BACKUP_ORIGINAL.md`

## Instrucción al agente

Antes de afirmar cualquier funcionalidad del laboratorio, localizar archivo/clase/ruta. Si no hay evidencia, clasificar como pendiente o trabajo futuro. Conservar las reglas de redacción APA/Zotero/humanizer de este maestro, subordinadas siempre a la veracidad técnica del addendum.

---
"""

    # Prepend addendum after first title block for visibility, also keep full original
    updated = original.rstrip() + "\n" + addendum
    # Insert a short pointer at the top
    pointer = (
        "> **ADDENDUM ACTIVO (lab_ag_ia_g_edu):** Ver sección final "
        "`ADDENDUM OBLIGATORIO — PROYECTO lab_ag_ia_g_edu` para alcance de software verificado. "
        "La evidencia de código prevalece sobre afirmaciones no comprobadas.\n\n"
    )
    if "ADDENDUM ACTIVO (lab_ag_ia_g_edu)" not in updated:
        # after first horizontal rule or at line 7
        if updated.startswith("#"):
            first_nl = updated.find("\n")
            updated = updated[: first_nl + 1] + "\n" + pointer + updated[first_nl + 1 :]
        else:
            updated = pointer + updated

    MASTER_OUT_PROJ.write_text(updated, encoding="utf-8")
    MASTER_OUT_AG.write_text(updated, encoding="utf-8")


def main() -> None:
    words = update_main_md()
    print(f"MD words={words}")
    write_audit()
    print("audit OK")
    write_matrix()
    print("matrix OK")
    write_refs_registry()
    print("refs OK")
    update_master_prompt()
    print("master OK")
    md_to_docx()
    print(f"DOCX={DOCX.exists()} size={DOCX.stat().st_size if DOCX.exists() else 0}")
    print("DONE", WC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
