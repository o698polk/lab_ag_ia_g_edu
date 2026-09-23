# Ref: BL-O4-* | Skill: K-013/K-016/K-017 | Fase: F6
"""Evaluation API with ABAC and anti-IDOR for student grades."""

from datetime import date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, get_current_user, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.evaluation import (
    AttendanceBulkRequest,
    AttendanceMark,
    AttendancePercentOut,
    AttendanceRecordOut,
    AttendanceRosterOut,
    AttendanceSessionCreate,
    AttendanceSessionOut,
    EvaluationCreate,
    EvaluationOut,
    FinalGradesOut,
    FinalGradesSave,
    GradebookOut,
    GradeOut,
    GradeUpsert,
    KardexOut,
    KardexUpsert,
    StudentCourseOut,
)
from app.services.catalog_service import TermClosedError
from app.services.evaluation_service import EvaluationService
from app.services.role_service import AuthorizationError

router = APIRouter(tags=["evaluation"])


def _map_err(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, TermClosedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"decision": "DENY", "reason_code": "TERM_CLOSED"},
        )
    if isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": exc.reason_code},
        )
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=500, detail="INTERNAL")


def _kardex_out(svc: EvaluationService, entry) -> KardexOut:
    labels = svc.kardex_labels(entry)
    return KardexOut(
        id=entry.id,
        student_id=entry.student_id,
        term_id=entry.term_id,
        subject_id=entry.subject_id,
        course_id=entry.course_id,
        final_grade=entry.final_grade,
        academic_status=entry.academic_status,
        credits=entry.credits,
        subject_name=labels.get("subject_name") or "",
        term_name=labels.get("term_name") or "",
    )


