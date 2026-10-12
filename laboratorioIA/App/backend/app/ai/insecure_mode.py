"""SPEC-031 — Modo laboratorio inseguro del agente IA.

Activar solo con AI_INSECURE_MODE=1|true|yes en el entorno.
Default apagado: comportamiento seguro (SPEC-016/026/028/029/030) intacto.
"""

from __future__ import annotations

import os


def is_insecure_mode() -> bool:
    """True si el laboratorio deliberadamente desactiva controles del agente."""
    val = (os.getenv("AI_INSECURE_MODE") or "").strip().lower()
    return val in ("1", "true", "yes", "on")
