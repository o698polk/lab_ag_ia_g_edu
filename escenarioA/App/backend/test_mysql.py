"""Prueba integral contra MySQL XAMPP."""
from run import app

c = app.test_client()
results = []

def check(name, ok, detail=""):
    status = "OK" if ok else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name} {detail}")

# DB URI
check("MySQL URI", "mysql" in app.config["SQLALCHEMY_DATABASE_URI"], app.config["SQLALCHEMY_DATABASE_URI"])

# Login page
r = c.get("/")
check("Login page", r.status_code == 200)

# Admin login
r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"})
data = r.get_json() or {}
check("Admin login", r.status_code == 200 and "access_token" in data, f"roles={data.get('user',{}).get('roles')}")
admin_token = data.get("access_token")
ah = {"Authorization": f"Bearer {admin_token}"}

# Dashboard
r = c.get("/api/v1/dashboard", headers=ah)
d = r.get_json() or {}
check("Dashboard", r.status_code == 200 and d.get("students") >= 1, str(d))

# Modules
for path in [
    "/users", "/students", "/teachers", "/careers", "/subjects", "/terms",
    "/courses", "/enrollments", "/schedules", "/grades", "/attendance",
    "/roles", "/notifications", "/audit", "/reports/summary",
]:
    r = c.get(f"/api/v1{path}", headers=ah)
    check(f"GET {path}", r.status_code == 200, f"status={r.status_code}")

# Teacher grades
r = c.post("/api/v1/auth/login", json={"username": "docente1", "password": "Docente123!"})
th = {"Authorization": f"Bearer {r.get_json()['access_token']}"}
r = c.post("/api/v1/grades", headers=th, json={
    "student_id": 1, "course_id": 1, "partial1": 5, "partial2": 6, "supplementary": 8
})
g = r.get_json() or {}
check("Notas + supletorio", r.status_code == 200 and g.get("final_grade") == 8.0, str(g.get("status")))

# Attendance
r = c.post("/api/v1/attendance", headers=th, json={
    "student_id": 1, "course_id": 1, "session_date": "2026-10-07", "status": "presente"
})
check("Asistencia", r.status_code == 200, str((r.get_json() or {}).get("status")))

# Impersonation
r = c.post("/api/v1/users/2/login-as", headers=ah)
imp = r.get_json() or {}
check("Impersonación", r.status_code == 200 and imp.get("user", {}).get("username") == "docente1")
ih = {"Authorization": f"Bearer {imp.get('access_token')}"}
r = c.post("/api/v1/auth/return-to-admin", headers=ih)
check("Return admin", r.status_code == 200 and (r.get_json() or {}).get("user", {}).get("username") == "admin")

# Student login
r = c.post("/api/v1/auth/login", json={"username": "estudiante1", "password": "Estudiante123!"})
check("Login estudiante", r.status_code == 200)

# Kardex
r = c.get("/api/v1/kardex/1", headers=ah)
check("Kárdex", r.status_code == 200 and "grades" in (r.get_json() or {}))

# AI fallback
r = c.post("/api/v1/ai/chat", headers=ah, json={"message": "Cuantos estudiantes hay?"})
check("IA chat", r.status_code == 200 and "reply" in (r.get_json() or {}))

# App frontend
r = c.get("/app/")
check("App UI", r.status_code == 200)

fails = [x for x in results if x[0] == "FAIL"]
print("\n=== RESUMEN ===")
print(f"Total: {len(results)} | OK: {len(results)-len(fails)} | FAIL: {len(fails)}")
if fails:
    for f in fails:
        print(" FAIL:", f[1], f[2])
    raise SystemExit(1)
print("TODAS LAS PRUEBAS PASARON CON MYSQL/XAMPP")
