"""Llamadas al proveedor LLM (OpenAI-compatible / DeepSeek)."""

import json
import re
from urllib.parse import urlparse

import requests
from flask import current_app

from app.ai.deepseek import build_system_context, get_ai_config
from app.models import User
from app.services.crypto import decrypt_value

# Markup que algunos modelos emiten en lugar de tool_calls estructurados (SPEC-023)
_DSML_MARK_RE = re.compile(
    r"(DSML|invoke\s+name\s*=|<\|/?|</?\||tool_call|function_call|</?parameter)",
    re.I,
)
_INVOKE_RE = re.compile(
    r'(?:invoke|tool_call|function)\s+name\s*=\s*["\']?([a-zA-Z0-9_]+)["\']?',
    re.I,
)
_PARAM_RE = re.compile(
    r'(?:parameter|param)\s+name\s*=\s*["\']?([a-zA-Z0-9_]+)["\']?[^>]*>\s*([^<\n]+)',
    re.I,
)
_PARAM_ATTR_RE = re.compile(
    r'(?:parameter|param)\s+name\s*=\s*["\']?([a-zA-Z0-9_]+)["\']?[^>]*?(?:value\s*=\s*["\']([^"\']+)["\'])?',
    re.I,
)
_JSON_TOOL_RE = re.compile(
    r'\{\s*"name"\s*:\s*"([a-zA-Z0-9_]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
    re.S,
)

ALLOWED_HOSTS = {"api.deepseek.com", "api.openai.com", "127.0.0.1", "localhost"}


def _validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        return False
    host = parsed.hostname or ""
    if host in ALLOWED_HOSTS:
        return True
    return host.endswith(".deepseek.com") or host.endswith(".openai.com")


def _resolve_config():
    cfg = get_ai_config()
    api_key = current_app.config.get("DEEPSEEK_API_KEY") or ""
    model = current_app.config["DEEPSEEK_MODEL"]
    temperature = 0.3
    system_prompt = None
    api_url = current_app.config["DEEPSEEK_API_URL"]
    enabled = bool(api_key)

    if cfg and cfg.is_enabled:
        enabled = True
        if cfg.api_key_encrypted:
            api_key = decrypt_value(cfg.api_key_encrypted) or api_key
        model = cfg.model or model
        temperature = cfg.temperature if cfg.temperature is not None else temperature
        system_prompt = cfg.system_prompt

    return {
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "system_prompt": system_prompt,
        "api_url": api_url,
        "enabled": enabled and bool(api_key),
    }


