from run import app

c = app.test_client()

# Admin sees 4 terms
a = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"}).get_json()
ah = {"Authorization": f"Bearer {a['access_token']}"}
terms_admin = c.get("/api/v1/terms", headers=ah).get_json()
print("admin_terms", len(terms_admin), [t["code"] for t in terms_admin])
dash = c.get("/api/v1/dashboard", headers=ah).get_json()
print("dashboard", dash)

# Student sees only active
s = c.post("/api/v1/auth/login", json={"username": "est0001", "password": "Estudiante123!"}).get_json()
sh = {"Authorization": f"Bearer {s['access_token']}"}
terms_st = c.get("/api/v1/terms", headers=sh).get_json()
print("student_terms", len(terms_st), [t["code"] for t in terms_st])
grades_st = c.get("/api/v1/grades", headers=sh).get_json()
print("student_grades", len(grades_st))
courses_st = c.get("/api/v1/courses", headers=sh).get_json()
print("student_courses", len(courses_st))

# Teacher
t = c.post("/api/v1/auth/login", json={"username": "docente01", "password": "Docente123!"}).get_json()
th = {"Authorization": f"Bearer {t['access_token']}"}
terms_t = c.get("/api/v1/terms", headers=th).get_json()
print("teacher_terms", len(terms_t), [x["code"] for x in terms_t])
courses_t = c.get("/api/v1/courses", headers=th).get_json()
print("teacher_courses", len(courses_t))

assert len(terms_admin) == 4
assert len(terms_st) == 2
assert set(t["code"] for t in terms_st) == {"2025-1", "2025-2"}
assert len(grades_st) > 0
print("VISIBILITY_OK")
