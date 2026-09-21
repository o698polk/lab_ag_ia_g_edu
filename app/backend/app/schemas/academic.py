# Ref: BL-O2-004 | Skill: K-013/K-017 | Fase: F6
"""Pydantic schemas for academic catalog."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class CareerCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=255)
    modality: str = "PRESENCIAL"
    duration_semesters: int = 10


class CareerOut(BaseModel):
    id: int
    code: str
    name: str
    modality: str
    duration_semesters: int
    status: str

    model_config = {"from_attributes": True}


class SubjectCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str
    credits: Decimal = Decimal("0")
    hours: int = 0
    description: Optional[str] = None
    type: str = "OBLIGATORIA"


class SubjectOut(BaseModel):
    id: int
    code: str
    name: str
    credits: Decimal
    hours: int
    type: str
    status: str

    model_config = {"from_attributes": True}


class CurriculumCreate(BaseModel):
    career_id: int
    version: str


class CurriculumSubjectCreate(BaseModel):
    subject_id: int
    level: int = 1
    semester: int = 1
    credits: Decimal = Decimal("0")


class CurriculumOut(BaseModel):
    id: int
    career_id: int
    version: str
    status: str
    subject_ids: List[int] = []

    model_config = {"from_attributes": True}


class TermCreate(BaseModel):
    code: str
    name: str
    start_date: date
    end_date: date
    status: str = "PLANNED"
    is_current: bool = False


class TermStatusUpdate(BaseModel):
    status: str


class TermOut(BaseModel):
    id: int
    code: str
    name: str
    start_date: date
    end_date: date
    status: str
    is_current: bool

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    user_id: int
    student_code: str
    career_id: Optional[int] = None
    level: Optional[str] = None
    admission_date: Optional[date] = None


class StudentOut(BaseModel):
    id: int
    user_id: int
    student_code: str
    career_id: Optional[int]
    level: Optional[str]
    status: str

    model_config = {"from_attributes": True}


class TeacherCreate(BaseModel):
    user_id: int
    teacher_code: str
    specialty: Optional[str] = None


class TeacherOut(BaseModel):
    id: int
    user_id: int
    teacher_code: str
    specialty: Optional[str]
    status: str

    model_config = {"from_attributes": True}


def curriculum_to_out(cur) -> CurriculumOut:  # noqa: ANN001
    return CurriculumOut(
        id=cur.id,
        career_id=cur.career_id,
        version=cur.version,
        status=cur.status,
        subject_ids=[i.subject_id for i in (cur.items or [])],
    )
