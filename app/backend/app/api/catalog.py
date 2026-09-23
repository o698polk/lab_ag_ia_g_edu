# Ref: BL-O2-004 | Skill: K-013/K-017 | Fase: F6
"""Academic catalog API routes."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.permissions import constants as P
from app.schemas.academic import (
    CareerCreate,
    CareerOut,
    StatusUpdate,
    CurriculumCreate,
    CurriculumOut,
    CurriculumSubjectCreate,
    StudentCreate,
    StudentOut,
    SubjectCreate,
    SubjectOut,
    TeacherCreate,
    TeacherOut,
    TermCreate,
    TermOut,
    TermStatusUpdate,
    curriculum_to_out,
)
from app.services.catalog_service import CatalogService, TermClosedError

router = APIRouter(tags=["catalog"])


def _map_err(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, TermClosedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"decision": "DENY", "reason_code": "TERM_CLOSED"},
        )
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=500, detail="INTERNAL")


@router.get("/careers", response_model=List[CareerOut])
def list_careers(
    _: Annotated[CurrentUser, Depends(require_permission(P.CAREERS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return CatalogService(db).list_careers()


@router.post("/careers", response_model=CareerOut, status_code=201)
def create_career(
    body: CareerCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.CAREERS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).create_career(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/careers/{career_id}/status", response_model=CareerOut)
def set_career_status(
    career_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.CAREERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).set_career_status(career_id, body.status)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/subjects", response_model=List[SubjectOut])
def list_subjects(
    _: Annotated[CurrentUser, Depends(require_permission(P.SUBJECTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return CatalogService(db).list_subjects()


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    body: SubjectCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.SUBJECTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    data = body.model_dump()
    type_ = data.pop("type")
    try:
        return CatalogService(db).create_subject(**data, type_=type_)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/subjects/{subject_id}/status", response_model=SubjectOut)
def set_subject_status(
    subject_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.SUBJECTS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).set_subject_status(subject_id, body.status)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/curricula", response_model=List[CurriculumOut])
def list_curricula(
    _: Annotated[CurrentUser, Depends(require_permission(P.CURRICULUM_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return [curriculum_to_out(c) for c in CatalogService(db).list_curricula()]


@router.post("/curricula", response_model=CurriculumOut, status_code=201)
def create_curriculum(
    body: CurriculumCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.CURRICULUM_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        cur = CatalogService(db).create_curriculum(**body.model_dump())
        return curriculum_to_out(cur)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.post("/curricula/{curriculum_id}/subjects", response_model=CurriculumOut, status_code=201)
def add_curriculum_subject(
    curriculum_id: int,
    body: CurriculumSubjectCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.CURRICULUM_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        CatalogService(db).add_curriculum_subject(
            curriculum_id=curriculum_id, **body.model_dump()
        )
        cur = next(
            c for c in CatalogService(db).list_curricula() if c.id == curriculum_id
        )
        return curriculum_to_out(cur)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/curricula/{curriculum_id}/status", response_model=CurriculumOut)
def set_curriculum_status(
    curriculum_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.CURRICULUM_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        cur = CatalogService(db).set_curriculum_status(curriculum_id, body.status)
        return curriculum_to_out(cur)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/terms", response_model=List[TermOut])
def list_terms(
    _: Annotated[CurrentUser, Depends(require_permission(P.TERMS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return CatalogService(db).list_terms()


@router.post("/terms", response_model=TermOut, status_code=201)
def create_term(
    body: TermCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.TERMS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).create_term(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/terms/{term_id}/status", response_model=TermOut)
def set_term_status(
    term_id: int,
    body: TermStatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.TERMS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).set_term_status(term_id, body.status)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/terms/{term_id}/writable")
def check_term_writable(
    term_id: int,
    _: Annotated[CurrentUser, Depends(require_permission(P.TERMS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    """Utility endpoint to validate RF-TRM-002 before academic writes."""
    try:
        term = CatalogService(db).assert_term_writable(term_id)
        return {"writable": True, "term_id": term.id, "status": term.status}
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/students", response_model=List[StudentOut])
def list_students(
    _: Annotated[CurrentUser, Depends(require_permission(P.STUDENTS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return CatalogService(db).list_students()


@router.post("/students", response_model=StudentOut, status_code=201)
def create_student(
    body: StudentCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.STUDENTS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).create_student(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/students/{student_id}/status", response_model=StudentOut)
def set_student_status(
    student_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.STUDENTS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).set_student_status(student_id, body.status)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.get("/teachers", response_model=List[TeacherOut])
def list_teachers(
    _: Annotated[CurrentUser, Depends(require_permission(P.TEACHERS_VIEW))],
    db: Annotated[Session, Depends(get_db)],
):
    return CatalogService(db).list_teachers()


@router.post("/teachers", response_model=TeacherOut, status_code=201)
def create_teacher(
    body: TeacherCreate,
    _: Annotated[CurrentUser, Depends(require_permission(P.TEACHERS_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).create_teacher(**body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc


@router.patch("/teachers/{teacher_id}/status", response_model=TeacherOut)
def set_teacher_status(
    teacher_id: int,
    body: StatusUpdate,
    _: Annotated[CurrentUser, Depends(require_permission(P.TEACHERS_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return CatalogService(db).set_teacher_status(teacher_id, body.status)
    except Exception as exc:  # noqa: BLE001
        raise _map_err(exc) from exc
