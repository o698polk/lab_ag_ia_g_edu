"""Validación SPEC-023: parseo DSML + búsqueda users + reply limpia."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "database" / "seeds"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def main():
    from run import app

    sample = (
        "<|DSML|calls>\n"
        '<|DSML|invoke name="users_list">\n'
        '<|DSML|parameter name="search" string="true">Gabriela Lopez</|DSML|parameter>\n'
        "</|DSML|invoke>\n"
        "</|DSML|calls>"
    )

    with app.app_context():
        from app.ai.provider import (
            has_tool_markup,
            parse_dsml_tool_calls,
            parse_tool_calls,
            strip_tool_markup,
        )
        from app.ai.gateway.executor import execute_tool
        from app.ai.gateway.orchestrator import _compose_user_reply, _is_raw_tool_dump
        from app.models import User

        assert has_tool_markup(sample), "debe detectar markup"
        calls = parse_dsml_tool_calls(sample)
        print("CALLS", calls)
        assert calls and calls[0]["name"] == "users_list"
        assert "Gabriela" in str(calls[0]["args"].get("search", ""))
        assert parse_tool_calls({"content": sample, "tool_calls": None})[0]["name"] == "users_list"
        clean = strip_tool_markup(sample)
        print("CLEAN", repr(clean))
        assert "DSML" not in clean.upper()
        assert "invoke" not in clean.lower()

        u = User.query.filter_by(username="admin").first()
        assert u
        tc = parse_dsml_tool_calls(sample)[0]
        res = execute_tool(u, tc["name"], tc["args"], confirm=False)
        assert res.get("ok"), res
        print("EXEC_OK count", len(res.get("data") or []), "meta", res.get("count"))

        reply = _compose_user_reply([{"tool": "users_list", "result": res}], [])
        assert not _is_raw_tool_dump(reply)
        assert "DSML" not in reply
        print("REPLY", reply[:200].encode("ascii", "replace").decode())

    print("ALL_CHECKS_PASSED")


if __name__ == "__main__":
    main()
