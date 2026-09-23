# Ref: BL-O4-* | Skill: K-013/K-017 | Fase: F6
"""Schemas for evaluations, grades, attendance, kardex."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    course_id: int
    name: str
    weight_percent: Decimal = Field(gt=0, le=100)
    evaluation_type_code: Optional[str] = None
    due_date: Optional[date] = None


class EvaluationOut(BaseModel):
    id: int
    course_id: int
    name: str
    weight_percent: Decimal
    status: str
    due_date: Optional[date] = None

    model_config = {"from_attributes": True}


class GradeUpsert(BaseModel):
    evaluation_id: int
    student_id: int
    score: Decimal = Field(ge=0, le=100)
    comment: Optional[str] = None


class GradeOut(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    score: Decimal
    comment: Optional[str] = None
    graded_by_teacher_id: Optional[int] = None
    graded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AttendanceSessionCreate(BaseModel):
    course_id: int
    session_date: date
    topic: Optional[str] = None
    hour_slot: int = Field(default=1, ge=1)


class AttendanceSessionOut(BaseModel):
    id: int
    course_id: int
    session_date: date
    hour_slot: int = 1
    topic: Optional[str] = None

    model_config = {"from_attributes": True}


class AttendanceRosterStudent(BaseModel):
    student_id: int
    student_code: str
    name: str
    status: Optional[str] = None
    notes: Optional[str] = None
    present: bool = False


class AttendanceRosterOut(BaseModel):
    course_id: int
    session_id: Optional[int] = None
    session_date: date
    hour_slot: int
    hours_available: list[int]
    students: list[AttendanceRosterStudent]


class AttendanceBulkItem(BaseModel):
    student_id: int
    status: str = "PRESENT"
    notes: Optional[str] = None


class AttendanceBulkRequest(BaseModel):
    course_id: int
    session_date: date
    hour_slot: int = Field(default=1, ge=1)
    records: list[AttendanceBulkItem]


class GradebookRow(BaseModel):
    student_id: int
    student_code: str
    name: str
    attendance_pct: float
    score: Optional[Decimal] = None
    grade_id: Optional[int] = None


class GradebookOut(BaseModel):
    course_id: int
    evaluation_id: Optional[int] = None
    students: list[GradebookRow]


class AttendanceMark(BaseModel):
    session_id: int
    student_id: int
    status: str
    notes: Optional[str] = None


class AttendanceRecordOut(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class AttendancePercentOut(BaseModel):
    course_id: int
    student_id: int
    percentage: float


class KardexUpsert(BaseModel):
    student_id: int
    term_id: int
    subject_id: int
    course_id: Optional[int] = None
    final_grade: Optional[Decimal] = None
    academic_status: str = "IN_PROGRESS"
    credits: Decimal = Decimal("0")


class KardexOut(BaseModel):
    id: int
    student_id: int
    term_id: int
    subject_id: int
    course_id: Optional[int]
    final_grade: Optional[Decimal]
    academic_status: str
    credits: Decimal

    model_config = {"from_attributes": True}
