"""F12 local latency sample. Skill K-011. Does not print secrets."""

from __future__ import annotations

import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000/api/v1"


def call(method: str, path: str, body: dict | None = None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            code = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        code = exc.code
    ms = (time.perf_counter() - t0) * 1000
    return code, ms, raw


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[index]


def login(username: str, password: str):
    code, ms, raw = call("POST", "/auth/login", {"username": username, "password": password})
    token = None
    if code == 200:
        token = json.loads(raw).get("access_token")
    return code, ms, token


login_ok = []
for _ in range(8):
    code, ms, token = login("admin", "Admin123!")
    login_ok.append({"code": code, "ms": round(ms, 2)})

admin_token = None
for item in reversed(login_ok):
    if item["code"] == 200:
        _, _, admin_token = login("admin", "Admin123!")
        break

grade_samples = []
if admin_token:
    for path in ("/students/1/grades", "/courses/1/grades"):
        code, ms, raw = call("GET", path, token=admin_token)
        grade_samples.append({"path": path, "probe_code": code, "probe_ms": round(ms, 1)})
    chosen = "/students/1/grades"
    series = []
    for _ in range(30):
        code, ms, _ = call("GET", chosen, token=admin_token)
        series.append({"code": code, "ms": ms})
else:
    chosen = None
    series = []

ok_login_ms = [x["ms"] for x in login_ok if x["code"] == 200]
ok_grade_ms = [x["ms"] for x in series if x["code"] < 500]

report = {
    "login_samples": login_ok,
    "login_ok_n": len(ok_login_ms),
    "login_p50_ms": round(statistics.median(ok_login_ms), 2) if ok_login_ms else None,
    "login_p95_ms": round(p95(ok_login_ms), 2) if ok_login_ms else None,
    "grades_probes": grade_samples,
    "grades_path": chosen,
    "grades_n": len(ok_grade_ms),
    "grades_codes": {},
    "grades_p50_ms": round(statistics.median(ok_grade_ms), 2) if ok_grade_ms else None,
    "grades_p95_ms": round(p95(ok_grade_ms), 2) if ok_grade_ms else None,
    "note": "Login sample stays under 10/60s rate limit. p95 uses HTTP < 500.",
}
codes: dict[str, int] = {}
for item in series:
    key = str(item["code"])
    codes[key] = codes.get(key, 0) + 1
report["grades_codes"] = codes

out = Path(__file__).with_name("perf.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in report if k != "login_samples"}, indent=2))
