from run import app

c = app.test_client()

r = c.post("/api/v1/auth/login", json={"username": "docente1", "password": "Docente123!"})
t = r.get_json()["access_token"]
h = {"Authorization": f"Bearer {t}"}

g = c.post(
    "/api/v1/grades",
    headers=h,
    json={"student_id": 1, "course_id": 1, "partial1": 5, "partial2": 6},
)
print("grade_low", g.status_code, g.get_json().get("needs_supplementary"), g.get_json().get("average"))

g2 = c.post(
    "/api/v1/grades",
    headers=h,
    json={
        "student_id": 1,
        "course_id": 1,
        "partial1": 5,
        "partial2": 6,
        "supplementary": 8,
    },
)
print("with_supp", g2.status_code, g2.get_json().get("final_grade"), g2.get_json().get("status"))

a = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"}).get_json()
ah = {"Authorization": f"Bearer {a['access_token']}"}
imp = c.post("/api/v1/users/2/login-as", headers=ah)
print("impersonate", imp.status_code, imp.get_json().get("user", {}).get("username"))