@router.post("/evaluations", response_model=EvaluationOut, status_code=201)
def create_evaluation(
    body: EvaluationCreate,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.create_evaluation(
            teacher=teacher, as_admin=as_admin, **body.model_dump()
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/courses/{course_id}/evaluations", response_model=List[EvaluationOut])
def list_evaluations(
    course_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).list_evaluations(course_id)


@router.put("/grades", response_model=GradeOut)
def upsert_grade(
    body: GradeUpsert,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.upsert_grade(
            teacher=teacher, as_admin=as_admin, **body.model_dump()
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/courses/{course_id}/grades", response_model=List[GradeOut])
def list_course_grades(
    course_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    # Teachers/admins with permission can list course grades;
    # still re-check assignment for teachers (not admin).
    svc = EvaluationService(db)
    if "ADMINISTRATOR" not in current.roles:
        try:
            teacher = svc.teacher_for_user(current.user.id)
            course = svc._course(course_id)
            svc._require_teacher_assignment(teacher, course)
        except Exception as exc:  # noqa: BLE001
            raise _map_err(exc) from exc
    return svc.list_grades_for_course(course_id)


@router.get("/me/grades", response_model=List[GradeOut])
def my_grades(
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        student = svc.student_for_user(current.user.id)
        return svc.list_grades_for_student(student.id)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/students/{student_id}/grades", response_model=List[GradeOut])
def grades_by_student(
    student_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    """Anti-IDOR: STUDENT only own grades; others need elevated role."""
    svc = EvaluationService(db)
    if "ADMINISTRATOR" in current.roles or "TEACHER" in current.roles:
        return svc.list_grades_for_student(student_id)
    try:
        me = svc.student_for_user(current.user.id)
    except LookupError as exc:
        raise _map_err(exc) from exc
    if me.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": "RESOURCE_NOT_OWNED"},
        )
    return svc.list_grades_for_student(student_id)


@router.post("/attendance/sessions", response_model=AttendanceSessionOut, status_code=201)
def create_session(
    body: AttendanceSessionCreate,
    current: Annotated[CurrentUser, Depends(require_permission(P.ATTENDANCE_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.create_attendance_session(
            teacher=teacher, as_admin=as_admin, **body.model_dump()
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.put("/attendance/records", response_model=AttendanceRecordOut)
def mark_attendance(
    body: AttendanceMark,
    current: Annotated[CurrentUser, Depends(require_permission(P.ATTENDANCE_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.mark_attendance(
            teacher=teacher, as_admin=as_admin, **body.model_dump()
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/attendance/roster", response_model=AttendanceRosterOut)
def attendance_roster(
    current: Annotated[CurrentUser, Depends(require_permission(P.ATTENDANCE_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    course_id: int = Query(...),
    session_date: date = Query(...),
    hour_slot: int = Query(default=1, ge=1),
):
    svc = EvaluationService(db)
    if "ADMINISTRATOR" not in current.roles:
        try:
            teacher = svc.teacher_for_user(current.user.id)
            course = svc._course(course_id)
            svc._require_teacher_assignment(teacher, course)
        except Exception as exc:  # noqa: BLE001
            raise _map_err(exc) from exc
    try:
        return svc.attendance_roster(
            course_id=course_id, session_date=session_date, hour_slot=hour_slot
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.put("/attendance/bulk", response_model=AttendanceRosterOut)
def attendance_bulk(
    body: AttendanceBulkRequest,
    current: Annotated[CurrentUser, Depends(require_permission(P.ATTENDANCE_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.save_attendance_bulk(
            teacher=teacher,
            as_admin=as_admin,
            course_id=body.course_id,
            session_date=body.session_date,
            hour_slot=body.hour_slot,
            records=[r.model_dump() for r in body.records],
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/courses/{course_id}/final-grades", response_model=FinalGradesOut)
def list_final_grades(
    course_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    if "ADMINISTRATOR" not in current.roles:
        try:
            teacher = svc.teacher_for_user(current.user.id)
            course = svc._course(course_id)
            svc._require_teacher_assignment(teacher, course)
        except Exception as exc:  # noqa: BLE001
            raise _map_err(exc) from exc
    return svc.list_final_grades(course_id)


@router.put("/courses/{course_id}/final-grades", response_model=FinalGradesOut)
def save_final_grades(
    course_id: int,
    body: FinalGradesSave,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        as_admin = "ADMINISTRATOR" in current.roles
        teacher = None
        if not as_admin:
            teacher = svc.teacher_for_user(current.user.id)
        else:
            teacher = svc.ops.get_teacher_by_user_id(current.user.id)
        return svc.save_final_grades(
            teacher=teacher,
            as_admin=as_admin,
            course_id=course_id,
            items=[item.model_dump() for item in body.items],
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/me/academic", response_model=List[StudentCourseOut])
def my_academic(
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        student = svc.student_for_user(current.user.id)
        return svc.student_academic(student.id)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/courses/{course_id}/gradebook", response_model=GradebookOut)
def course_gradebook(
    course_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.GRADES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    evaluation_id: Optional[int] = Query(default=None),
):
    svc = EvaluationService(db)
    if "ADMINISTRATOR" not in current.roles:
        try:
            teacher = svc.teacher_for_user(current.user.id)
            course = svc._course(course_id)
            svc._require_teacher_assignment(teacher, course)
        except Exception as exc:  # noqa: BLE001
            raise _map_err(exc) from exc
    return svc.gradebook(course_id, evaluation_id)


@router.get(
    "/attendance/courses/{course_id}/students/{student_id}/percent",
    response_model=AttendancePercentOut,
)
def attendance_percent(
    course_id: int,
    student_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.ATTENDANCE_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    if "ADMINISTRATOR" not in current.roles:
        if "TEACHER" in current.roles:
            try:
                teacher = svc.teacher_for_user(current.user.id)
                course = svc._course(course_id)
                svc._require_teacher_assignment(teacher, course)
            except Exception as exc:  # noqa: BLE001
                raise _map_err(exc) from exc
        else:
            try:
                me = svc.student_for_user(current.user.id)
            except Exception as exc:  # noqa: BLE001
                raise _map_err(exc) from exc
            if me.id != student_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"decision": "DENY", "reason_code": "RESOURCE_NOT_OWNED"},
                )
    pct = svc.attendance_percentage(course_id=course_id, student_id=student_id)
    return AttendancePercentOut(
        course_id=course_id, student_id=student_id, percentage=pct
    )


@router.put("/kardex", response_model=KardexOut)
def upsert_kardex(
    body: KardexUpsert,
    _: Annotated[CurrentUser, Depends(require_permission(P.KARDEX_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = EvaluationService(db)
        return _kardex_out(svc, svc.upsert_kardex(**body.model_dump()))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/me/kardex", response_model=List[KardexOut])
def my_kardex(
    current: Annotated[CurrentUser, Depends(require_permission(P.KARDEX_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    try:
        student = svc.student_for_user(current.user.id)
        return [_kardex_out(svc, row) for row in svc.list_kardex(student.id)]
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/students/{student_id}/kardex", response_model=List[KardexOut])
def kardex_by_student(
    student_id: int,
    current: Annotated[CurrentUser, Depends(require_permission(P.KARDEX_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    svc = EvaluationService(db)
    if "ADMINISTRATOR" in current.roles:
        return [_kardex_out(svc, row) for row in svc.list_kardex(student_id)]
    try:
        me = svc.student_for_user(current.user.id)
    except LookupError as exc:
        raise _map_err(exc) from exc
    if me.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": "RESOURCE_NOT_OWNED"},
        )
    return [_kardex_out(svc, row) for row in svc.list_kardex(student_id)]
