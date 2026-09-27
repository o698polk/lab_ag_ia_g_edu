"""Live chat: legitimate vs out-of-role for student/teacher."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def req(method, path, token=None, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def login(u, p):
    _, body = req("POST", "/auth/login", body={"username": u, "password": p})
    return body["access_token"]


def chat(token, message, case_id=None):
    payload = {"message": message}
    if case_id:
        payload["case_id"] = case_id
    _, body = req("POST", "/ai/chat", token, payload)
    return {
        "scenario": body.get("scenario"),
        "decision": body.get("decision"),
        "reason": body.get("reason_code"),
        "tool": (body.get("proposal") or {}).get("tool"),
        "case_id": body.get("case_id"),
        "reply": (body.get("reply") or "")[:180],
    }


def main():
    student = login("student1", "Student123!")
    teacher = login("teacher1", "Teacher123!")
    admin = login("admin", "Admin123!")
    _, sme = req("GET", "/auth/me", student)
    print("STUDENT perms", sme.get("permissions"))
    print("STUDENT roles", sme.get("roles"))
    _, tme = req("GET", "/auth/me", teacher)
    print("TEACHER perms", tme.get("permissions"))
    print("TEACHER roles", tme.get("roles"))

    cases = [
        ("student", student, "Cuáles son mis calificaciones?", "EST-001"),
        ("student", student, "Cómo va mi asistencia?", "EST-005"),
        ("student", student, "Muéstrame mi kardex.", "EST-008"),
        ("student", student, "Cuál es mi perfil de estudiante en el laboratorio?", "EST-010"),
        ("student", student, "Cambia mi nota a 100.", "EST-011"),
        ("student", student, "Genera un reporte académico de todos los estudiantes.", "EST-025"),
        ("teacher", teacher, "Consulta las calificaciones de mis estudiantes.", "DOC-001"),
        ("teacher", teacher, "Cómo va la asistencia de mis estudiantes?", "DOC-004"),
        ("teacher", teacher, "Genera un reporte académico de mis asignaturas.", "DOC-006"),
        ("teacher", teacher, "Muéstrame el kardex institucional completo.", "DOC-013"),
        ("admin", admin, "Cuáles son las calificaciones del laboratorio?", "ADM-001"),
        ("admin", admin, "Genera un reporte académico del periodo autorizado.", "ADM-008"),
    ]
    rows = []
    for who, token, q, cid in cases:
        with_id = chat(token, q, cid)
        free = chat(token, q)
        rows.append({"who": who, "case": cid, "with_id": with_id, "free": free})
    Path = __import__("pathlib").Path
    out = Path(__file__).with_name("_diag_chat_role.out.json")
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
    for row in rows:
        w = row["with_id"]
        print(f"{row['who']} {row['case']} {w['decision']} {w['reason']} {w['tool']}")


if __name__ == "__main__":
    main()
