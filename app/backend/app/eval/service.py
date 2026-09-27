"""Run the frozen battery through the real Tool Gateway."""

from __future__ import annotations

import csv
import io
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import CurrentUser
from app.eval.cases import filter_cases, get_case, quality_report
from app.gateway.pep import ToolGateway
from app.models import EvalResult, EvalRun, Grade
from app.services.ai_settings_service import AiSettingsService


def _actor_role(current: CurrentUser) -> str:
    for code in ("STUDENT", "TEACHER", "ADMINISTRATOR"):
        if code in (current.roles or []):
            return code
    return current.roles[0] if current.roles else ""


class EvalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = ToolGateway(db)

    @staticmethod
    def catalog(**filters: Any) -> dict[str, Any]:
        rows = filter_cases(**filters)
        return {
            "quality": quality_report(),
            "count": len(rows),
            "cases": rows,
        }

    def run_case(self, current: CurrentUser, case_id: str) -> dict[str, Any]:
        case = get_case(case_id)
        if case is None:
            raise LookupError("CASE_NOT_FOUND")
        role = _actor_role(current)
        if case["role"] not in (current.roles or []):
            raise PermissionError("CASE_ROLE_MISMATCH")
        guard = AiSettingsService(self.db).guard_status(current.user.id)
        scenario = "B" if guard["policies_enforced"] else "A"
        run = EvalRun(
            run_id=str(uuid.uuid4()),
            user_id=current.user.id,
            role=role,
            scenario=scenario,
            policies_enforced=bool(guard["policies_enforced"]),
            policy_version="v1",
            case_count=1,
        )
        self.db.add(run)
        self.db.flush()
        result = self._execute(current, case, run, scenario)
        run.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"run_id": run.run_id, "scenario": scenario, "result": result}

    def run_battery(self, current: CurrentUser, *, role: Optional[str] = None) -> dict[str, Any]:
        actor_role = _actor_role(current)
        target_role = (role or actor_role).upper()
        if target_role not in (current.roles or []):
            raise PermissionError("CASE_ROLE_MISMATCH")
        cases = filter_cases(role=target_role)
        guard = AiSettingsService(self.db).guard_status(current.user.id)
        scenario = "B" if guard["policies_enforced"] else "A"
        run = EvalRun(
            run_id=str(uuid.uuid4()),
            user_id=current.user.id,
            role=actor_role,
            scenario=scenario,
            policies_enforced=bool(guard["policies_enforced"]),
            policy_version="v1",
            case_count=len(cases),
        )
        self.db.add(run)
        self.db.flush()
        results = [self._execute(current, case, run, scenario) for case in cases]
        run.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        return {
            "run_id": run.run_id,
            "scenario": scenario,
            "policies_enforced": run.policies_enforced,
            "indicators": self._indicators(results, scenario),
            "results": results,
        }

    def list_runs(self, user_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = list(
            self.db.scalars(
                select(EvalRun)
                .where(EvalRun.user_id == user_id)
                .order_by(EvalRun.id.desc())
                .limit(limit)
            )
        )
        return [self._run_out(r, include_results=False) for r in rows]

    def get_run(self, user_id: int, run_id: str) -> dict[str, Any] | None:
        run = self.db.scalar(
            select(EvalRun)
            .options(selectinload(EvalRun.results))
            .where(EvalRun.run_id == run_id, EvalRun.user_id == user_id)
        )
        if run is None:
            return None
        return self._run_out(run, include_results=True)

    def export(self, user_id: int, run_id: str, fmt: str = "json") -> tuple[str, str]:
        data = self.get_run(user_id, run_id)
        if data is None:
            raise LookupError("RUN_NOT_FOUND")
        if fmt == "csv":
            buf = io.StringIO()
            fields = [
                "case_id",
                "role",
                "category",
                "question",
                "expected_tool",
                "expected_a",
                "expected_b",
                "observed_decision",
                "reason_code",
                "policy_id",
                "match_expected",
                "technical_error",
                "latency_ms",
            ]
            writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in data["results"]:
                writer.writerow(row)
            return "text/csv", buf.getvalue()
        import json

        return "application/json", json.dumps(data, default=str, ensure_ascii=False)

    def _execute(
        self,
        current: CurrentUser,
        case: dict[str, Any],
        run: EvalRun,
        scenario: str,
    ) -> dict[str, Any]:
        snapshot = self._snapshot_grade(case)
        started = time.perf_counter()
        gw = self.gateway.invoke(
            current=current,
            tool_name=case["expected_tool"],
            parameters=dict(case.get("parameters") or {}),
        )
        latency = (time.perf_counter() - started) * 1000
        self._restore_grade(case, snapshot)
        expected = case["expected_scenario_b"] if scenario == "B" else case["expected_scenario_a"]
        tech = gw.reason_code in {"UNKNOWN_TOOL", "AI_UNAVAILABLE"} or (
            isinstance(gw.result, dict) and gw.result.get("error")
        )
        observed = gw.decision
        if tech and gw.decision == "ALLOW":
            observed = "ERROR"
        match = (not tech) and observed == expected
        if gw.decision == "ALLOW":
            reply = "Solicitud ejecutada (ALLOW)."
        else:
            reply = f"Solicitud denegada ({gw.reason_code})."
        row = EvalResult(
            run_pk=run.id,
            case_id=case["case_id"],
            role=case["role"],
            category=case["category"],
            question=case["question"],
            expected_tool=case["expected_tool"],
            expected_a=case["expected_scenario_a"],
            expected_b=case["expected_scenario_b"],
            observed_decision=observed,
            reason_code=gw.reason_code,
            policy_id=gw.policy_id,
            request_id=gw.request_id,
            match_expected=match,
            technical_error=bool(tech),
            latency_ms=round(latency, 2),
            reply=reply,
        )
        self.db.add(row)
        self.db.flush()
        return self._result_out(row)

    def _snapshot_grade(self, case: dict[str, Any]) -> Optional[Decimal]:
        if case["expected_tool"] != "update_grade":
            return None
        params = case.get("parameters") or {}
        try:
            ev = int(params.get("evaluation_id") or 1)
            sid = params.get("student_id")
            if sid in (None, "CURRENT_USER"):
                return None
            grade = self.db.scalar(
                select(Grade).where(Grade.evaluation_id == ev, Grade.student_id == int(sid))
            )
            return grade.score if grade is not None else None
        except (TypeError, ValueError):
            return None

    def _restore_grade(self, case: dict[str, Any], snapshot: Optional[Decimal]) -> None:
        if case["expected_tool"] != "update_grade" or snapshot is None:
            return
        params = case.get("parameters") or {}
        try:
            ev = int(params.get("evaluation_id") or 1)
            sid = int(params["student_id"])
        except (TypeError, ValueError, KeyError):
            return
        grade = self.db.scalar(
            select(Grade).where(Grade.evaluation_id == ev, Grade.student_id == sid)
        )
        if grade is not None:
            grade.score = snapshot
            self.db.flush()

    @staticmethod
    def _indicators(results: list[dict[str, Any]], scenario: str) -> dict[str, Any]:
        total = len(results)
        tech = sum(1 for r in results if r["technical_error"])
        usable = [r for r in results if not r["technical_error"]]
        adv = [r for r in usable if r["category"] != "L"]
        legit = [r for r in usable if r["category"] == "L"]
        denied = [r for r in usable if r["observed_decision"] == "DENY"]
        allowed = [r for r in usable if r["observed_decision"] == "ALLOW"]
        adv_blocked = [r for r in adv if r["observed_decision"] == "DENY"]
        adv_ran = [r for r in adv if r["observed_decision"] == "ALLOW"]
        legit_ok = [r for r in legit if r["observed_decision"] == "ALLOW"]
        legit_denied = [r for r in legit if r["observed_decision"] == "DENY"]
        latencies = [r["latency_ms"] for r in usable]
        return {
            "scenario": scenario,
            "executed": total,
            "authorized": len(allowed),
            "denied": len(denied),
            "adversarial_executed_in_open": len(adv_ran),
            "adversarial_blocked": len(adv_blocked),
            "technical_errors": tech,
            "legitimate_allowed": len(legit_ok),
            "legitimate_denied": len(legit_denied),
            "block_rate_b": (len(adv_blocked) / len(adv)) if adv else None,
            "adversarial_exec_rate_a": (len(adv_ran) / len(adv)) if adv else None,
            "legitimate_allow_rate": (len(legit_ok) / len(legit)) if legit else None,
            "audit_coverage": 1.0 if total and all(r.get("request_id") or r["technical_error"] for r in results) else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        }

    def _run_out(self, run: EvalRun, *, include_results: bool) -> dict[str, Any]:
        results = [self._result_out(r) for r in (run.results if include_results else [])]
        out = {
            "run_id": run.run_id,
            "role": run.role,
            "scenario": run.scenario,
            "policies_enforced": run.policies_enforced,
            "policy_version": run.policy_version,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "case_count": run.case_count,
        }
        if include_results:
            out["results"] = results
            out["indicators"] = self._indicators(results, run.scenario)
        return out

    @staticmethod
    def _result_out(row: EvalResult) -> dict[str, Any]:
        return {
            "case_id": row.case_id,
            "role": row.role,
            "category": row.category,
            "question": row.question,
            "expected_tool": row.expected_tool,
            "expected_a": row.expected_a,
            "expected_b": row.expected_b,
            "observed_decision": row.observed_decision,
            "reason_code": row.reason_code,
            "policy_id": row.policy_id,
            "request_id": row.request_id,
            "match_expected": row.match_expected,
            "technical_error": row.technical_error,
            "latency_ms": row.latency_ms,
            "reply": row.reply,
        }
