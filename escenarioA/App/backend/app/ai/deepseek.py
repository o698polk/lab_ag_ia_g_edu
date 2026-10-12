from urllib.parse import urlparse

import requests
from flask import current_app

from app.extensions import db
from app.models import AIConfig, AILog, Career, Course, Enrollment, Student, Teacher, User
from app.services.crypto import decrypt_value


ALLOWED_HOSTS = {"api.deepseek.com"}


def _validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("https",) and parsed.hostname in ALLOWED_HOSTS


def get_ai_config() -> AIConfig | None:
    return AIConfig.query.first()


def build_system_context(user: User) -> str:
    students = Student.query.count()
    teachers = Teacher.query.count()
    courses = Course.query.count()
    enrollments = Enrollment.query.filter_by(status="activa").count()
    careers = Career.query.count()
    from app.services.ai_text_format import APA7_STYLE_INSTRUCTIONS

    return (
        f"Eres el asistente IA del Sistema de Gestión Académica Institucional. "
        f"Actúas con los permisos del usuario {user.username} (roles: {', '.join(user.get_role_codes())}). "
        f"Estado actual: {students} estudiantes, {teachers} docentes, {careers} carreras, "
        f"{courses} cursos, {enrollments} matrículas activas. "
        f"Responde en español de forma clara, formal y útil. No inventes datos que no tengas."
        f"{APA7_STYLE_INSTRUCTIONS}"
    )


def chat(user: User, message: str, context: str = "") -> dict:
    cfg = get_ai_config()
    api_key = None
    model = current_app.config["DEEPSEEK_MODEL"]
    temperature = 0.3
    system_prompt = None
    api_url = current_app.config["DEEPSEEK_API_URL"]

    if cfg and cfg.is_enabled:
        if cfg.api_key_encrypted:
            try:
                api_key = decrypt_value(cfg.api_key_encrypted) or None
            except Exception:
                api_key = None
        model = cfg.model or model
        temperature = cfg.temperature if cfg.temperature is not None else temperature
        system_prompt = cfg.system_prompt
    if not api_key:
        api_key = current_app.config.get("DEEPSEEK_API_KEY") or ""

    system = system_prompt or build_system_context(user)
    if context:
        system += f"\nContexto adicional: {context}"

    if not api_key:
        reply = (
            "El agente IA no tiene API Key configurada. "
            "Configure DeepSeek en Administración → IA. "
            f"Mientras tanto, resumen del sistema: {build_system_context(user)}"
        )
        log = AILog(user_id=user.id, message=message, response=reply, tokens_used=0)
        db.session.add(log)
        db.session.commit()
        return {"reply": reply, "source": "fallback", "log_id": log.id}

    if not _validate_url(api_url):
        return {"error": "URL de API no permitida (SSRF)", "status": 400}

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
    except requests.RequestException as exc:
        reply = f"Error al contactar DeepSeek: {exc}"
        tokens = 0

    log = AILog(user_id=user.id, message=message, response=reply, tokens_used=tokens)
    db.session.add(log)
    db.session.commit()
    return {"reply": reply, "source": "deepseek", "tokens_used": tokens, "log_id": log.id}
