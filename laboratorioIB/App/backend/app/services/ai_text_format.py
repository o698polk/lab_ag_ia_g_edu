"""Formato de presentación formal del asistente (SPEC-027, guía APA 7)."""

from __future__ import annotations

import re

# Markdown emphasis
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_RE_BOLD_US = re.compile(r"__(.+?)__", re.S)
_RE_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.S)
_RE_ITALIC_US = re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", re.S)
_RE_CODE_FENCE = re.compile(r"```[\w]*\n?(.*?)```", re.S)
_RE_INLINE_CODE = re.compile(r"`([^`]+)`")
_RE_HEADING = re.compile(r"^#{1,6}\s+", re.M)
_RE_BULLET = re.compile(r"^[\t ]*([-*•–—▪▸►✓✔●○]|[\u2022\u2023\u25E6])\s+", re.M)
_RE_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002600-\U000026FF"
    "\U0001FA00-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)
_RE_ORNAMENT = re.compile(r"[★☆✦✧✓✔✕✖►▸←→⇒⇔≈≠∞]+")
_RE_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_RE_MULTI_NL = re.compile(r"\n{3,}")


def _strip_md_emphasis(text: str) -> str:
    t = text or ""
    t = _RE_CODE_FENCE.sub(lambda m: m.group(1).strip(), t)
    t = _RE_INLINE_CODE.sub(r"\1", t)
    t = _RE_BOLD.sub(r"\1", t)
    t = _RE_BOLD_US.sub(r"\1", t)
    # Pasadas para negrita/cursiva residuales
    for _ in range(3):
        t = _RE_ITALIC.sub(r"\1", t)
        t = _RE_ITALIC_US.sub(r"\1", t)
        t = _RE_BOLD.sub(r"\1", t)
    t = _RE_HEADING.sub("", t)
    # Asteriscos sueltos de adorno
    t = re.sub(r"(?<!\w)\*{1,3}(?!\w)", "", t)
    return t


def _bullets_to_numbered(text: str) -> str:
    lines = (text or "").split("\n")
    out = []
    n = 0
    for line in lines:
        m = _RE_BULLET.match(line)
        if m:
            n += 1
            rest = _RE_BULLET.sub("", line, count=1).strip()
            out.append(f"{n}. {rest}" if rest else f"{n}.")
        else:
            # Reiniciar numeración tras párrafo no-lista
            if line.strip() == "":
                n = 0
            out.append(line)
    return "\n".join(out)


def format_apa_plain(text: str | None) -> str:
    """
    Convierte texto del asistente a presentación simple y formal (guía APA 7).
    Conserva URLs y saltos de párrafo; elimina markdown ornamental y símbolos raros.
    """
    if not text:
        return ""
    t = str(text).replace("\r\n", "\n").replace("\r", "\n")
    t = _strip_md_emphasis(t)
    t = _bullets_to_numbered(t)
    t = _RE_EMOJI.sub("", t)
    t = _RE_ORNAMENT.sub("", t)
    # Guiones decorativos tipo "---" o "***"
    t = re.sub(r"(?m)^[\t ]*([-*_]){3,}[\t ]*$", "", t)
    t = _RE_MULTI_SPACE.sub(" ", t)
    t = _RE_MULTI_NL.sub("\n\n", t)
    # Limpiar espacios al final de línea
    t = "\n".join(line.rstrip() for line in t.split("\n"))
    return t.strip()


APA7_STYLE_INSTRUCTIONS = (
    "\n\nPresentación del texto (guía APA 7.ª edición, adaptada al chat académico):\n"
    "- Escribe en español formal, claro y conciso; oraciones completas.\n"
    "- No uses markdown: ni asteriscos (*), ni negrita (**), ni cursiva (_), ni bloques de código.\n"
    "- No uses emojis ni símbolos decorativos.\n"
    "- Para enumerar, usa listas numeradas (1. 2. 3.) o párrafos; no uses viñetas con guion o asterisco.\n"
    "- Evita títulos con #. Prefiere un párrafo introductorio y luego la información.\n"
    "- Mantén un tono profesional y respetuoso, propio de un entorno institucional.\n"
)
