# Ref: BL-O3-* | Skill: K-013/K-017 | Fase: F6
"""Operations API: courses, assignments, enrollments, schedules."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.models import Course, Teacher
from app.permissions import constants as P
from app.schemas.academic import StatusUpdate
from app.schemas.operations import (
    AbacCheckOut,
    AssignmentCreate,
    AssignmentOut,
    ClassroomCreate,
    ClassroomOut,
    CourseCreate,
    CourseOut,
    CourseRosterStudent,
    CourseUpdate,
    EnrollmentBulk,
    EnrollmentCreate,
    EnrollmentOut,
    ScheduleCreate,
    ScheduleOut,
)
from app.services.catalog_service import TermClosedError
from app.services.operations_service import (
    CapacityError,
    OperationsService,
    ScheduleConflictError,
)

router = APIRouter(tags=["operations"])


def _course_out(svc: OperationsService, course) -> CourseOut:
    theory = getattr(course, "hours_theory", 0) or 0
    practical = getattr(course, "hours_practical", 0) or 0
    autonomous = getattr(course, "hours_autonomous", 0) or 0
    attendable = theory + practical
    labels = svc.course_labels(course)
    return CourseOut(
        id=course.id,
        subject_id=course.subject_id,
        term_id=course.term_id,
        parallel_code=course.parallel_code,
        capacity=course.capacity,
        hours_theory=theory,
        hours_practical=practical,
        hours_autonomous=autonomous,
        status=course.status,
        teacher_id=labels.get("teacher_id"),
        hours_total=theory + practical + autonomous,
        hours_attendable=attendable if attendable > 0 else 1,
        course_name=labels.get("course_name") or "",
        subject_name=labels.get("subject_name") or "",
        subject_code=labels.get("subject_code") or "",
        term_name=labels.get("term_name") or "",
        term_code=labels.get("term_code") or "",
        teacher_name=labels.get("teacher_name") or "",
    )


def _assignment_out(svc: OperationsService, row) -> AssignmentOut:
    course = svc.db.get(Course, row.course_id)
    labels = svc.course_labels(course) if course else {}
    teacher = svc.db.get(Teacher, row.teacher_id)
    return AssignmentOut(
        id=row.id,
        teacher_id=row.teacher_id,
        course_id=row.course_id,
        term_id=row.term_id,
        status=row.status,
        teacher_name=svc._user_name(teacher.user_id) if teacher else "",
        course_name=labels.get("course_name") or "",
        subject_name=labels.get("subject_name") or "",
        term_name=labels.get("term_name") or "",
    )


def _enrollment_out(svc: OperationsService, row) -> EnrollmentOut:
    course = svc.db.get(Course, row.course_id)
    labels = svc.course_labels(course) if course else {}
    return EnrollmentOut(
        id=row.id,
        student_id=row.student_id,
        course_id=row.course_id,
        term_id=row.term_id,
        status=row.status,
        enrolled_at=row.enrolled_at,
        student_name=svc.student_name(row.student_id),
        course_name=labels.get("course_name") or "",
        subject_name=labels.get("subject_name") or "",
        term_name=labels.get("term_name") or "",
    )


def _map_err(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, TermClosedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"decision": "DENY", "reason_code": "TERM_CLOSED"},
        )
    if isinstance(exc, CapacityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ScheduleConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=500, detail="INTERNAL")


@router.get("/courses", response_model=List[CourseOut])
def list_courses(
    current: Annotated[CurrentUser, Depends(require_permission(P.COURSES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    term_id: Optional[int] = Query(default=None),
):
    svc = OperationsService(db)
    teacher_id = None
    student_id = None
    if "ADMINISTRATOR" not in current.roles:
        if "TEACHER" in current.roles:
            teacher = svc.get_teacher_by_user_id(current.user.id)
            teacher_id = teacher.id if teacher else -1
        elif "STUDENT" in current.roles:
            student = svc.get_student_by_user_id(current.user.id)
            student_id = student.id if student else -1
    return [
        _course_out(svc, c)
        for c in svc.list_courses(term_id=term_id, teacher_id=teacher_id, student_id=student_id)
    ]


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    body: CourseCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.COURSES_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _course_out(svc, svc.create_course(**body.model_dump()))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/courses/{course_id}/status", response_model=CourseOut)
def set_course_status(
    course_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.COURSES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _course_out(svc, svc.set_course_status(course_id, body.status))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    body: CourseUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.COURSES_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _course_out(svc, svc.update_course(course_id, **body.model_dump(exclude_unset=True)))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/courses/{course_id}/roster", response_model=List[CourseRosterStudent])
def course_roster(
    course_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.ENROLLMENTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return OperationsService(db).course_roster(course_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/teaching-assignments", response_model=List[AssignmentOut])
def list_assignments(
    _: Annotated[CurrentUser, Depends(require_permission(P.ASSIGNMENTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    course_id: Optional[int] = Query(default=None),
):
    svc = OperationsService(db)
    return [_assignment_out(svc, row) for row in svc.list_assignments(course_id=course_id)]


@router.post("/teaching-assignments", response_model=AssignmentOut, status_code=201)
def assign_teacher(
    body: AssignmentCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.ASSIGNMENTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _assignment_out(svc, svc.assign_teacher(**body.model_dump()))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/teaching-assignments/{assignment_id}/status", response_model=AssignmentOut)
def set_assignment_status(
    assignment_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.ASSIGNMENTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _assignment_out(svc, svc.set_assignment_status(assignment_id, body.status))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/abac/teaching-assignment", response_model=AbacCheckOut)
def check_assignment(
    teacher_id: int,
    course_id: int,
    term_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.ASSIGNMENTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    exists = OperationsService(db).teaching_assignment_exists(
        teacher_id=teacher_id, course_id=course_id, term_id=term_id
    )
    return AbacCheckOut(
        teaching_assignment_exists=exists,
        teacher_id=teacher_id,
        course_id=course_id,
        term_id=term_id,
    )


@router.get("/enrollments", response_model=List[EnrollmentOut])
def list_enrollments(
    _: Annotated[CurrentUser, Depends(require_permission(P.ENROLLMENTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    course_id: Optional[int] = Query(default=None),
):
    svc = OperationsService(db)
    return [_enrollment_out(svc, row) for row in svc.list_enrollments(course_id=course_id)]


@router.post("/enrollments", response_model=EnrollmentOut, status_code=201)
def enroll(
    body: EnrollmentCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.ENROLLMENTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _enrollment_out(svc, svc.enroll_student(**body.model_dump()))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.post("/enrollments/bulk", response_model=List[EnrollmentOut])
def enroll_bulk(
    body: EnrollmentBulk,
    _: Annotated[CurrentUser, Depends(require_permission(P.ENROLLMENTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return [
            _enrollment_out(svc, row)
            for row in svc.sync_enrollments(**body.model_dump())
        ]
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.post("/enrollments/{enrollment_id}/cancel", response_model=EnrollmentOut)
def cancel_enrollment(
    enrollment_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.ENROLLMENTS_CANCEL))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        svc = OperationsService(db)
        return _enrollment_out(svc, svc.cancel_enrollment(enrollment_id))
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/classrooms", response_model=List[ClassroomOut])
def list_classrooms(
    _: Annotated[CurrentUser, Depends(require_permission(P.SCHEDULES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return OperationsService(db).list_classrooms()


@router.post("/classrooms", response_model=ClassroomOut, status_code=201)
def create_classroom(
    body: ClassroomCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.SCHEDULES_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return OperationsService(db).create_classroom(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/schedules", response_model=List[ScheduleOut])
def list_schedules(
    _: Annotated[CurrentUser, Depends(require_permission(P.SCHEDULES_VIEW))],
    db: Annotated[Session, Depends(get_db)],
    term_id: Optional[int] = Query(default=None),
):
    return OperationsService(db).list_schedules(term_id=term_id)


@router.post("/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(
    body: ScheduleCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.SCHEDULES_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return OperationsService(db).create_schedule(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.SCHEDULES_DELETE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        OperationsService(db).delete_schedule(schedule_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc
    return None
