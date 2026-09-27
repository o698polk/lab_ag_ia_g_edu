"""CRUD / filter tools for every SIGA module. Execution is via services, never raw SQL."""

from __future__ import annotations

from app.tools.registry import ToolMeta

A = ["ADMINISTRATOR"]
AT = ["ADMINISTRATOR", "TEACHER"]
ATS = ["ADMINISTRATOR", "TEACHER", "STUDENT"]

_FILTER = {"q": "str?", "status": "str?", "limit": "int?"}


def _t(
    name: str,
    desc: str,
    method: str,
    endpoint: str,
    schema: dict,
    perms: list[str],
    roles: list[str],
    resource: str,
    risk: str = "LOW",
) -> ToolMeta:
    return ToolMeta(
        tool_name=name,
        description=desc,
        method=method,
        endpoint=endpoint,
        parameters_schema=schema,
        required_permissions=perms,
        allowed_roles=roles,
        resource_type=resource,
        risk_level=risk,
    )


MODULE_TOOLS: dict[str, ToolMeta] = {
    t.tool_name: t
    for t in [
        _t("list_users", "Listar usuarios", "GET", "/users", {**_FILTER, "role": "str?"}, ["users.view"], A, "user"),
        _t("get_user", "Ver un usuario", "GET", "/users/{id}", {"user_id": "int"}, ["users.view"], A, "user"),
        _t(
            "create_user",
            "Registrar usuario",
            "POST",
            "/users",
            {
                "username": "str",
                "email": "str",
                "cedula": "str",
                "password": "str?",
                "first_name": "str?",
                "last_name": "str?",
                "role_codes": "list?",
            },
            ["users.create"],
            A,
            "user",
            "HIGH",
        ),
        _t(
            "update_user",
            "Actualizar usuario",
            "PATCH",
            "/users/{id}",
            {"user_id": "int", "first_name": "str?", "last_name": "str?", "email": "str?", "phone": "str?"},
            ["users.update"],
            A,
            "user",
            "HIGH",
        ),
        _t("set_user_status", "Cambiar estado de usuario", "PATCH", "/users/{id}/status", {"user_id": "int", "status": "str"}, ["users.update"], A, "user", "HIGH"),
        _t("delete_user", "Eliminar usuario", "DELETE", "/users/{id}", {"user_id": "int"}, ["users.delete"], A, "user", "HIGH"),
        _t("assign_user_roles", "Asignar roles a usuario", "PUT", "/users/{id}/roles", {"user_id": "int", "role_codes": "list"}, ["users.update"], A, "user", "HIGH"),
        _t("list_roles", "Listar roles", "GET", "/roles", _FILTER, ["roles.view"], A, "role"),
        _t("list_permissions", "Listar permisos", "GET", "/permissions", _FILTER, ["permissions.view"], A, "permission"),
        _t("create_role", "Crear rol", "POST", "/roles", {"code": "str", "name": "str", "description": "str?"}, ["roles.create"], A, "role", "HIGH"),
        _t("assign_role_permissions", "Asignar permisos a un rol", "PUT", "/roles/{code}/permissions", {"role_code": "str", "permission_codes": "list"}, ["permissions.assign"], A, "role", "HIGH"),
        _t("list_careers", "Listar carreras", "GET", "/careers", _FILTER, ["careers.view"], AT, "career"),
        _t("create_career", "Crear carrera", "POST", "/careers", {"code": "str", "name": "str", "modality": "str?", "duration_semesters": "int?"}, ["careers.create"], A, "career", "HIGH"),
        _t("set_career_status", "Cambiar estado de carrera", "PATCH", "/careers/{id}/status", {"career_id": "int", "status": "str"}, ["careers.update"], A, "career", "HIGH"),
        _t("list_subjects", "Listar asignaturas", "GET", "/subjects", _FILTER, ["subjects.view"], ATS, "subject"),
        _t("create_subject", "Crear asignatura", "POST", "/subjects", {"code": "str", "name": "str", "credits": "str?"}, ["subjects.create"], A, "subject", "HIGH"),
        _t("set_subject_status", "Cambiar estado de asignatura", "PATCH", "/subjects/{id}/status", {"subject_id": "int", "status": "str"}, ["subjects.update"], A, "subject", "HIGH"),
        _t("list_curricula", "Listar mallas", "GET", "/curricula", _FILTER, ["curriculum.view"], AT, "curriculum"),
        _t("create_curriculum", "Crear malla", "POST", "/curricula", {"career_id": "int", "version": "str"}, ["curriculum.create"], A, "curriculum", "HIGH"),
        _t("list_terms", "Listar periodos", "GET", "/terms", _FILTER, ["terms.view"], ATS, "term"),
        _t("create_term", "Crear periodo", "POST", "/terms", {"code": "str", "name": "str", "start_date": "str", "end_date": "str", "status": "str?"}, ["terms.create"], A, "term", "HIGH"),
        _t("set_term_status", "Cambiar estado de periodo", "PATCH", "/terms/{id}/status", {"term_id": "int", "status": "str"}, ["terms.update"], A, "term", "HIGH"),
        _t("list_students", "Listar estudiantes", "GET", "/students", _FILTER, ["students.view"], AT, "student"),
        _t("create_student", "Registrar perfil de estudiante", "POST", "/students", {"user_id": "int", "student_code": "str", "career_id": "int?"}, ["students.create"], A, "student", "HIGH"),
        _t("set_student_status", "Cambiar estado de estudiante", "PATCH", "/students/{id}/status", {"student_id": "int", "status": "str"}, ["students.update"], A, "student", "HIGH"),
        _t("list_teachers", "Listar docentes", "GET", "/teachers", _FILTER, ["teachers.view"], AT, "teacher"),
        _t("create_teacher", "Registrar perfil de docente", "POST", "/teachers", {"user_id": "int", "teacher_code": "str", "specialty": "str?"}, ["teachers.create"], A, "teacher", "HIGH"),
        _t("set_teacher_status", "Cambiar estado de docente", "PATCH", "/teachers/{id}/status", {"teacher_id": "int", "status": "str"}, ["teachers.update"], A, "teacher", "HIGH"),
        _t("list_courses", "Listar cursos", "GET", "/courses", {**_FILTER, "term_id": "int?"}, ["courses.view"], ATS, "course"),
        _t("create_course", "Crear curso/paralelo", "POST", "/courses", {"subject_id": "int", "term_id": "int", "parallel_code": "str?", "capacity": "int?"}, ["courses.create"], A, "course", "HIGH"),
        _t("update_course", "Actualizar curso", "PATCH", "/courses/{id}", {"course_id": "int", "capacity": "int?", "parallel_code": "str?"}, ["courses.update"], A, "course", "HIGH"),
        _t("set_course_status", "Cambiar estado de curso", "PATCH", "/courses/{id}/status", {"course_id": "int", "status": "str"}, ["courses.update"], A, "course", "HIGH"),
        _t("list_assignments", "Listar asignaciones docentes", "GET", "/teaching-assignments", {**_FILTER, "course_id": "int?"}, ["assignments.view"], AT, "assignment"),
        _t("create_assignment", "Asignar docente a curso", "POST", "/teaching-assignments", {"teacher_id": "int", "course_id": "int", "term_id": "int"}, ["assignments.create"], A, "assignment", "HIGH"),
        _t("list_enrollments", "Listar matrículas", "GET", "/enrollments", {**_FILTER, "course_id": "int?", "student_id": "int?"}, ["enrollments.view"], AT, "enrollment"),
        _t("list_classrooms", "Listar aulas", "GET", "/classrooms", _FILTER, ["schedules.view"], AT, "classroom"),
        _t("create_classroom", "Crear aula", "POST", "/classrooms", {"code": "str", "name": "str", "capacity": "int?"}, ["schedules.create"], A, "classroom", "HIGH"),
        _t("create_schedule", "Crear horario", "POST", "/schedules", {"course_id": "int", "teacher_id": "int", "classroom_id": "int", "term_id": "int", "day_of_week": "str", "start_time": "str", "end_time": "str"}, ["schedules.create"], A, "schedule", "HIGH"),
        _t("delete_schedule", "Eliminar horario", "DELETE", "/schedules/{id}", {"schedule_id": "int"}, ["schedules.delete"], A, "schedule", "HIGH"),
        _t("list_evaluations", "Listar evaluaciones", "GET", "/evaluations", {**_FILTER, "course_id": "int?"}, ["grades.view"], AT, "evaluation"),
        _t("create_evaluation", "Crear evaluación", "POST", "/evaluations", {"course_id": "int", "name": "str", "weight_percent": "str"}, ["grades.update"], AT, "evaluation", "HIGH"),
        _t("create_attendance_session", "Crear sesión de asistencia", "POST", "/attendance/sessions", {"course_id": "int", "session_date": "str", "topic": "str?"}, ["attendance.update"], AT, "attendance", "HIGH"),
        _t("list_notifications", "Listar avisos", "GET", "/notifications", {"unread_only": "bool?"}, ["notifications.view"], ATS, "notification"),
        _t("create_notification", "Crear aviso", "POST", "/notifications", {"title": "str", "body": "str", "user_id": "int?"}, ["notifications.create"], A, "notification", "HIGH"),
        _t("get_dashboard", "Resumen del dashboard", "GET", "/dashboard", {}, ["dashboard.view"], ATS, "dashboard"),
        _t("list_audit", "Listar auditoría", "GET", "/audit/events", {"limit": "int?"}, ["audit.view"], A, "audit"),
    ]
}