def call_llm(user: User, messages: list[dict], *, use_tools: bool = True) -> dict:
    cfg = _resolve_config()
    if not cfg["enabled"]:
        return {"fallback": True, "reply": None}

    if not _validate_url(cfg["api_url"]):
        return {"error": "URL de API no permitida (SSRF)"}

    from app.services.ai_text_format import APA7_STYLE_INSTRUCTIONS

    roles = ",".join(user.get_role_codes() or []) or "sin_rol"
    system = cfg["system_prompt"] or build_system_context(user)
    system += (
        "\n\nEres un agente con acceso a herramientas del sistema académico. "
        "Usa las tools del API (tool_calls) para consultar o modificar datos reales. "
        "NUNCA escribas markup DSML, XML de tools, ni texto como "
        "'invoke name=', '<|DSML|>', '<tool_call>' o bloques de function_call en tu respuesta. "
        "Esas marcas son internas y el usuario no debe verlas. "
        "Para acciones que modifican datos, el sistema pedirá confirmación al usuario. "
        "Responde siempre en español, de forma clara y organizada. "
        "Nunca pegues JSON crudo, nombres internos de tools ni bloques [Tool …]. "
        "Cuando haya un reporte, indica el nombre del archivo y el enlace de descarga. "
        "No inventes datos."
        f"\nRol(es) del usuario actual: {roles}. "
        "Aplica mínimo privilegio: solo usa las tools disponibles. "
        "Si el usuario es docente, sus «materias» son sus cursos (courses_list / report type courses). "
        "Cuando pida un reporte o Excel de materias/cursos/estudiantes/notas de su ámbito, "
        "use reports_generate con el report_type adecuado (courses, students, grades, attendance) "
        "y format xlsx o pdf; incluya siempre el enlace de descarga del artifact. "
        "Puede listar estudiantes y cursos propios. "
        "No intente el directorio global de usuarios, roles ni auditoría si no hay tool. "
        "Si pide datos fuera de su alcance, indíquelo con claridad."
    )
    system += APA7_STYLE_INSTRUCTIONS

    payload_messages = [{"role": "system", "content": system}] + messages
    payload = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
        "messages": payload_messages,
    }
    if use_tools:
        from app.ai.gateway.registry import tools_for_user

        tools = tools_for_user(user)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}

    try:
        resp = requests.post(cfg["api_url"], json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        msg = choice["message"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "message": msg,
            "tokens_used": tokens,
            "source": "llm",
        }
    except requests.RequestException as exc:
        return {"error": str(exc), "tokens_used": 0}


def has_tool_markup(text: str | None) -> bool:
    if not text:
        return False
    return bool(_DSML_MARK_RE.search(text))


def strip_tool_markup(text: str | None) -> str:
    """Elimina marcas DSML / invoke del texto visible (SPEC-023)."""
    if not text:
        return ""
    t = text
    # Bloques DSML completos
    t = re.sub(r"<\|[^|>]*\|>", " ", t)
    t = re.sub(r"</?\|[^>]*>", " ", t)
    t = re.sub(r"(?is)<[^>]*DSML[^>]*>.*?</[^>]*DSML[^>]*>", " ", t)
    t = re.sub(r"(?is)</?[^>]*DSML[^>]*>", " ", t)
    t = re.sub(r"(?is)<tool_call>.*?</tool_call>", " ", t)
    t = re.sub(r"(?is)<function[^>]*>.*?</function>", " ", t)
    t = re.sub(r"(?is)invoke\s+name\s*=\s*[\"']?[a-zA-Z0-9_]+[\"']?[^\n]*", " ", t)
    t = re.sub(r"(?is)parameter\s+name\s*=\s*[\"']?[a-zA-Z0-9_]+[\"']?[^<\n]*", " ", t)
    t = re.sub(r"(?is)\bDSML\b", " ", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def parse_dsml_tool_calls(content: str | None) -> list[dict]:
    """Extrae tool-calls de markup DSML / invoke en texto (SPEC-023)."""
    if not content or not has_tool_markup(content):
        return []

    out: list[dict] = []

    # Formato: invoke name="X" ... parameter name="a">value
    # Partir por cada invoke
    parts = re.split(r"(?i)(?:invoke|tool_call)\s+name\s*=", content)
    for part in parts[1:]:
        name_m = re.match(r'\s*["\']?([a-zA-Z0-9_]+)["\']?', part)
        if not name_m:
            continue
        name = name_m.group(1)
        # Tomar hasta el siguiente invoke o fin
        chunk = part[:800]
        args: dict = {}
        for pm in _PARAM_RE.finditer(chunk):
            key = pm.group(1)
            val = (pm.group(2) or "").strip()
            if val.lower() in ("true", "false"):
                args[key] = val.lower() == "true"
            else:
                try:
                    if val.isdigit():
                        args[key] = int(val)
                    else:
                        args[key] = val
                except Exception:
                    args[key] = val
        # Atributo value= si no hubo cuerpo
        if not args:
            for pm in _PARAM_ATTR_RE.finditer(chunk):
                if pm.group(2):
                    args[pm.group(1)] = pm.group(2)
        out.append({"id": f"dsml_{name}_{len(out)}", "name": name, "args": args})

    # JSON embebido {"name":"...","arguments":{...}}
    if not out:
        for jm in _JSON_TOOL_RE.finditer(content):
            try:
                args = json.loads(jm.group(2))
            except json.JSONDecodeError:
                args = {}
            out.append({"id": f"json_{jm.group(1)}", "name": jm.group(1), "args": args})

    # Fallback: solo nombre de tool conocido en invoke
    if not out:
        for im in _INVOKE_RE.finditer(content):
            out.append({"id": f"dsml_{im.group(1)}", "name": im.group(1), "args": {}})

    return out


def parse_tool_calls(message: dict) -> list[dict]:
    calls = message.get("tool_calls") or []
    out = []
    for c in calls:
        fn = c.get("function") or {}
        name = fn.get("name")
        if not name:
            continue
        raw = fn.get("arguments") or "{}"
        try:
            args = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            args = {}
        out.append({"id": c.get("id"), "name": name, "args": args})

    # SPEC-023: si no hay tool_calls API, parsear markup en content
    if not out:
        out = parse_dsml_tool_calls(message.get("content") or "")
    return out
