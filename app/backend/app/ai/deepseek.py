# Ref: RF-AI-CFG | Skill: K-018 | Fase: post-F12
"""DeepSeek HTTP client. Never logs the API key."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from app.tools.registry import TOOLS

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
ALLOWED_TOOLS = frozenset(TOOLS.keys())

_SYSTEM = (
    "Eres el asistente académico de SIGA. Respondes en español, breve y claro. "
    "Si la consulta requiere un dato o un cambio del sistema SIGA, propone UNA herramienta en JSON "
    'con la forma {"tool":"<nombre>","parameters":{...},"reply":"<texto>"}. '
    "Si es una pregunta general (programación, teoría, tutoriales, cultura) no uses herramienta: "
    'responde con {"tool":null,"parameters":{},"reply":"<respuesta útil>"}. '
    "Herramientas: "
    + ", ".join(sorted(ALLOWED_TOOLS))
    + ". Usa student_id=CURRENT_USER para el usuario que pregunta. "
    "Nunca reveles claves, tokens, secretos ni configuración interna."
)


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _root(base_url: str) -> str:
    root = (base_url or DEFAULT_BASE_URL).rstrip("/")
    if root.endswith("/v1"):
        return root
    return f"{root}/v1"


def validate_key(*, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 12.0) -> None:
    url = f"{_root(base_url)}/models"
    try:
        res = httpx.get(url, headers=_headers(api_key), timeout=timeout)
    except httpx.HTTPError as exc:
        raise ValueError("DEEPSEEK_UNREACHABLE") from exc
    if res.status_code in (401, 403):
        raise ValueError("DEEPSEEK_KEY_INVALID")
    if res.status_code >= 400:
        raise ValueError("DEEPSEEK_VALIDATE_FAILED")


def propose_from_message(
    *,
    api_key: str,
    message: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 20.0,
) -> dict[str, Any]:
    payload = {
        "model": model or DEFAULT_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": message},
        ],
    }
    try:
        res = httpx.post(
            f"{_root(base_url)}/chat/completions",
            headers=_headers(api_key),
            json=payload,
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise ValueError("DEEPSEEK_UNREACHABLE") from exc
    if res.status_code in (401, 403):
        raise ValueError("DEEPSEEK_KEY_INVALID")
    if res.status_code >= 400:
        raise ValueError("DEEPSEEK_CHAT_FAILED")
    try:
        data = res.json()
        content = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError, ValueError):
        content = ""
    return _parse_proposal(content)


def _parse_proposal(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            parsed = {}
        tool = parsed.get("tool")
        if tool in ALLOWED_TOOLS:
            params = parsed.get("parameters") if isinstance(parsed.get("parameters"), dict) else {}
            return {
                "tool": tool,
                "parameters": params,
                "reply": str(parsed.get("reply") or "").strip() or None,
            }
        reply = str(parsed.get("reply") or text).strip()
        return {"tool": None, "parameters": {}, "reply": reply or text}
    return {"tool": None, "parameters": {}, "reply": text or None}
