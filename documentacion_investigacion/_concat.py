# -*- coding: utf-8 -*-
from pathlib import Path

base = Path(r"D:\PROYECTOS\lab_ag_ia_g_edu\documentacion_investigacion")
out = base / "proyecto_investigacion_lab_ag_ia_g_edu.md"
wc = base / "_wordcount.txt"

# front+ch1 already in out from earlier generation
files = [
    out,  # portada + cap I
    base / "_ch2.md",
    base / "_ch3.md",
    base / "_ch4a.md",
    base / "_ch4b.md",
    base / "_expand.md",
    base / "_expand2.md",
    base / "_expand3.md",
    base / "_ch5.md",
    base / "_ch6_refs_anexos.md",
]

parts = []
for i, f in enumerate(files):
    t = f.read_text(encoding="utf-8")
    if i == 0:
        parts.append(t.rstrip() + "\n")
    else:
        parts.append("\n" + t.strip() + "\n")

text = "\n".join(parts)
out.write_text(text, encoding="utf-8")

words = text.split()
n = len(words)

in_fence = False
sub = []
for ln in text.splitlines():
    if ln.strip().startswith("```"):
        in_fence = not in_fence
        continue
    if not in_fence:
        sub.extend(ln.split())
n_sub = len(sub)

wc.write_text(
    f"word_count_all_tokens={n}\n"
    f"word_count_excluding_fences={n_sub}\n"
    f"path={out}\n"
    f"exists={out.exists()}\n"
    f"bytes={out.stat().st_size}\n",
    encoding="utf-8",
)
print("words", n, "excl_fences", n_sub, "bytes", out.stat().st_size)
