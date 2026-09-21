import json
from pathlib import Path

p = Path(
    r"C:\Users\POLK\.cursor\projects\d-PROYECTOS-lab-ag-ia-g-edu"
    r"\agent-transcripts\675f57df-26ad-433d-a779-86bd55feeb74"
    r"\675f57df-26ad-433d-a779-86bd55feeb74.jsonl"
)
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
keys = (
    "fase 10",
    "fase 11",
    "proximo",
    "próximo",
    "siguiente",
    "modernizaci",
    "f10 cerrada",
    "si apruebas",
    "promptmaster",
)
hits = []
for i, line in enumerate(lines):
    if "assistant" not in line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get("role") != "assistant":
        continue
    text = ""
    for c in o.get("message", {}).get("content", []) or []:
        if isinstance(c, dict) and c.get("type") == "text":
            text += c.get("text", "")
    low = text.lower()
    if any(k in low for k in keys):
        hits.append((i, text))

out = Path(r"d:\PROYECTOS\lab_ag_ia_g_edu\evidence\verify\_transcript_phase_hits.txt")
parts = [f"hits {len(hits)}\n"]
for i, t in hits[-12:]:
    parts.append(f"--- {i} ---\n")
    parts.append(t[:1500].replace("\u2192", "->"))
    parts.append("\n\n")
out.write_text("".join(parts), encoding="utf-8")
print("wrote", out, "n=", len(hits))
