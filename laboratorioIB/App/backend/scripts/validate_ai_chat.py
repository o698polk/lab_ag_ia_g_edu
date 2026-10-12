"""Validación SPEC-018 / SPEC-020: persistencia chat + historial + tools + reportes."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "database" / "seeds"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from run import app
from app.models import AIConversation, AIMessage, User, Student, Grade, Course
from app.ai.conversations import (
    get_or_create_active,
    create_conversation,
    list_user_conversations,
    open_conversation,
    message_count,
)
from app.ai.gateway.executor import execute_tool


def main():
    c = app.test_client()
    with app.app_context():
        u = User.query.filter_by(username="admin").first()
        assert u, "admin missing"

        active = get_or_create_active(u.id)
        n_before = AIMessage.query.filter_by(conversation_id=active.id).count()
        print(f"ACTIVE msgs_before={n_before} id={active.id}")

        r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"})
        token = r.get_json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        r1 = c.post(
            "/api/v1/ai/chat",
            headers=h,
            json={
                "message": "Cuenta estudiantes con system_stats",
                "channel": "float",
                "conversation_id": active.id,
            },
        )
        j1 = r1.get_json()
        assert r1.status_code == 200, j1
        assert j1.get("conversation_id") == active.id
        print(f"CHAT1 ok tools={len(j1.get('tool_calls') or [])} source={j1.get('source')}")

        r2 = c.get(f"/api/v1/ai/conversations/active?conversation_id={active.id}", headers=h)
        j2 = r2.get_json()
        assert j2["id"] == active.id
        assert j2.get("message_count", 0) > n_before
        print(f"PERSIST ok message_count={j2.get('message_count')}")

        r3 = c.post(
            "/api/v1/ai/chat",
            headers=h,
            json={
                "message": "Genera reporte de estudiantes en formato json",
                "channel": "panel",
                "conversation_id": active.id,
            },
        )
        j3 = r3.get_json()
        arts = j3.get("artifacts") or []
        print(f"REPORT artifacts={len(arts)}")
        if not arts:
            from app.ai.gateway.handlers import reports_generate

            res = reports_generate(u, {"report_type": "students", "format": "json"}, conversation_id=active.id)
            assert res.get("ok"), res
            arts = [res["artifact"]]
            print("REPORT forced via tool")

        art = arts[0]
        url = art.get("download_url") or art.get("download_path")
        assert url and url.startswith("/api/v1/ai/artifacts/"), url
        assert "sig=" in url and "expires=" in url, url
        # SPEC-022: reply fluida, sin dump [Tool …] / JSON
        reply = j3.get("reply") or ""
        assert "[Tool " not in reply, reply[:200]
        assert '"ok": true' not in reply and '"ok":true' not in reply, reply[:200]
        assert "download" in reply.lower() or (art.get("filename") or "") in reply, reply[:300]
        print(f"REPLY_CLEAN ok len={len(reply)}")
        # SPEC-021: descarga directa SIN JWT
        rd = c.get(url)
        assert rd.status_code == 200, (rd.status_code, rd.get_json())
        print(f"DOWNLOAD_SIGNED ok bytes={len(rd.data)} url={url[:90]}…")
        rd2 = c.get(f"/api/v1/ai/artifacts/{art['id']}/download", headers=h)
        assert rd2.status_code == 200
        print(f"DOWNLOAD_JWT ok bytes={len(rd2.data)}")
        bad = c.get(f"/api/v1/ai/artifacts/{art['id']}/download?expires=9999999999&sig=deadbeef")
        assert bad.status_code in (401, 403)
        print("DOWNLOAD_BAD_SIG rejected ok")

        st = Student.query.first()
        course = Course.query.first()
        pend = execute_tool(
            u,
            "grades_upsert",
            {"student_id": st.id, "course_id": course.id, "partial1": 8.5},
            confirm=False,
        )
        assert pend.get("needs_confirm"), pend
        done = execute_tool(
            u,
            "grades_upsert",
            {"student_id": st.id, "course_id": course.id, "partial1": 8.5},
            confirm=True,
        )
        assert done.get("ok"), done
        g = Grade.query.filter_by(student_id=st.id, course_id=course.id).first()
        assert g and float(g.partial1) == 8.5
        print(f"MUTATION ok partial1={g.partial1}")

        old_id = active.id
        old_msgs = message_count(old_id)
        neu = create_conversation(u.id)
        old = AIConversation.query.get(old_id)
        assert neu.id != old_id
        assert old.is_archived is True
        assert message_count(old_id) == old_msgs, "no se deben borrar mensajes al crear nueva"
        print(f"NEW_CONV archives previous ok new={neu.id} old_msgs={old_msgs}")

        hist = list_user_conversations(u.id)
        ids = {c["id"] for c in hist}
        assert old_id in ids and neu.id in ids, "historial debe incluir anterior y nueva"
        print(f"HISTORY list ok n={len(hist)}")

        rl = c.get("/api/v1/ai/conversations", headers=h)
        assert rl.status_code == 200
        api_ids = {x["id"] for x in rl.get_json()}
        assert old_id in api_ids
        print("API list includes archived ok")

        restored = open_conversation(old_id, u.id)
        assert restored and restored.id == old_id and restored.is_archived is False
        assert message_count(old_id) == old_msgs
        neu2 = AIConversation.query.get(neu.id)
        assert neu2.is_archived is True
        print("OPEN restores previous conversation ok")

        ro = c.post(f"/api/v1/ai/conversations/{old_id}/open", headers=h)
        assert ro.status_code == 200
        jo = ro.get_json()
        assert jo["id"] == old_id
        assert jo.get("message_count", 0) >= old_msgs
        print(f"API open ok messages={jo.get('message_count')}")

        # Nueva sobre vacía: reutilizar, no duplicar
        empty = create_conversation(u.id)
        again = create_conversation(u.id)
        assert empty.id == again.id
        print("REUSE empty conversation ok")

        print("ALL_CHECKS_PASSED")


if __name__ == "__main__":
    main()
